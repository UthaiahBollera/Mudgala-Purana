"""Lossless storage and complete pre-migration equivalence, including all holds."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import json_storage as storage


class SharedJSON(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'document.json'
        self.value = {'historical': {'issues': ['Uncertain ' * 200], 'accepted': None},
                      'records': [{'id': str(i), 'text': 'ಕನ್ನಡ' * 300, 'accepted': None} for i in range(150)]}

    def pack(self, value=None):
        storage.save_json_document(self.path, self.value if value is None else value)
        return json.loads(self.path.read_text())

    def test_legacy_plain_json_still_loads(self):
        self.path.write_text(json.dumps(self.value))
        self.assertEqual(storage.load_json_document(self.path), self.value)

    def test_all_types_order_unicode_and_reserved_shapes_round_trip(self):
        value = {'z': None, 'a': [True, False, 0, 1, 1.5, '', [], {}, {'ref': 'literal'},
                                {'map': [['not', 'metadata']]}, {'concat': 'literal'}], 'ಕನ್ನಡ': 'देहि'}
        self.pack(value)
        self.assertEqual(storage.canonical_bytes(storage.load_json_document(self.path)), storage.canonical_bytes(value))

    def test_repeated_references_do_not_alias_mutable_history(self):
        shared = {'issues': self.value['historical']['issues'], 'accepted': None}
        self.pack({'old': shared, 'new': copy.deepcopy(shared)})
        loaded = storage.load_json_document(self.path)
        loaded['new']['issues'].append('later')
        self.assertEqual(loaded['old'], shared)

    def test_large_repeated_evidence_stored_once(self):
        index = self.pack()
        texts = [node['text'] for s in index['shards']
                 for node in json.loads((self.path.parent / s['file']).read_text())['objects'].values() if 'text' in node]
        self.assertEqual(texts.count('ಕನ್ನಡ' * 300), 1)

    def test_growing_boundaries_reuse_prior_chunks(self):
        before = {'old': [[1, 2, i] for i in range(1000)]}
        first = self.pack(before)
        keys = lambda index: {k for s in index['shards'] for k in json.loads((self.path.parent / s['file']).read_text())['objects']}
        old_keys = keys(first)
        after = copy.deepcopy(before)
        after['new'] = before['old'] + [[1, 2, 1000]]
        second = self.pack(after)
        self.assertGreater(len(old_keys & keys(second)), 10)
        self.assertEqual(storage.load_json_document(self.path), after)

    def test_repacking_is_deterministic(self):
        first = self.pack()
        raw = self.path.read_bytes()
        shards = {s['file']: (self.path.parent/s['file']).read_bytes() for s in first['shards']}
        self.pack(storage.load_json_document(self.path))
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertTrue(all((self.path.parent/p).read_bytes() == b for p, b in shards.items()))

    def test_edit_preserves_every_unmodified_field(self):
        self.pack()
        loaded = storage.load_json_document(self.path)
        loaded['records'][-1]['accepted'] = 'later adjudication'
        expected = copy.deepcopy(self.value)
        expected['records'][-1]['accepted'] = 'later adjudication'
        self.pack(loaded)
        self.assertEqual(storage.canonical_bytes(storage.load_json_document(self.path)), storage.canonical_bytes(expected))

    def test_shard_tamper_rejected(self):
        index = self.pack()
        p = self.path.parent/index['shards'][0]['file']
        p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(ValueError): storage.load_json_document(self.path)

    def test_object_tamper_rejected_even_with_new_shard_hash(self):
        index = self.pack()
        descriptor = index['shards'][0]
        p = self.path.parent/descriptor['file']
        doc = json.loads(p.read_text())
        key = next(iter(doc['objects']))
        doc['objects'][key] = {'text': 'altered evidence'}
        raw = storage.canonical_bytes(doc)+b'\n'
        h = hashlib.sha256(raw).hexdigest()
        dest = p.with_name(descriptor['bucket']+'-'+h+'.json')
        dest.write_bytes(raw)
        descriptor.update(file=str(dest.relative_to(self.path.parent)), sha256=h, bytes=len(raw))
        self.path.write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, 'Content object checksum'): storage.load_json_document(self.path)

    def test_logical_checksum_rejected(self):
        index = self.pack()
        index['logical_sha256'] = '0'*64
        self.path.write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, 'Logical document checksum'): storage.load_json_document(self.path)

    def test_path_escape_rejected(self):
        index = self.pack()
        index['shards'][0]['file'] = '../outside.json'
        self.path.write_text(json.dumps(index))
        with self.assertRaises(ValueError): storage.load_json_document(self.path)

    def test_missing_shard_rejected(self):
        index = self.pack()
        (self.path.parent/index['shards'][0]['file']).unlink()
        with self.assertRaises(FileNotFoundError): storage.load_json_document(self.path)

    def test_unknown_storage_version_rejected(self):
        index = self.pack()
        index['storage_format'] = 'mudgala-shared-json-v999'
        self.path.write_text(json.dumps(index))
        with self.assertRaises(ValueError): storage.load_json_document(self.path)

    def test_interrupted_save_keeps_previous_document_readable(self):
        self.pack()
        atomic = storage._atomic_write
        def interrupted(path, raw):
            if path == self.path: raise OSError('simulated interrupted index write')
            atomic(path, raw)
        with patch.object(storage, '_atomic_write', side_effect=interrupted):
            with self.assertRaises(OSError): self.pack({'new': 'new content ' * 300})
        self.assertEqual(storage.load_json_document(self.path), self.value)

    def test_size_failure_happens_before_publishing_index(self):
        self.pack()
        raw = self.path.read_bytes()
        with patch.object(storage, 'MAX_SHARD_BYTES', 1):
            with self.assertRaises(ValueError): self.pack({'new': 'new content ' * 300})
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertEqual(storage.load_json_document(self.path), self.value)


class CompleteMigrationEquivalence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((ROOT/'translation/storage-migration-equivalence.json').read_text())

    def assert_document(self, name):
        original = json.loads(subprocess.check_output(['git', 'show', self.report['baseline_source_commit']+':translation/'+name], cwd=ROOT))
        # Re-run the complete migration on its immutable source snapshot.
        # Future authorized adjudications must not be frozen to migration-day data.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/name
            storage.save_json_document(path, original)
            loaded = storage.load_json_document(path)
        self.assertEqual(storage.canonical_bytes(original), storage.canonical_bytes(loaded))
        self.assertEqual(storage.digest(loaded), self.report['documents'][name]['logical_sha256'])

    def test_every_coverage_boundary_and_field_exact(self): self.assert_document('coverage.json')
    def test_every_registry_record_flag_acceptance_and_provenance_exact(self): self.assert_document('unresolved-passages.json')
    def test_indexes_and_all_shards_below_eight_mib(self):
        for name in self.report['documents']:
            p = ROOT/'translation'/name
            index = json.loads(p.read_text())
            self.assertLessEqual(p.stat().st_size, storage.MAX_SHARD_BYTES)
            self.assertTrue(all((p.parent/s['file']).stat().st_size <= storage.MAX_SHARD_BYTES for s in index['shards']))


if __name__ == '__main__': unittest.main()
