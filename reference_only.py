"""Literal OCR-only chapter provenance and provisional reading sections.

Editorial locators deliberately never enter the numbered-verse TSV model.
"""
import hashlib
import json
import re
from html import escape
from pathlib import Path

SOURCE_KIND = 'user_uploaded_reference_OCR_only'
NOTICE = ('ಉಲ್ಲೇಖದ OCR ಪಠ್ಯವನ್ನು ಮಾತ್ರ ಆಧರಿಸಿದ ತಾತ್ಕಾಲಿಕ ಕನ್ನಡ ಅನುವಾದ. '
          'ಈ ಕನ್ನಡಪಾಠದ ಪರಿಶೀಲನೆಗೆ ಮೂಲಚಿತ್ರಗಳನ್ನು ಬಳಸಿಲ್ಲ. ಇಲ್ಲಿನ ಸ್ಥಳಸೂಚಿಗಳು ಸಂಪಾದಕೀಯ ಗುರುತುಗಳು ಮಾತ್ರ; '
          'ದೃಢಪಡಿಸಿದ ಶ್ಲೋಕಸಂಖ್ಯೆಗಳಲ್ಲ. ಅಸ್ಪಷ್ಟ ಪಾಠ ಮತ್ತು ಅರ್ಥಗಳು ಪರಿಶೀಲನೆಯಲ್ಲಿವೆ.')
KN = str.maketrans('0123456789', '೦೧೨೩೪೫೬೭೮೯')

def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()

def blocks(draft):
    yield from draft['segments']
    yield draft['colophon']
    for name in ('closing_benedictions', 'terminal_closure'):
        if draft.get(name):
            yield draft[name]

def display_text(record, block):
    draft = record['draft_original']
    key = block.get('segment_key')
    if key is None:
        key = next(k for k in ('colophon','closing_benedictions','terminal_closure')
                   if draft.get(k) is block)
    text = block['kannada_translation']
    for item in record.get('display_transliterations', {}).get(key, []):
        before, after = item['source'], item['kannada']
        assert item['scope'] == 'literal_script_only_reading_unaccepted'
        assert before and all(0x900 <= ord(c) <= 0x97f for c in before)
        assert after == ''.join(chr(ord(c)+0x380) for c in before)
        assert text.count(before) == 1
        text = text.replace(before, after, 1)
    return text

def validate(data):
    assert data['schema_version'] == 1 and data['source_kind'] == SOURCE_KIND
    keys, ids, previous_end = [], set(), None
    totals = {'reference_only_chapters': 0, 'editorial_locators': 0,
              'verified_verse_total': None}
    for record in data['chapters']:
        draft = record['draft_original']
        manifest = draft['original_manifest']
        k, ch = draft['khanda'], draft['chapter']
        assert k == 9 and 25 <= ch <= 41
        keys.append((k, ch))
        assert record['draft_canonical_sha256'] == digest(draft), 'Draft changed'
        assert record['manifest_canonical_sha256'] == digest(manifest), 'Raw manifest changed'
        assert manifest['source_kind'] == SOURCE_KIND
        assert manifest['stable_verse_keys'] is None
        assert draft['accepted_translation'] is None and draft['accepted_reading'] is None
        assert draft['publication_clearance'] is None
        pages = {}
        for page in record['literal_pages']:
            assert page['reference_page'] not in pages
            assert hashlib.sha256(page['text'].encode()).hexdigest() == page['sha256']
            pages[page['reference_page']] = page
        def span(item):
            page, a, b = item['reference_page'], item['char_start'], item['char_end_exclusive']
            raw = item.get('raw_source', item.get('text'))
            assert 0 <= a < b <= len(pages[page]['text'])
            assert pages[page]['text'][a:b] == raw, 'Literal source span changed'
            return (page, a, b)
        expected = []
        for part in manifest['source_parts']:
            assert part['scan_available'] is False and part['argon_available'] is False
            assert part['accepted_reading'] is None
            assert part['reference_sha256'] == pages[part['reference_page']]['sha256']
            expected.append(span(part))
        body = []
        chapter_spans = []
        for ordinal, segment in enumerate(draft['segments'], 1):
            sid = segment['segment_key']
            assert sid in (f'kh{k:02}-ch{ch:03}-loc{ordinal:03}', f'kh{k:02}-ch{ch:03}-refseg-{ordinal:03}'), 'Not an editorial locator'
            assert sid not in ids
            ids.add(sid)
            body.extend(span(s) for s in segment['source_spans'])
        for block in blocks(draft):
            assert block['accepted_reading'] is None and block['accepted_translation'] is None
            assert block['kannada_translation'].strip()
            assert isinstance(block['uncertainties'], list)
            foreign = {c for c in display_text(record, block)
                       if 0x900 <= ord(c) <= 0xdff and not 0xc80 <= ord(c) <= 0xcff
                       and c not in '।॥'}
            assert not foreign, ('Foreign Indic letters in Kannada draft', ch, foreign)
            chapter_spans.extend(span(s) for s in block['source_spans'])
        assert body == sorted(body), 'Body out of source order'
        used = []
        for page, a, b in expected:
            selected = [s for s in body if s[0] == page and a <= s[1] and s[2] <= b]
            at = a
            for s in selected:
                assert s[1] == at, 'Body gap or overlap'
                at = s[2]
            assert at == b, 'Incomplete source coverage'
            used.extend(selected)
        assert used == body, 'Body span outside original source parts'
        assert chapter_spans == sorted(chapter_spans), 'Nonverse material out of order'
        for page, a, b in chapter_spans:
            if previous_end is not None:
                assert (page, a) >= previous_end, 'Cross-chapter source overlap'
            previous_end = (page, b)
        if ch == 25:
            assert manifest['partial_saved_Argon_supplement'], 'Partial Argon evidence lost'
            assert manifest['partial_saved_Argon_note']
        totals['reference_only_chapters'] += 1
        totals['editorial_locators'] += len(draft['segments'])
    assert keys == sorted(set(keys)), 'Duplicate or unordered reference chapter'
    return totals

def load(root):
    path = Path(root) / 'translation' / 'reference-only-chapters.json'
    if not path.exists():
        return {'schema_version': 1, 'source_kind': SOURCE_KIND, 'chapters': []}
    data = json.loads(path.read_text())
    validate(data)
    validate_publication_index(root,data)
    return data

def chapter_id(k, ch, part=1):
    return f'reference-chapter-kh{k}-{ch}-{part}'

def render(data):
    """Return sections; reuse existing CSS without adding an invocation or verse marker."""
    validate(data)
    if not data['chapters']:
        return []
    def e(s): return escape(str(s), quote=True)
    def kn(s): return str(s).translate(KN)
    def section(sid, title, body, kind, label=None):
        return (f'<section class="page {kind}" id="{e(sid)}" data-source-pages="" '
                f'data-title="{e(title)}" data-toc-label="{e(label or title)}">'
                f'<h2>{e(title)}</h2>{body}<div class="page-number" aria-hidden="true"></div></section>')
    toc = '<p class="caption">'+NOTICE+'</p><table class="contents"><thead><tr><th>ಅಧ್ಯಾಯ</th><th>ವಿಷಯ</th><th>ಸ್ಥಳಸೂಚಿಗಳು</th></tr></thead><tbody>'
    for record in data['chapters']:
        d = record['draft_original']; k, ch = d['khanda'], d['chapter']
        title = f'ಖಂಡ {kn(k)} · ಅಧ್ಯಾಯ {kn(ch)} · ಉಲ್ಲೇಖ ಪಠ್ಯ ಮಾತ್ರ'
        toc += (f'<tr data-reference-chapter="{ch}" data-khanda="{k}" data-completion="reference-only-provisional">'
                f'<td>{kn(ch)}</td><td><a href="#{chapter_id(k,ch)}">{e(title)}</a></td>'
                f'<td>{kn(len(d["segments"]))}</td></tr>')
    pages = [section('contents-reference-only', 'ಉಲ್ಲೇಖ ಪಠ್ಯಗಳ ವಿಷಯ ಸೂಚಿ', toc+'</tbody></table>', 'contents-page reference-only-contents')]
    for record in data['chapters']:
        d = record['draft_original']; k, ch = d['khanda'], d['chapter']
        title = f'ಖಂಡ {kn(k)} · ಅಧ್ಯಾಯ {kn(ch)} · ಉಲ್ಲೇಖ ಪಠ್ಯ ಮಾತ್ರ'
        def paragraph(block, sid, kind):
            page_hashes = {p['reference_page']:p['sha256'] for p in record['literal_pages']}
            pointers = [f'ocr:{page_hashes[s["reference_page"]]}:p{s["reference_page"]}:c{s["char_start"]}-{s["char_end_exclusive"]}'
                        for s in block['source_spans']]
            return (f'<p id="{e(sid)}" class="{kind}" lang="kn" data-treatment="reference-only-provisional" '
                    f'data-source-kind="{SOURCE_KIND}" data-source-spans="{e(",".join(pointers))}">{e(display_text(record, block))}</p>')
        chunks = [d['segments'][i:i+4] for i in range(0,len(d['segments']),4)]
        for number, chunk in enumerate(chunks, 1):
            body = '<p class="caption">'+NOTICE+'</p>' if number == 1 else ''
            if number == 1 and ch == 25:
                body += '<p class="caption">ಈ ಅಧ್ಯಾಯದ ಕೆಲವು ಪುಟಗಳ ಹಿಂದಿನ ಪಠ್ಯವೂ ಪ್ರತ್ಯೇಕವಾಗಿ ದಾಖಲಾಗಿದೆ; ಮುಂದುವರಿದ ಪುಟದ ಮೂಲಚಿತ್ರ ಲಭ್ಯವಿಲ್ಲ.</p>'
            for block in chunk:
                body += paragraph(block, block['segment_key'], 'reference-translation')
            if number == len(chunks):
                body += paragraph(d['colophon'], f'kh{k:02}-ch{ch:03}-reference-colophon', 'reference-colophon caption')
                for name in ('closing_benedictions','terminal_closure'):
                    if d.get(name):
                        body += paragraph(d[name], f'kh{k:02}-ch{ch:03}-{name.replace("_","-")}', 'reference-closing caption')
            pages.append(section(chapter_id(k,ch,number), title, body, 'reference-only-chapter', title))
    return pages

def validate_rendered(data, doc):
    """Check the actual reading HTML, including localized uncertainty text."""
    totals = validate(data)
    expected = {}
    for record in data['chapters']:
        d = record['draft_original']; k,ch = d['khanda'],d['chapter']
        for block in d['segments']:
            expected[block['segment_key']] = (record,block)
        expected[f'kh{k:02}-ch{ch:03}-reference-colophon'] = (record,d['colophon'])
        for name in ('closing_benedictions','terminal_closure'):
            if d.get(name):
                expected[f'kh{k:02}-ch{ch:03}-{name.replace("_","-")}'] = (record,d[name])
        first = doc.xpath('//*[@id=$id]',id=chapter_id(k,ch))
        assert len(first)==1 and NOTICE in ''.join(first[0].itertext())
        assert not first[0].xpath('.//p[@class="mantra"]'), 'Fabricated opening invocation'
        row = doc.xpath('//tr[@data-reference-chapter=$chapter and @data-khanda=$khanda]',chapter=str(ch),khanda=str(k))
        assert len(row)==1 and row[0].get('data-completion')=='reference-only-provisional'
        assert row[0].xpath('.//a/@href')==['#'+chapter_id(k,ch)]
        assert row[0].xpath('./td[last()]/text()')==[str(len(d['segments'])).translate(KN)]
    nodes = doc.xpath('//p[@data-source-kind=$kind]',kind=SOURCE_KIND)
    assert len(nodes)==len(expected)
    for node in nodes:
        record,block=expected[node.get('id')]
        assert ''.join(node.itertext())==display_text(record,block), 'Provisional Kannada text changed'
        assert node.get('data-treatment')=='reference-only-provisional'
        hashes={p['reference_page']:p['sha256']for p in record['literal_pages']}
        pointers=[f'ocr:{hashes[s["reference_page"]]}:p{s["reference_page"]}:c{s["char_start"]}-{s["char_end_exclusive"]}'for s in block['source_spans']]
        assert node.get('data-source-spans')==','.join(pointers)
    assert len(doc.xpath('//tr[@data-reference-chapter]'))==totals['reference_only_chapters']
    return totals

def validate_publication_index(root, data):
    root = Path(root)
    manifest = json.loads((root/'translation/batch-manifest.json').read_text())
    index = manifest['reference_only_index']
    path = root/index['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==index['sha256']
    totals = validate(data)
    assert index['verified_verse_total'] is None
    assert index['reference_chapters']==[[r['draft_original']['khanda'],r['draft_original']['chapter']]for r in data['chapters']]
    assert index['editorial_locator_count']==totals['editorial_locators']
    registry_path=root/index['registry_file']
    assert hashlib.sha256(registry_path.read_bytes()).hexdigest()==index['registry_sha256']
    registry=json.loads(registry_path.read_text())
    expected=[s['segment_key']for r in data['chapters']for s in r['draft_original']['segments']]
    assert [r['id']for r in registry['records']]==expected
    nonverse_expected=[]
    for r in data['chapters']:
        d=r['draft_original']
        for name in ('colophon','closing_benedictions','terminal_closure'):
            if d.get(name):
                suffix='reference-colophon'if name=='colophon'else name.replace('_','-')
                nonverse_expected.append(f'kh{d["khanda"]:02}-ch{d["chapter"]:03}-{suffix}')
    assert [r['id']for r in registry['nonverse_records']]==nonverse_expected
    expected_blocks={}
    for record in data['chapters']:
        d=record['draft_original']
        for b in d['segments']:expected_blocks[b['segment_key']]=(record,b)
        for name in ('colophon','closing_benedictions','terminal_closure'):
            if d.get(name):
                suffix='reference-colophon'if name=='colophon'else name.replace('_','-')
                expected_blocks[f'kh{d["khanda"]:02}-ch{d["chapter"]:03}-{suffix}']=(record,d[name])
    for row in registry['records']+registry['nonverse_records']:
        record,block=expected_blocks[row['id']]
        assert row['source_spans']==block['source_spans']and row['uncertainties']==block['uncertainties']
        assert row['draft_source_sha256']==record['draft_source_sha256']
        assert row['book_id']is None and row['google_books_pages']is None and row['google_books_page_url']is None
    assert len(registry['chapter_evidence'])==len(data['chapters'])
    for row,record in zip(registry['chapter_evidence'],data['chapters']):
        d=record['draft_original'];m=d['original_manifest']
        assert [row['khanda'],row['chapter']]==[d['khanda'],d['chapter']]
        assert row['manifest_canonical_sha256']==record['manifest_canonical_sha256']
        assert row['scan_available']is False and row['argon_continuation_available']is False
        assert row['partial_saved_Argon_present']==bool(m.get('partial_saved_Argon_supplement'))
        assert row['original_holds']==m.get('holds')and row['original_missing_source_evidence']==m.get('missing_source_evidence')
    for r in registry['nonverse_records']:
        assert r['kind']=='reference_nonverse'and r['status']=='open_reference_only_nonverse_reading'
        assert r['accepted_translation']is None and r['accepted_reading']is None
    for r in registry['records']:
        assert r['kind']=='editorial_locator' and r['status']=='open_reference_only_reading'
        assert r['accepted_translation'] is None and r['accepted_reading'] is None
        assert r['book_id'] is None and r['google_books_pages'] is None and r['google_books_page_url'] is None
    return totals
