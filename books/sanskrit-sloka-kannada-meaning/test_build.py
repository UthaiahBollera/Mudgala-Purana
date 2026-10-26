"""Regression checks for reading order, blank protection and EPUB structure."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile
import build


class BookBuildTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / 'book'
        shutil.copytree(build.ROOT, self.root, ignore=shutil.ignore_patterns('dist', '__pycache__', 'site'))
        self.patch = patch.object(build, 'ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def run_build(self):
        with contextlib.redirect_stdout(io.StringIO()):
            build.build()

    def manifest(self, edit):
        p = self.root / 'book.json'
        m = json.loads(p.read_text())
        edit(m)
        p.write_text(json.dumps(m, ensure_ascii=False))

    def test_epub_spine_and_portable_preview(self):
        self.run_build()
        with zipfile.ZipFile(self.root / 'dist/mudgala-preview.epub') as z:
            self.assertEqual(z.infolist()[0].filename, 'mimetype')
            self.assertEqual(z.infolist()[0].compress_type, zipfile.ZIP_STORED)
            opf = ET.fromstring(z.read('EPUB/package.opf'))
            ns = {'o': 'http://www.idpf.org/2007/opf'}
            m = json.loads((self.root / 'book.json').read_text())
            expected_spine = ['cover'] + [c['id'] for c in m['frontmatter']] + [c['id'] for c in m['chapters'] if c.get('include', True)]
            self.assertEqual([n.get('idref') for n in opf.findall('o:spine/o:itemref', ns)], expected_spine)
            for n in opf.findall('o:manifest/o:item', ns):
                self.assertIn('EPUB/' + n.get('href'), z.namelist())
            self.assertEqual(z.read('EPUB/chapters/khanda-01/chapter-001.xhtml'), (self.root / 'dist/web/chapters/khanda-01/chapter-001.xhtml').read_bytes())
            self.assertEqual(z.read('EPUB/frontmatter/01-devotional-opening.xhtml'), (self.root / 'frontmatter/01-devotional-opening.xhtml').read_bytes())
        standalone = (self.root / 'dist/mudgala-preview.html').read_text()
        self.assertIn('ಮುದ್ಗಲ ಪುರಾಣ', standalone)
        self.assertIn('data:image/png;base64,', standalone)
        self.assertIn('data:font/ttf;base64,', standalone)
        self.assertNotIn('src="assets/', standalone)

    def test_frontmatter_coverage_and_no_reader_chrome(self):
        self.run_build()
        ns = {'h': 'http://www.w3.org/1999/xhtml'}
        m = json.loads((self.root / 'book.json').read_text())
        expected_pages = {(d['id'], str(p)) for d in m['source_documents'] for p in d['integrated_pdf_pages']}
        for name in ('dist/web/index.html', 'dist/mudgala-preview.html'):
            body = ET.parse(self.root / name).find('h:body', ns)
            self.assertEqual(body.findall('.//h:a', ns), [])
            self.assertEqual(body.findall('.//h:nav', ns), [])
            sections = body.findall('.//h:section[@data-source-pdf-page]', ns)
            actual_pages = {(n.get('data-source-file', 'user-pdf-001'), n.get('data-source-pdf-page')) for n in sections}
            for section in body.findall('.//h:section[@data-source-pdf-pages]', ns):
                if section.get('data-source-file'):
                    actual_pages.update((section.get('data-source-file'), p) for p in section.get('data-source-pdf-pages').split())
            document_ids = {d['filename']: d['id'] for d in m['source_documents']}
            for unit in body.findall('.//h:div[@data-source-refs]', ns):
                actual_pages.update((document_ids[r['file']], str(r['pdf_page'])) for r in json.loads(unit.get('data-source-refs')))
            self.assertEqual(actual_pages, expected_pages)
            front = body.findall('.//h:section[@class="frontmatter"]', ns)
            self.assertEqual([n.get('id') for n in front], [c['id'] for c in m['frontmatter']])
            rows = body.findall('.//h:tr[@id]', ns) + body.findall('.//h:tr[@data-key]', ns)
            self.assertEqual(len(rows), 372)
            self.assertEqual([len(n.findall('.//h:tr[@id]', ns)) + len(n.findall('.//h:tr[@data-key]', ns)) for n in front], [0,0,65,62,64,63,61,57,0,0,0,0,0])
            self.assertEqual(len(body.findall('.//h:div[@data-unit]', ns)), 1 + sum(c['coverage']['last_verse'] for c in m['chapters']))
            self.assertEqual(len(body.findall('.//h:div[@data-fragment="true"]', ns)), sum(not c['coverage']['last_verse_complete'] for c in m['chapters']))
            scans = [f for f in body.findall('.//h:figure', ns) if 'text-page-scan' in f.get('class', '').split()]
            self.assertGreaterEqual(len(scans), 8)
            self.assertTrue(all(f.get('style') == 'display:none' for f in scans))
            text = ''.join(body.itertext())
            for forbidden in ('Structure preview', 'Download EPUB', 'script choice', 'Source PDF page', 'Khanda 1 · Chapter 1', 'boundary_rationale'):
                self.assertNotIn(forbidden, text)
        with zipfile.ZipFile(self.root / 'dist/mudgala-preview.epub') as z:
            nav = ET.fromstring(z.read('EPUB/nav.xhtml')).find('.//h:nav', ns)
            self.assertEqual(nav.get('hidden'), 'hidden')
            self.assertNotIn('review', ''.join(z.namelist()))
            self.assertNotIn('AGENTS.md', ''.join(z.namelist()))

    def test_sanskrit_kannada_pairing_and_split_verse(self):
        ns = {'h': 'http://www.w3.org/1999/xhtml'}
        m = json.loads((self.root / 'book.json').read_text())
        for c in m['chapters']:
            root = ET.parse(self.root / c['file'])
            units = root.findall('.//h:div[@data-unit]', ns)
            numbered = [u for u in units if '-v' in u.get('id', '')]
            self.assertEqual([u.get('id') for u in numbered], [f"{c['id']}-v{n:03}" for n in range(1,c['coverage']['last_verse']+1)])
            for u in units:
                pair = u.find('h:div[@class="verse-pair"]', ns)
                self.assertEqual([p.get('lang') for p in pair], ['sa-Knda', 'kn'])
                self.assertTrue(all(''.join(p.itertext()).strip() for p in pair))
        root = ET.parse(self.root / m['chapters'][0]['file'])
        v21 = root.find('.//h:div[@id="kh01-ch001-v021"]', ns)
        self.assertEqual(v21.get('data-source-pdf-pages'), '14 15')
        self.assertIn('ಭವಸಾಗರಾತ್', ''.join(v21.itertext()))
        self.assertIn('ಭವಸಾಗರದಿಂದ', ''.join(v21.itertext()))
        v47 = root.find('.//h:div[@id="kh01-ch001-v047"]', ns)
        self.assertIsNone(v47.get('data-fragment'))
        self.assertEqual(v47.get('data-source-pdf-pages'), '15 16')
        self.assertTrue(''.join(v47.find('h:div[@class="verse-pair"]/h:p', ns).itertext()).startswith('ಕುತ್ರ ಬುದ್ಧಿ'))
        self.run_build()
        with zipfile.ZipFile(self.root / 'dist/mudgala-preview.epub') as z:
            self.assertIn('EPUB/assets/fonts/TiroDevanagariSanskrit-Regular.ttf', z.namelist())

    def test_kannada_script_archive_and_uncertainties(self):
        import re
        ns = {'h': 'http://www.w3.org/1999/xhtml'}
        archive = json.loads((self.root / 'review/sanskrit-devanagari-source.json').read_text())
        self.assertEqual(len(archive['entries']), 55)
        for item in archive['entries']:
            p = ET.parse(self.root / item['file']).findall('.//h:p', ns)[item['paragraph'] - 1]
            self.assertEqual(p.get('lang'), 'sa-Knda')
            text = ''.join(p.itertext())
            if item['id'] == 'kh01-ch001-v047':
                self.assertEqual(item['kannada'], 'ಕುತ್ರ')
                self.assertTrue(text.startswith(item['kannada']))
            else:
                self.assertEqual(text, item['kannada'])
            self.assertIsNone(re.search('[\u0900-\u0963\u0966-\u097f]', text))
            self.assertEqual(item['devanagari'].count('⟦…⟧'), text.count('⟦…⟧'))
        m = json.loads((self.root / 'book.json').read_text())
        for c in m['chapters']:
            chapter = ET.parse(self.root / c['file'])
            unclear = chapter.findall('.//h:p[@data-reading-uncertain="true"]', ns)
            self.assertEqual(len(unclear), len(c['sanskrit_uncertain_verse_numbers']))
        self.run_build()
        with zipfile.ZipFile(self.root / 'dist/mudgala-preview.epub') as z:
            self.assertNotIn('EPUB/review/sanskrit-devanagari-source.json', z.namelist())

    def test_grouped_reading_preserves_every_verse_mapping(self):
        ns = {'h': 'http://www.w3.org/1999/xhtml'}
        m = json.loads((self.root / 'book.json').read_text())
        self.run_build()
        with zipfile.ZipFile(self.root / 'dist/mudgala-preview.epub') as z:
            epubs = {c['id']: ET.fromstring(z.read('EPUB/' + c['file'])) for c in m['chapters']}
        combined = [ET.parse(self.root / name).getroot() for name in ('dist/web/index.html', 'dist/mudgala-preview.html')]
        for c in m['chapters']:
            canonical = ET.parse(self.root / c['file'])
            expected = {u.get('id'): u.find('h:div[@class="verse-pair"]', ns) for u in canonical.findall('.//h:div[@data-unit]', ns) if '-v' in u.get('id','')}
            verse_ids = [f"{c['id']}-v{n:03}" for n in range(1,c['coverage']['last_verse']+1)]
            self.assertEqual(list(expected), verse_ids)
            outputs = [epubs[c['id']], ET.parse(self.root / 'dist/web' / c['file']).getroot()] + combined
            for root in outputs:
                chapter = root.find('.//*[@id="' + c['id'] + '"]')
                groups = chapter.findall('.//h:section[@class="verse-group"]', ns)
                self.assertEqual(len(groups), len(c['reading_groups']))
                all_slokas, all_meanings = [], []
                for group, manifest_group in zip(groups, c['reading_groups']):
                    self.assertEqual([e.get('class') for e in group], ['group-slokas', 'group-divider', 'group-meanings'])
                    slokas, meanings = list(group[0]), list(group[2])
                    ids = group.get('data-verse-ids').split()
                    self.assertEqual(ids, manifest_group['verses'])
                    self.assertEqual([e.get('data-verse-id') for e in slokas], ids)
                    self.assertEqual([e.get('data-meaning-for') for e in meanings], ids)
                    for verse_id, sloka, meaning in zip(ids, slokas, meanings):
                        sa = sloka.find('h:div[@class="entry-text"]/h:p', ns)
                        kn = meaning.find('h:div[@class="entry-text"]/h:p', ns)
                        self.assertEqual(ET.tostring(sa), ET.tostring(expected[verse_id][0]))
                        self.assertEqual(ET.tostring(kn), ET.tostring(expected[verse_id][1]))
                        self.assertEqual(sloka.find('h:div[@class="num"]', ns).text, meaning.find('h:div[@class="num"]', ns).text)
                    all_slokas += [e.get('data-verse-id') for e in slokas]
                    all_meanings += [e.get('data-meaning-for') for e in meanings]
                self.assertEqual(all_slokas, verse_ids)
                self.assertEqual(all_meanings, verse_ids)
                self.assertEqual(chapter.findall('.//h:span[@class="partial-label"]', ns), [])
                elements = list(chapter.iter())
                colophon = chapter.find('.//*[@id="' + c['id'] + '-colophon"]')
                final = chapter.find('.//*[@id="' + verse_ids[-1] + '"]')
                if c.get('coverage', {}).get('chapter_complete', True):
                    self.assertIsNotNone(colophon)
                    self.assertGreater(elements.index(colophon), elements.index(final))
                else:
                    self.assertIsNone(colophon, 'Partial chapter must not invent an ending')

    def test_context_boundaries_match_review_and_keep_connected_speech(self):
        m = json.loads((self.root / 'book.json').read_text())
        for chapter in m['chapters']:
            self.assertEqual(chapter['reading_grouping'], 'context')
            review = json.loads((self.root / chapter['grouping_review']).read_text())
            self.assertEqual([{'id': g['id'], 'verses': g['verses']} for g in review['groups']], chapter['reading_groups'])
            self.assertTrue(all(g['boundary_rationale'].strip() for g in review['groups']))
        review = json.loads((self.root / m['chapters'][0]['grouping_review']).read_text())
        ranges = [g['verse_range'] for g in review['groups']]
        for connected in ([18,21], [22,23], [26,28], [32,33], [34,35], [45,49], [58,59]):
            self.assertIn(connected, ranges)
        self.assertTrue(review['groups'][-1]['complete_available_thought'])
        self.assertGreater(len({len(g['verses']) for g in m['chapters'][0]['reading_groups']}), 1)

    def test_context_group_crosses_source_page_without_losing_mapping(self):
        def edit(m):
            groups = m['chapters'][0]['reading_groups']
            first = next(i for i,g in enumerate(groups) if g['verses'][0] == 'kh01-ch001-v018')
            self.assertEqual(groups[first + 1]['verses'][0], 'kh01-ch001-v022')
            groups[first]['verses'] += groups[first + 1]['verses']
            groups.pop(first + 1)
        self.manifest(edit)
        self.run_build()
        ns = {'h': 'http://www.w3.org/1999/xhtml'}
        root = ET.parse(self.root / 'dist/web/chapters/khanda-01/chapter-001.xhtml')
        group = root.find('.//h:section[@id="kh01-ch001-group-07"]', ns)
        expected = [f'kh01-ch001-v{n:03}' for n in range(18,24)]
        self.assertEqual([u.get('data-verse-id') for u in group[0]], expected)
        self.assertEqual([u.get('data-meaning-for') for u in group[2]], expected)
        self.assertEqual(root.find('.//h:div[@id="kh01-ch001-v021"]', ns).get('data-source-pdf-pages'), '14 15')
        self.assertEqual(root.find('.//h:div[@id="kh01-ch001-v022"]', ns).get('data-source-pdf-pages'), '15')
        self.assertEqual([s.get('data-source-pdf-page') for s in root.findall('.//h:section[@data-source-pdf-page]', ns)], ['14','15','16'])

    def test_source_records_and_preserved_published_prefix(self):
        ns = {'h': 'http://www.w3.org/1999/xhtml'}
        m = json.loads((self.root / 'book.json').read_text())
        records = json.loads((self.root / m['verse_source_archive']).read_text())
        expected = {e['id']:e for e in records['verses']}
        for e in json.loads((self.root / m['khanda2_verse_source_archive']).read_text()):
            expected[e['id']] = {'sanskrit_kannada_script': e['sanskrit_kannada'], 'kannada_meaning': e['meaning'], 'source_refs': e['source_refs']}
        actual = {}
        for c in m['chapters']:
            root = ET.parse(self.root / c['file'])
            for unit in root.findall('.//h:div[@data-unit]', ns):
                key = unit.get('id')
                if '-v' not in key:
                    continue
                pair = unit.find('h:div[@class="verse-pair"]', ns)
                self.assertEqual(''.join(pair[0].itertext()), expected[key]['sanskrit_kannada_script'])
                self.assertEqual(''.join(pair[1].itertext()), expected[key]['kannada_meaning'])
                self.assertEqual(json.loads(unit.get('data-source-refs')), expected[key]['source_refs'])
                actual[key] = pair
        self.assertEqual(set(actual), set(expected))
        self.assertEqual(len(actual), sum(c['coverage']['last_verse'] for c in m['chapters']))
        frozen = ET.parse(self.root / 'review/published-chapter1-prefix.xhtml')
        current = ET.parse(self.root / m['chapters'][0]['file'])
        for n in range(1,47):
            key = f'kh01-ch001-v{n:03}'
            old = frozen.find('.//h:div[@id="'+key+'"]/h:div[@class="verse-pair"]', ns)
            new = current.find('.//h:div[@id="'+key+'"]/h:div[@class="verse-pair"]', ns)
            self.assertEqual(ET.tostring(old), ET.tostring(new))
        split = json.loads(current.find('.//h:div[@id="kh01-ch001-v047"]', ns).get('data-source-refs'))
        self.assertEqual([e['pdf_page'] for e in split], [15,16])
        self.assertEqual([(e['file'],e['pdf_page']) for e in expected['kh01-ch003-v058']['source_refs']], [('1 TO 25.pdf',20),('26 TO 55.pdf',1)])

    def test_continuation_chapter_source_splits(self):
        m = json.loads((self.root / 'book.json').read_text())
        records = json.loads((self.root / m['verse_source_archive']).read_text())
        entries = {e['id']: e for e in records['verses']}
        for key, pages in {'kh01-ch005-v025': [6,7], 'kh01-ch006-v026': [8,9], 'kh01-ch006-v052': [9,10], 'kh01-ch007-v008': [10,11], 'kh01-ch008-v025': [13,14], 'kh01-ch008-v049': [14,15], 'kh01-ch008-v069': [15,16], 'kh01-ch009-v015': [16,17], 'kh01-ch009-v040': [17,18], 'kh01-ch010-v013': [18,19], 'kh01-ch010-v038': [19,20], 'kh01-ch011-v014': [20,21], 'kh01-ch011-v040': [21,22], 'kh01-ch011-v066': [22,23], 'kh01-ch012-v032': [24,25], 'kh01-ch013-v025': [26,27], 'kh01-ch013-v050': [27,28], 'kh01-ch014-v019': [28,29]}.items():
            self.assertEqual([r['pdf_page'] for r in entries[key]['source_refs']], pages)
            self.assertEqual({r['file'] for r in entries[key]['source_refs']}, {'26 TO 55.pdf'})
        self.assertEqual([r['pdf_page'] for r in entries['kh01-ch016-v026']['source_refs']], [1,2])
        self.assertEqual({r['file'] for r in entries['kh01-ch016-v026']['source_refs']}, {'55 TO 76.pdf'})
        for key, pages in {'kh01-ch017-v018':[2,3], 'kh01-ch017-v043':[3,4], 'kh01-ch018-v004':[4,5], 'kh01-ch018-v029':[5,6], 'kh01-ch018-v053':[6,7]}.items():
            self.assertEqual([r['pdf_page'] for r in entries[key]['source_refs']], pages)
            self.assertEqual({r['file'] for r in entries[key]['source_refs']}, {'55 TO 76.pdf'})
        # Preserve source claims of imperishable enjoyment alongside later fall discourse.
        self.assertIn('अक्षयं', entries['kh01-ch018-v036']['sanskrit_devanagari'])
        self.assertIn('सर्वेऽक्षयास्तान्', entries['kh01-ch018-v051']['sanskrit_devanagari'])
        self.assertTrue(entries['kh01-ch018-v051']['uncertain_readings'])
        self.assertIn('चानेके', entries['kh01-ch018-v060']['sanskrit_devanagari'])
        # Preserve a visibly problematic source negative and its flagged literal meaning.
        self.assertIn('नैव', entries['kh01-ch006-v008']['sanskrit_devanagari'])
        self.assertIn('ಮಾಡಲ್ಪಟ್ಟಿಲ್ಲ', entries['kh01-ch006-v008']['kannada_meaning'])
        self.assertTrue(entries['kh01-ch006-v008']['uncertain_readings'])
        self.assertIn('मत्प्रसादादद्वितीयं', entries['kh01-ch006-v055']['sanskrit_devanagari'])

    def test_group_mapping_rejects_wrong_order_duplicate_and_missing(self):
        original = (self.root / 'book.json').read_text()
        for kind in ('wrong-order', 'duplicate', 'missing'):
            with self.subTest(kind=kind):
                p = self.root / 'book.json'
                p.write_text(original)
                def edit(m):
                    ids = m['chapters'][0]['reading_groups'][0]['verses']
                    if kind == 'wrong-order':
                        ids[0], ids[1] = ids[1], ids[0]
                    elif kind == 'duplicate':
                        ids[1] = ids[0]
                    else:
                        ids.pop()
                self.manifest(edit)
                with self.assertRaisesRegex(AssertionError, 'each verse ID exactly once'):
                    self.run_build()

    def test_group_mapping_rejects_misnumbered_verse(self):
        ns = {'h': 'http://www.w3.org/1999/xhtml'}
        p = self.root / 'chapters/khanda-01/chapter-001.xhtml'
        t = ET.parse(p)
        t.find('.//h:div[@id="kh01-ch001-v001"]/h:div[@class="num"]', ns).text = '೨'
        t.write(p, encoding='utf-8', xml_declaration=True)
        with self.assertRaisesRegex(AssertionError, 'Displayed verse number'):
            self.run_build()

    def test_frontmatter_order_rejected(self):
        self.manifest(lambda m: m['frontmatter'].reverse())
        with self.assertRaisesRegex(AssertionError, 'source-page order'):
            self.run_build()

    def test_duplicate_chapter_rejected(self):
        self.manifest(lambda m: m['chapters'].append(m['chapters'][0].copy()))
        with self.assertRaisesRegex(AssertionError, 'Duplicate'):
            self.run_build()

    def test_out_of_order_rejected(self):
        self.manifest(lambda m: m['chapters'].insert(0, dict(m['chapters'][0], id='second', number=2, file='chapters/khanda-01/out-of-order.xhtml')))
        with self.assertRaisesRegex(AssertionError, 'ordered'):
            self.run_build()

    def test_blank_content_protected(self):
        self.manifest(lambda m: m['chapters'][0].update(status='blank'))
        p = self.root / 'chapters/khanda-01/chapter-001.xhtml'
        p.write_text(p.read_text().replace('</main>', 'unexpected text</main>'))
        with self.assertRaisesRegex(AssertionError, 'Blank scaffold'):
            self.run_build()

    def test_missing_asset_rejected(self):
        (self.root / 'styles/book.css').unlink()
        with self.assertRaisesRegex(AssertionError, 'Broken asset'):
            self.run_build()


if __name__ == '__main__':
    unittest.main()
