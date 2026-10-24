#!/usr/bin/env python3
"""Build web, standalone HTML and EPUB 3 from one ordered manifest (stdlib only)."""
from pathlib import Path
import base64
import copy
import html
import json
import mimetypes
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
NS = {'h': 'http://www.w3.org/1999/xhtml'}

# EPUB font media types must not depend on the build host's MIME database.
mimetypes.add_type('font/ttf', '.ttf')
mimetypes.add_type('font/otf', '.otf')
mimetypes.add_type('font/woff', '.woff')
mimetypes.add_type('font/woff2', '.woff2')


def safe_path(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(f'Missing or unsafe source: {value}')
    return path


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or 'application/octet-stream'
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()


def document(title, body, stylesheet='styles/book.css', language='kn'):
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" '
            'xmlns:epub="http://www.idpf.org/2007/ops" '
            f'lang="{language}" xml:lang="{language}"><head><meta charset="utf-8"/>'
            '<meta name="viewport" content="width=device-width, initial-scale=1"/>'
            f'<title>{html.escape(title)}</title><link rel="stylesheet" href="{stylesheet}"/>'
            f'</head><body>{body}</body></html>')


def reader_document(section):
    """Keep canonical verse/meaning pairs; arrange reader groups by stable IDs."""
    original = safe_path(section['file']).read_bytes()
    groups = section.get('reading_groups')
    if groups is None:
        return original
    tree = ET.fromstring(original)
    q = lambda tag: '{' + NS['h'] + '}' + tag
    main = tree.find('.//h:main', NS)
    parents = {child: parent for parent in main.iter() for child in parent}
    units = [u for u in main.findall('.//h:div[@data-unit]', NS)
             if re.fullmatch(re.escape(section['id']) + r'-v\d{3}', u.get('id', ''))]
    verse_ids = [u.get('id') for u in units]
    assert verse_ids and verse_ids == sorted(set(verse_ids)), 'Canonical verse IDs must be unique and ordered'
    grouped_ids = [verse_id for group in groups for verse_id in group['verses']]
    assert grouped_ids == verse_ids, 'Reading groups must cover each verse ID exactly once in source order'
    assert all(g['verses'] for g in groups), 'Reading groups must be nonempty; boundaries are reviewed by context, not fixed size'
    group_ids = [g['id'] for g in groups]
    original_ids = {e.get('id') for e in main.iter() if e.get('id')}
    assert len(group_ids) == len(set(group_ids)) and not set(group_ids) & original_ids, 'Duplicate reading group ID'
    by_id = {u.get('id'): u for u in units}
    for group in groups:
        original_units = [by_id[verse_id] for verse_id in group['verses']]
        container = parents[original_units[0]]
        start, end = (u.get('data-unit').removesuffix('-fragment') for u in (original_units[0], original_units[-1]))
        label = ('ಶ್ಲೋಕಗಳು ' + start + '–' + end).translate(str.maketrans('0123456789', '೦೧೨೩೪೫೬೭೮೯'))
        wrapper = ET.Element(q('section'), {'class': 'verse-group', 'id': group['id'], 'data-verse-ids': ' '.join(group['verses']), 'aria-label': label})
        slokas = ET.SubElement(wrapper, q('div'), {'class': 'group-slokas'})
        ET.SubElement(wrapper, q('hr'), {'class': 'group-divider'})
        meanings = ET.SubElement(wrapper, q('div'), {'class': 'group-meanings'})
        for verse_id, unit in zip(group['verses'], original_units):
            pair = unit.find('h:div[@class="verse-pair"]', NS)
            paragraphs = list(pair) if pair is not None else []
            assert [p.get('lang') for p in paragraphs] == ['sa-Knda', 'kn'], 'Verse/meaning mapping requires exactly one sloka and one meaning'
            number = str(int(verse_id.rsplit('-v', 1)[1]))
            assert unit.get('data-unit').removesuffix('-fragment') == number, 'Verse number does not match its stable ID'
            expected_number = number.translate(str.maketrans('0123456789', '೦೧೨೩೪೫೬೭೮೯'))
            expected_label = expected_number + ('…' if unit.get('data-fragment') == 'true' else '')
            assert unit.find('h:div[@class="num"]', NS).text == expected_label, 'Displayed verse number does not match its stable ID'
            assert unit.get('data-fragment') == 'true' or ''.join(paragraphs[0].itertext()).endswith('॥' + expected_number + '॥'), 'Sloka ending number does not match its stable ID'
            for is_meaning, block, paragraph in ((False, slokas, paragraphs[0]), (True, meanings, paragraphs[1])):
                attrs = ({'class': 'unit meaning-entry', 'id': verse_id + '-meaning', 'data-meaning-for': verse_id}
                         if is_meaning else dict(unit.attrib, **{'class': 'unit sloka-entry', 'data-verse-id': verse_id}))
                row = ET.SubElement(block, q('div'), attrs)
                row.append(copy.deepcopy(unit.find('h:div[@class="num"]', NS)))
                content = ET.SubElement(row, q('div'), {'class': 'entry-text'})
                content.append(copy.deepcopy(paragraph))
                if (is_meaning and int(unit.get('data-unit').removesuffix('-fragment')) in section.get('coverage', {}).get('meaning_gaps', [])
                        and not paragraph.findall('.//h:abbr[@class="reading-uncertain"]', NS)):
                    ET.SubElement(content, q('abbr'), {'class': 'reading-uncertain', 'title': 'ಅರ್ಥದ ದೃಢೀಕರಣ ಬಾಕಿ'}).text = '†'
                if unit.get('data-fragment') == 'true':
                    ET.SubElement(content, q('span'), {'class': 'partial-label'}).text = 'ಅಪೂರ್ಣ'
        container.insert(list(container).index(original_units[0]), wrapper)
        for unit in original_units:
            parents[unit].remove(unit)
    ET.register_namespace('', NS['h'])
    return ET.tostring(tree, encoding='utf-8', xml_declaration=True)


def build():
    m = json.loads((ROOT / 'book.json').read_text(encoding='utf-8'))
    chapters = m['chapters']
    frontmatter = m.get('frontmatter', [])
    sources = frontmatter + chapters
    reading_sections = frontmatter + [c for c in chapters if c.get('include', True)]
    ids = [c['id'] for c in sources]
    paths = [c['file'] for c in sources]
    order = [(c['khanda'], c['number']) for c in chapters]
    assert ids and len(ids) == len(set(ids)) and len(paths) == len(set(paths)), 'Duplicate chapter'
    assert order == sorted(set(order)), 'Chapters must be unique and ordered by khanda/chapter'
    front_order = [c['source_pdf_page'] for c in frontmatter]
    assert front_order == sorted(set(front_order)), 'Front matter must follow unique source-page order'
    for c in sources:
        tree = ET.parse(safe_path(c['file']))
        main = tree.find('.//h:main', NS)
        assert main is not None and main.get('id') == c['id']
        if c['status'] == 'blank':
            assert not ''.join(main.itertext()).strip() and len(main) == 0, 'Blank scaffold contains content'
        for node in tree.iter():
            for attr in ('src', 'href'):
                ref = node.get(attr)
                if ref and not ref.startswith(('#', 'https:', 'http:', 'data:')):
                    target = (safe_path(c['file']).parent / ref.split('#')[0]).resolve()
                    assert target.is_relative_to(ROOT) and target.is_file(), f'Broken asset: {ref}'
    rendered = {c['file']: reader_document(c) for c in sources}
    out = ROOT / 'dist'
    if out.exists():
        shutil.rmtree(out)
    web = out / 'web'
    web.mkdir(parents=True)
    for folder in ('assets', 'styles', 'chapters', 'frontmatter'):
        shutil.copytree(ROOT / folder, web / folder)
    for c in sources:
        (web / c['file']).write_bytes(rendered[c['file']])
    esc = html.escape
    toc = ''.join(f'<li><a href="{esc(c["file"])}">{esc(c["title"])}</a></li>' for c in reading_sections)
    cover = f'<section class="cover" id="cover" aria-label="{esc(m["title"])}"><img src="{m["cover"]}" width="1024" height="1536" alt="{esc(m["title"])}"/></section>'
    # Portable preview: all images/fonts/styles are embedded, no server or network required.
    css = safe_path(m['stylesheet']).read_text(encoding='utf-8')
    css = re.sub(r'url\("([^\"]+)"\)', lambda x: 'url("' + data_uri((ROOT / 'styles' / x[1]).resolve()) + '")', css)
    content = ''
    web_content = ''
    for c in reading_sections:
        main = ET.fromstring(rendered[c['file']]).find('.//h:main', NS)
        ET.register_namespace('', NS['h'])
        fragment = ET.tostring(main, encoding='unicode').replace('<main ', '<section ', 1).replace('</main>', '</section>')
        def embed_reference(match):
            ref = html.unescape(match[2])
            if ref.startswith(('#', 'https:', 'http:', 'data:')):
                return match[0]
            target = (safe_path(c['file']).parent / ref).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                raise ValueError(f'Broken standalone asset: {ref}')
            return match[1] + '="' + data_uri(target) + '"'
        def web_reference(match):
            ref = html.unescape(match[2])
            if ref.startswith(('#', 'https:', 'http:', 'data:')):
                return match[0]
            target = (safe_path(c['file']).parent / ref).resolve()
            if not target.is_relative_to(ROOT) or not target.is_file():
                raise ValueError(f'Broken web asset: {ref}')
            return match[1] + '="' + target.relative_to(ROOT).as_posix() + '"'
        web_content += re.sub(r'(src|href)="([^"]+)"', web_reference, fragment)
        fragment = re.sub(r'(src|href)="([^"]+)"', embed_reference, fragment)
        content += fragment
    reading = f'<main class="reader">{cover}{content}</main>'
    (web / 'index.html').write_text(document(m['title'], f'<main class="reader">{cover}{web_content}</main>'), encoding='utf-8')
    standalone = document(m['title'], reading)
    standalone = standalone.replace(f'<link rel="stylesheet" href="{m["stylesheet"]}"/>', '<style>' + css + '</style>')
    standalone = standalone.replace(f'src="{m["cover"]}"', f'src="{data_uri(safe_path(m["cover"]))}"')
    (out / 'mudgala-preview.html').write_text(standalone, encoding='utf-8')
    # EPUB keeps one XHTML file per chapter, in manifest order.
    epub_nav = '<nav epub:type="toc" id="toc" hidden="hidden"><h1>Contents</h1><ol><li><a href="cover.xhtml">Cover</a></li>' + toc + '</ol></nav>'
    items = [('nav', 'nav.xhtml', 'application/xhtml+xml', 'nav'), ('cover', 'cover.xhtml', 'application/xhtml+xml', '')]
    items += [(c['id'], c['file'], 'application/xhtml+xml', '') for c in reading_sections]
    resources = sorted([p for folder in ('assets', 'styles') for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix != '.txt'])
    for i, p in enumerate(resources):
        rel = p.relative_to(ROOT).as_posix()
        items.append((f'asset{i}', rel, mimetypes.guess_type(p)[0] or 'application/octet-stream', 'cover-image' if rel == m['cover'] else ''))
    manifest = ''.join(f'<item id="{i}" href="{p}" media-type="{mime}"' + (f' properties="{prop}"' if prop else '') + '/>' for i, p, mime, prop in items)
    spine = '<itemref idref="cover"/>' + ''.join(f'<itemref idref="{c["id"]}"/>' for c in reading_sections)
    opf = f'''<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="book-id">{m['identifier']}</dc:identifier><dc:title>{esc(m['title'])}</dc:title>''' + ''.join(f'<dc:language>{l}</dc:language>' for l in m['languages']) + f'<meta property="dcterms:modified">{m["modified"]}</meta></metadata><manifest>{manifest}</manifest><spine>{spine}</spine></package>'
    with zipfile.ZipFile(out / 'mudgala-preview.epub', 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml', '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr('EPUB/package.opf', opf)
        z.writestr('EPUB/nav.xhtml', document('Contents', epub_nav, language='en'))
        z.writestr('EPUB/cover.xhtml', document(m['title'], cover))
        for c in reading_sections:
            z.writestr('EPUB/' + c['file'], rendered[c['file']])
        for p in resources:
            z.write(p, 'EPUB/' + p.relative_to(ROOT).as_posix())
        z.write(ROOT / 'assets/fonts/TiroKannada-OFL.txt', 'EPUB/assets/fonts/TiroKannada-OFL.txt')
        z.write(ROOT / 'assets/fonts/TiroDevanagariSanskrit-OFL.txt', 'EPUB/assets/fonts/TiroDevanagariSanskrit-OFL.txt')
    shutil.copy2(out / 'mudgala-preview.epub', web / 'mudgala-preview.epub')
    print(f'Built {len(frontmatter)} front-matter section(s) and {sum(c.get('include', True) for c in chapters)} chapter(s): {out}')


if __name__ == '__main__':
    build()
