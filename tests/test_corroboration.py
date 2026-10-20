"""Reject overstated or mismatched evidence-only source corroboration."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from json_storage import load_json_document
from validate_corroboration import validate


class Corroboration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.index = json.loads((ROOT / 'translation/Google-corroboration-index.json').read_text())
        self.entry = self.index['chapters'][0]
        self.index['chapters'] = [self.entry]
        self.review = json.loads((ROOT / self.entry['review_file']).read_text())
        paths = {x['file'] for x in self.review['evidence_files']}
        paths.update(x['prior_review_file'] for x in self.review['records'])
        paths.update(x['original_source']['file'] for x in self.review['records'])
        for name in paths:
            dest = self.root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        source = {x['id']: x for x in load_json_document(ROOT / 'translation/unresolved-passages.json')['records']}
        self.registry = {'records': [source[f"kh1-ch4-v{x['key'][2]}"] for x in self.review['records']]}
        path = self.root / 'translation/narrative.tsv'
        with path.open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=['khanda', 'chapter', 'verse', 'source_pages', 'type', 'text'], delimiter='\t')
            writer.writeheader()
            for x in self.review['records']:
                writer.writerow(dict(zip(['khanda', 'chapter', 'verse'], x['key']), source_pages=x['historical_source_pages'], type=x['current_type'], text=x['current_text']))

    def check(self):
        path = self.root / self.entry['review_file']
        path.write_text(json.dumps(self.review, ensure_ascii=False))
        self.entry['review_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        for x in self.registry['records']:
            x['latest_source_corroboration']['review_sha256'] = self.entry['review_sha256']
        (self.root / 'translation/Google-corroboration-index.json').write_text(json.dumps(self.index))
        (self.root / 'translation/unresolved-passages.json').write_text(json.dumps(self.registry, ensure_ascii=False))
        return validate(self.root)

    def reject(self):
        with self.assertRaises(AssertionError):
            self.check()

    def test_six_target_wording_only_valid(self):
        self.assertEqual(self.check(), 6)

    def test_printing_not_full_chapter_certification(self):
        self.review['whole_chapter_validation'] = True
        self.reject()

    def test_printing_not_meaning_certification(self):
        self.review['records'][2]['meaning_certified'] = True
        self.reject()

    def test_retained_syntax_hold_required(self):
        next(x for x in self.registry['records'] if x['id'] == 'kh1-ch4-v30')['current_translation_review']['issues'] = []
        self.reject()

    def test_wrong_target_page_rejected(self):
        self.review['records'][0]['reference_source']['page_id'] = 'PT999'
        self.reject()

    def test_evidence_only_cannot_accept_new_text(self):
        self.review['records'][0]['accepted_new_replacement'] = 'ಹೊಸ ಪಾಠ'
        self.reject()


if __name__ == '__main__':
    unittest.main()
