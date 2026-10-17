"""Build in a disposable copy; check body-only HTML and EPUB navigation.

Run from any directory: python tests/test_reading_contents.py
No generated publication files in the checkout are changed.
"""
from pathlib import Path
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile
from lxml import etree, html

ROOT = Path(__file__).resolve().parents[1]
X = {'x': 'http://www.w3.org/1999/xhtml'}
KN = str.maketrans('0123456789', '೦೧೨೩೪೫೬೭೮೯')

def key(row):
    return int(row.get('khanda') or 1), int(row['chapter']), int(row['verse'])

def chapter_key(row):
    return (1, row) if isinstance(row, int) else (int(row.get('khanda', 1)), int(row['chapter']))

def check(base):
    merged = {}
    for path in [base/'translation/narrative.tsv', *sorted((base/'translation').glob('batch-*.tsv'))]:
        with path.open(encoding='utf-8', newline='') as stream:
            merged.update((key(row), row) for row in csv.DictReader(stream, delimiter='\t'))
    chapters = sorted({k[:2] for k in merged})
    completed = {chapter_key(row) for row in json.loads((base/'translation/completed-chapters.json').read_text())}
    reading_partial = {chapter_key(item) for item in json.loads((base/'translation/chapter-metadata.json').read_text())['chapters'] if item.get('reading_status') == 'partial'}
    doc = html.fromstring((base/'book/index.html').read_bytes())
    assert len(doc.xpath('//@id')) == len(set(doc.xpath('//@id')))
    rows = doc.xpath('//table[@class="contents"]//tr[@data-chapter]')
    assert [(int(r.get('data-khanda')), int(r.get('data-chapter'))) for r in rows] == chapters
    assert not doc.xpath('//tr[@data-source-chapter]'), 'Archival contents leaked into reading TOC'
    for section in doc.xpath('//section[contains(@class, "contents-page")]'):
        assert section.get('data-source-pages') == '', 'Generated contents claim scan provenance'
    for row, chapter in zip(rows, chapters):
        link = row.find('.//a')
        target = doc.get_element_by_id(link.get('href')[1:])
        subtitle = target.find('h3')
        if subtitle is not None:
            name = subtitle.text
        else:
            metadata = json.loads((base/'translation/chapter-metadata.json').read_text())
            item = next(item for item in metadata['chapters'] if chapter_key(item) == chapter)
            name = item['title']
            assert name == item['ordinal']+' ಅಧ್ಯಾಯ', 'Only generic duplicate subtitle may be omitted'
            expected_heading = item['section_title']
            if chapter not in completed or chapter in reading_partial:
                included = sorted(k[2] for k in merged if k[:2] == chapter)
                expected_heading += f' (ಭಾಗಶಃ · ಶ್ಲೋಕಗಳು {included[0]}–{included[-1]})'.translate(KN)
            assert target.find('h2').text == expected_heading
        partial = chapter not in completed or chapter in reading_partial
        if not partial:
            assert 'ಭಾಗಶಃ' not in target.find('h2').text
        if chapter[0] > 1 and chapter in completed:
            metadata = json.loads((base/'translation/chapter-metadata.json').read_text())
            item = next(item for item in metadata['chapters'] if chapter_key(item) == chapter)
            sections = doc.xpath('//section[starts-with(@id,$prefix)]', prefix=f'chapter-kh{chapter[0]}-{chapter[1]}-')
            colophons = [p.text_content() for section in sections for p in section.xpath('.//p[@class="colophon"]')]
            assert colophons == [item['colophon']], 'Completed chapter must retain its exact supplied colophon'
        assert link.text == name + (' (ಭಾಗಶಃ)' if partial else '')
        assert row.get('data-completion') == ('partial' if partial else 'complete')
        verses = [k[2] for k in merged if k[:2] == chapter]
        assert row.findall('td')[-1].text == f'{min(verses)}–{max(verses)}'.translate(KN)
        if subtitle is not None:
            assert target.get('data-toc-label').endswith(link.text)
        else:
            expected_label = f'ಖಂಡ {chapter[0]} · ಅಧ್ಯಾಯ {chapter[1]}'.translate(KN)
            assert target.get('data-toc-label') == expected_label + (' (ಭಾಗಶಃ)' if partial else '')
    for k, row in merged.items():
        khanda, chapter, verse = k
        vid = ('' if khanda == 1 else f'kh{khanda}-') + f'ch{chapter}-v{verse}'
        para = doc.get_element_by_id(vid)
        assert para.text_content() == re.sub(r'\s*\[[^\]]*\]', '', row['text'])
        assert para.get('data-source-pages') == row['source_pages']
        assert para.get('data-treatment') == row['type']
    with (base/'translation/frontmatter.tsv').open(encoding='utf-8', newline='') as stream:
        mantras = [r['text'] for r in csv.DictReader(stream, delimiter='\t') if r['source_page']=='8' and r['type']=='mantra']
    if mantras:
        page8 = doc.get_element_by_id('source-08')
        assert page8.get('data-source-pages') == '8'
        assert page8.xpath('.//p[@class="mantra"]/text()') == mantras
    with ZipFile(base/'dist/mudgala_purana.epub') as archive:
        parsed = {name: etree.fromstring(archive.read(name)) for name in archive.namelist() if name.endswith('.xhtml')}
        for name, content in parsed.items():
            for link in content.xpath('//x:a', namespaces=X):
                filename, _, fragment = link.get('href').partition('#')
                target = parsed[filename or name]
                if fragment:
                    assert target.xpath('//*[@id=$id]', id=fragment), (name, link.get('href'))
        chapter_links = [a for a in parsed['nav.xhtml'].xpath('//x:a', namespaces=X) if a.get('href').startswith('chapter-')]
        assert len(chapter_links) == len(chapters)
        assert [a.text for a in chapter_links] == [doc.get_element_by_id(r.find('.//a').get('href')[1:]).get('data-toc-label') for r in rows]
    print(f'Contents checks passed: {len(chapters)} chapters, {len(merged)} unchanged numbered texts, HTML/EPUB links and completion labels.')

with tempfile.TemporaryDirectory(prefix='mudgala-contents-') as tmp:
    base = Path(tmp)
    for filename in ('build_book.py', 'build_epub.py'):
        shutil.copy2(ROOT/filename, base/filename)
    shutil.copytree(ROOT/'translation', base/'translation')
    shutil.copytree(ROOT/'book/assets', base/'book/assets')
    archival = (base/'translation/contents.tsv').read_bytes()
    for filename in ('build_book.py', 'build_epub.py'):
        subprocess.run([sys.executable, str(base/filename)], check=True)
    check(base)
    assert (base/'translation/contents.tsv').read_bytes() == archival
    # A mixed-provenance fixture exercises numeric + Google Books sorting and
    # schema-2 EPUB metadata, without modifying production translations.
    path = base/'translation/narrative.tsv'
    with path.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream, delimiter='\t')
        fields, data = reader.fieldnames, list(reader)
    data[0]['source_pages'] = 'gb:Lh0FEQAAQBAJ:PT897,14,gb:Lh0FEQAAQBAJ:PT99'
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fields, delimiter='\t')
        writer.writeheader(); writer.writerows(data)
    (base/'translation/batch-manifest.json').write_text(json.dumps({'schema_version': 2, 'batches': [{'source_kind': 'google_books', 'book_id': 'Lh0FEQAAQBAJ', 'source_pages': [{'id': f'gb:Lh0FEQAAQBAJ:{page}', 'page_id': page, 'url': f'https://books.google.com/books?id=Lh0FEQAAQBAJ&pg={page}'} for page in ['PT897', 'PT898']]}]}))
    for filename in ('build_book.py', 'build_epub.py'):
        subprocess.run([sys.executable, str(base/filename)], check=True)
    check(base)
    with ZipFile(base/'dist/mudgala_purana.epub') as archive:
        metadata = etree.fromstring(archive.read('content.opf'))
        description = metadata.find('.//{http://purl.org/dc/elements/1.1/}source').text
        assert 'Google Books Lh0FEQAAQBAJ; page IDs gb:Lh0FEQAAQBAJ:PT897, gb:Lh0FEQAAQBAJ:PT898.' in description
        assert '139 TO 163' not in description
    assert (base/'translation/contents.tsv').read_bytes() == archival
