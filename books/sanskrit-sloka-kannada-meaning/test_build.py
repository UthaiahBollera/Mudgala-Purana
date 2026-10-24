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
        shutil.copytree(build.ROOT, self.root, ignore=shutil.ignore_patterns('dist', '__pycache__'))
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
            expected_spine = ['cover'] + [c['id'] for c in m['frontmatter']] + ['kh01-ch001']
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
        for name in ('dist/web/index.html', 'dist/mudgala-preview.html'):
            body = ET.parse(self.root / name).find('h:body', ns)
            self.assertEqual(body.findall('.//h:a', ns), [])
            self.assertEqual(body.findall('.//h:nav', ns), [])
            sections = body.findall('.//h:section[@data-source-pdf-page]', ns)
            self.assertEqual([n.get('data-source-pdf-page') for n in sections], [str(n) for n in range(1,16)])
            rows = body.findall('.//h:tr[@id]', ns) + body.findall('.//h:tr[@data-key]', ns)
            self.assertEqual(len(rows), 372)
            self.assertEqual([len(s.findall('.//h:tr[@id]', ns)) + len(s.findall('.//h:tr[@data-key]', ns)) for s in sections], [0,0,65,62,64,63,61,57,0,0,0,0,0,0,0])
            self.assertEqual(len(body.findall('.//h:div[@data-unit]', ns)),48)
            self.assertEqual(len(body.findall('.//h:div[@data-fragment="true"]', ns)),1)
            text = ''.join(body.itertext())
            for forbidden in ('Structure preview', 'Download EPUB', 'script choice', 'Source PDF page', 'Khanda 1 · Chapter 1'):
                self.assertNotIn(forbidden, text)
        with zipfile.ZipFile(self.root / 'dist/mudgala-preview.epub') as z:
            nav = ET.fromstring(z.read('EPUB/nav.xhtml')).find('.//h:nav', ns)
            self.assertEqual(nav.get('hidden'), 'hidden')
            self.assertNotIn('review', ''.join(z.namelist()))

    def test_sanskrit_kannada_pairing_and_split_verse(self):
        ns = {'h': 'http://www.w3.org/1999/xhtml'}
        root = ET.parse(self.root / 'chapters/khanda-01/chapter-001.xhtml')
        units = root.findall('.//h:div[@data-unit]', ns)
        self.assertEqual([u.get('data-unit') for u in units], ['ಆವಾಹನೆ'] + [str(n) for n in range(1,47)] + ['47-fragment'])
        for u in units:
            pair = u.find('h:div[@class="verse-pair"]', ns)
            self.assertEqual([p.get('lang') for p in pair], ['sa-Knda', 'kn'])
            self.assertTrue(''.join(pair[0].itertext()).strip())
            self.assertTrue(''.join(pair[1].itertext()).strip())
        v21 = root.find('.//h:div[@id="kh01-ch001-v021"]', ns)
        self.assertEqual(v21.get('data-source-pdf-pages'), '14 15')
        self.assertIn('ಭವಸಾಗರಾತ್', ''.join(v21.itertext()))
        self.assertIn('ಭವಸಾಗರದಿಂದ', ''.join(v21.itertext()))
        self.assertEqual(''.join(units[-1].find('h:div[@class="verse-pair"]/h:p', ns).itertext()), 'ಕುತ್ರ')
        self.run_build()
        with zipfile.ZipFile(self.root / 'dist/mudgala-preview.epub') as z:
            self.assertIn('EPUB/assets/fonts/TiroDevanagariSanskrit-Regular.ttf', z.namelist())

    def test_kannada_script_archive_and_uncertainties(self):
        import re
        ns = {'h': 'http://www.w3.org/1999/xhtml'}
        archive = json.loads((self.root / 'review/sanskrit-devanagari-source.json').read_text())
        self.assertEqual(len(archive['entries']), 55)
        for item in archive['entries']:
            paragraphs = ET.parse(self.root / item['file']).findall('.//h:p', ns)
            p = paragraphs[item['paragraph'] - 1]
            self.assertEqual(p.get('lang'), 'sa-Knda')
            self.assertEqual(p.get('{http://www.w3.org/XML/1998/namespace}lang'), 'sa-Knda')
            self.assertEqual(''.join(p.itertext()), item['kannada'])
            # Sanskrit letters/numerals must be Kannada; danda remains shared punctuation.
            self.assertIsNone(re.search('[\u0900-\u0963\u0966-\u097f]', ''.join(p.itertext())))
            self.assertEqual(item['devanagari'].count('⟦…⟧'), item['kannada'].count('⟦…⟧'))
        chapter = ET.parse(self.root / 'chapters/khanda-01/chapter-001.xhtml')
        unclear = chapter.findall('.//h:p[@data-reading-uncertain="true"]', ns)
        self.assertEqual(len(unclear), 5)
        self.assertEqual([e['id'] for e in archive['entries'] if '⟦…⟧' in e['devanagari']], [f'kh01-ch001-v{n:03}' for n in (10,25,32,40,46)])
        self.run_build()
        with zipfile.ZipFile(self.root / 'dist/mudgala-preview.epub') as z:
            self.assertNotIn('EPUB/review/sanskrit-devanagari-source.json', z.namelist())

    def test_grouped_reading_preserves_every_verse_mapping(self):
        ns = {'h': 'http://www.w3.org/1999/xhtml'}
        canonical = ET.parse(self.root / 'chapters/khanda-01/chapter-001.xhtml')
        expected = {u.get('id'): u.find('h:div[@class="verse-pair"]', ns) for u in canonical.findall('.//h:div[@data-unit]', ns) if u.get('id') != 'kh01-ch001-invocation'}
        verse_ids = [f'kh01-ch001-v{n:03}' for n in range(1,48)]
        self.assertEqual(list(expected), verse_ids)
        self.run_build()
        with zipfile.ZipFile(self.root / 'dist/mudgala-preview.epub') as z:
            outputs = [ET.fromstring(z.read('EPUB/chapters/khanda-01/chapter-001.xhtml'))]
        outputs += [ET.parse(self.root / name).getroot() for name in ('dist/web/index.html', 'dist/mudgala-preview.html', 'dist/web/chapters/khanda-01/chapter-001.xhtml')]
        for root in outputs:
            groups = root.findall('.//h:section[@class="verse-group"]', ns)
            self.assertEqual(len(groups), 16)
            all_slokas, all_meanings = [], []
            for group in groups:
                self.assertEqual([e.get('class') for e in group], ['group-slokas', 'group-divider', 'group-meanings'])
                slokas, meanings = list(group[0]), list(group[2])
                ids = group.get('data-verse-ids').split()
                self.assertEqual([e.get('data-verse-id') for e in slokas], ids)
                self.assertEqual([e.get('data-meaning-for') for e in meanings], ids)
                self.assertEqual(len(slokas), 2 if group is groups[-1] else 3)
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
            last = groups[-1]
            self.assertEqual(last.get('data-verse-ids').split(), verse_ids[-2:])
            self.assertEqual(''.join(last[0][-1].find('h:div[@class="entry-text"]/h:p', ns).itertext()), 'ಕುತ್ರ')
            self.assertEqual(len(last.findall('.//h:span[@class="partial-label"]', ns)), 2)
            v21 = root.find('.//h:div[@id="kh01-ch001-v021"]', ns)
            self.assertEqual(v21.get('data-source-pdf-pages'), '14 15')

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
        self.manifest(lambda m: m['chapters'].insert(0, dict(m['chapters'][0], id='second', number=2, file='chapters/khanda-01/chapter-002.xhtml')))
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
