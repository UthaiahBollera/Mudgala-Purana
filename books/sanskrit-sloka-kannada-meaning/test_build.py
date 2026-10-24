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
            self.assertEqual([n.get('idref') for n in opf.findall('o:spine/o:itemref', ns)], ['cover', 'kh01-ch001'])
            for n in opf.findall('o:manifest/o:item', ns):
                self.assertIn('EPUB/' + n.get('href'), z.namelist())
            self.assertEqual(z.read('EPUB/chapters/khanda-01/chapter-001.xhtml'), (self.root / 'chapters/khanda-01/chapter-001.xhtml').read_bytes())
        standalone = (self.root / 'dist/mudgala-preview.html').read_text()
        self.assertIn('ಮುದ್ಗಲ ಪುರಾಣ', standalone)
        self.assertIn('data:image/png;base64,', standalone)
        self.assertIn('data:font/ttf;base64,', standalone)
        self.assertNotIn('src="assets/', standalone)

    def test_reader_has_only_cover_and_blank_content(self):
        self.run_build()
        ns = {'h': 'http://www.w3.org/1999/xhtml'}
        for name in ('dist/web/index.html', 'dist/mudgala-preview.html',
                     'dist/web/chapters/khanda-01/chapter-001.xhtml'):
            body = ET.parse(self.root / name).find('h:body', ns)
            self.assertEqual(''.join(body.itertext()).strip(), '')
            self.assertEqual(body.findall('.//h:a', ns), [])
            self.assertEqual(body.findall('.//h:nav', ns), [])
            self.assertNotIn('script choice', (self.root / name).read_text())
        with zipfile.ZipFile(self.root / 'dist/mudgala-preview.epub') as z:
            nav = ET.fromstring(z.read('EPUB/nav.xhtml')).find('.//h:nav', ns)
            self.assertEqual(nav.get('hidden'), 'hidden')
            for name in z.namelist():
                if name.endswith(('.xhtml', '.opf')):
                    self.assertNotIn('Structure preview', z.read(name).decode())

    def test_duplicate_chapter_rejected(self):
        self.manifest(lambda m: m['chapters'].append(m['chapters'][0].copy()))
        with self.assertRaisesRegex(AssertionError, 'Duplicate'):
            self.run_build()

    def test_out_of_order_rejected(self):
        self.manifest(lambda m: m['chapters'].insert(0, dict(m['chapters'][0], id='second', number=2, file='chapters/khanda-01/chapter-002.xhtml')))
        with self.assertRaisesRegex(AssertionError, 'ordered'):
            self.run_build()

    def test_blank_content_protected(self):
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
