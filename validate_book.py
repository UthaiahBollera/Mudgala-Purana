"""Structural checks only; not a substitute for Sanskrit/Kannada review."""
import csv, re, sys, json
from pathlib import Path
from lxml import html
from fontTools.ttLib import TTFont

def verse_key(row):
    return int(row.get('khanda') or 1), int(row['chapter']), int(row['verse'])
def chapter_key(item):
    return (1, int(item)) if isinstance(item, int) else (int(item.get('khanda', 1)), int(item['chapter']))
def verse_id(khanda, chapter, verse):
    return ('' if khanda == 1 else f'kh{khanda}-') + f'ch{chapter}-v{verse}'

root = Path(__file__).resolve().parent
coverage = json.loads((root/'translation/coverage.json').read_text(encoding='utf-8'))
manifest_path = root/'translation/batch-manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else None
expected = (sys.argv[1] if len(sys.argv) > 1 else
            str(manifest['batches'][-1]['coverage_boundary']) if manifest and manifest['batches'] else
            str(max(int(key) for key in coverage if key.isdecimal())))
boundary = coverage[expected]
google_boundary = not expected.isdecimal()
GOOGLE_BOOKS_BY_KHANDA = {1: 'Lh0FEQAAQBAJ', 2: 'fZcHEQAAQBAJ'}

def source_ids(value, khanda=None):
    ids = value.split(',')
    assert ids and len(ids) == len(set(ids)), ('Invalid or duplicate source identifiers', value)
    for page in ids:
        if re.fullmatch(r'[1-9]\d*', page):
            assert khanda in (None, 1), ('Historical PDF source belongs to Khanda 1', khanda, page)
            continue
        if re.fullmatch(r'pdf:[0-9a-f]{64}:p[1-9]\d*', page):
            continue
        match = re.fullmatch(r'gb:([^:]+):PT[1-9]\d*', page)
        assert match and match[1] in GOOGLE_BOOKS_BY_KHANDA.values(), ('Invalid or duplicate source identifiers', value)
        if khanda is not None:
            assert match[1] == GOOGLE_BOOKS_BY_KHANDA.get(khanda), ('Google Books source does not match khanda', khanda, page)
    return set(ids)

merged = {}
for path in [root/'translation/narrative.tsv', *sorted((root/'translation').glob('batch-*.tsv'), key=lambda p: (int(p.name.split('-')[1]) if p.name.split('-')[1].isdigit() else 0, p.name))]:
    with path.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    keys = [verse_key(r) for r in rows]
    assert all(all(x > 0 for x in key) for key in keys), path
    assert len(keys) == len(set(keys)), path
    for key, row in zip(keys, rows):
        assert row['text'] and row['type'] in {'translation','translation-partial','translation-review','mantra'}, (path,key)
        merged[key] = row
source = (root/'book/index.html').read_text(encoding='utf-8')
doc = html.fromstring(source)
actual = [p for p in doc.xpath('//p[@id]') if re.fullmatch(r'(?:kh[1-9]\d*-)?ch[1-9]\d*-v[1-9]\d*', p.get('id'))]
assert len(doc.xpath('//@id')) == len(set(doc.xpath('//@id'))), 'Duplicate HTML IDs'
assert len(actual) == len(merged)
assert len({p.get('id') for p in actual}) == len(actual)
for key, row in merged.items():
    p = doc.get_element_by_id(verse_id(*key))
    assert p.text_content() == re.sub(r'\s*\[[^\]]*\]', '',row['text'])
    assert p.get('lang') == ('sa-Knda' if row['type']=='mantra' else 'kn')
    assert p.get('data-source-pages') == row['source_pages']
chapter_keys = {key[:2] for key in merged}
metadata = json.loads((root/'translation/chapter-metadata.json').read_text(encoding='utf-8'))
gaps = metadata.get('source_gaps', [])
assert {g['id'] for g in gaps} == set(boundary.get('source_gaps', [])), 'Untracked source gap'
declared_missing = boundary.get('missing_verse_ranges', [])
assert declared_missing == [r for g in gaps for r in g.get('missing_verse_ranges', []) if (r['khanda'], r['chapter']) in chapter_keys], 'Missing verse range lacks source-gap evidence'
for gap in gaps:
    assert gap['status'] == 'awaiting_replacement_scan'
    source_ids(gap['source_page'])
    node = doc.get_element_by_id(gap['id'])
    assert node.get('data-source-pages') == gap['source_page']
    assert gap['text'] in node.text_content()
for fragment in boundary.get('fragment_only_keys', []):
    key = tuple(fragment)
    assert key in merged and 'ಅಪೂರ್ಣ ಶ್ಲೋಕ' in merged[key]['text'], 'Fragment lacks visible incomplete-verse notice'
for chapter in chapter_keys:
    verses = sorted(key[2] for key in merged if key[:2] == chapter)
    missing = {v for r in declared_missing if (r['khanda'], r['chapter']) == chapter for v in range(r['verse_start'], r['verse_end']+1)}
    assert not missing & set(verses), 'Gap overlaps supplied verses'
    assert verses == [v for v in range(1,max(verses)+1) if v not in missing], chapter
pages = set().union(*(source_ids(r['source_pages'], key[0]) for key, r in merged.items()))
metadata_path = root/'translation/chapter-metadata.json'
metadata = json.loads(metadata_path.read_text(encoding='utf-8')) if metadata_path.exists() else {}
interstitials = metadata.get('interstitial_pages', [])
non_narrative = {str(page['source_page']) for page in interstitials}
assert len(non_narrative) == len(interstitials), 'Duplicate interstitial source pages'
assert non_narrative == {str(page) for page in boundary.get('non_narrative_source_pages', [])}, 'Untracked non-narrative source pages'
assert not pages & non_narrative, 'A source page cannot be both narrative and interstitial'
for page in interstitials:
    assert chapter_key(page['after']) in chapter_keys, page
    matches = doc.xpath('//section[@id=$id]', id=page['id'])
    assert len(matches) == int(page.get('render', True)), page
    if matches:
        assert matches[0].get('data-source-pages') == str(page['source_page']), page
covered_pages = pages | non_narrative
if google_boundary:
    assert {'chapter_counts_by_khanda', 'partial_keys', 'non_narrative_source_pages', 'source_pages'} <= boundary.keys(), 'Incomplete Google Books coverage record'
    assert not non_narrative, 'Google Books coverage must not inherit PDF interstitial pages'
    declared = boundary['source_pages']
    assert declared and len(declared) == len(set(declared)), 'Missing or duplicate Google Books coverage pages'
    assert all(page.startswith('gb:') for page in declared), 'Invalid Google Books coverage page'
    source_ids(','.join(declared))
    assert {page for page in covered_pages if page.isdecimal()} == {str(page) for page in range(14,134)}, 'Historical PDF coverage must stay exactly 14–133'
    assert {page for page in covered_pages if page.startswith('gb:')} == set(declared), 'Unknown or missing Google Books coverage pages'
    assert {page for page in covered_pages if page.startswith('pdf:')} == set(boundary.get('pdf_source_pages', [])), 'Unknown or missing local PDF coverage pages'
else:
    assert all(page.isdecimal() for page in covered_pages), 'Google Books source pages require a named coverage boundary'
    numeric_pages = {int(page) for page in covered_pages}
    assert set(range(14,int(expected)+1)) <= numeric_pages, sorted(set(range(14,int(expected)+1))-numeric_pages)
    assert max(numeric_pages) == int(expected)
if google_boundary:
    review_required = sorted(tuple(map(int, key)) for key in boundary.get('review_required_keys', []))
    actual_review_required = sorted(key for key, row in merged.items() if row['type'] == 'translation-review' and any(page.startswith(('gb:', 'pdf:')) for page in source_ids(row['source_pages'])))
    assert review_required == actual_review_required, 'Google Books review-required coverage differs from marked verses'
partials = sorted(k for k,r in merged.items() if r['type']=='translation-partial')
expected_partials = (sorted(tuple(map(int, key)) for key in boundary['partial_keys'])
                     if 'partial_keys' in boundary else ([max(merged)] if boundary['tail_partial'] else []))
assert len(expected_partials) == len(set(expected_partials)), 'Duplicate partial keys'
assert partials == expected_partials, (partials, expected_partials)
counts_by_khanda = {
    str(khanda): [sum(k == khanda and c == ch for k,c,v in merged)
                 for ch in range(1, max(c for k,c,v in merged if k == khanda)+1)]
    for khanda in sorted({key[0] for key in merged})
}
if 'chapter_counts_by_khanda' in boundary:
    assert counts_by_khanda == boundary['chapter_counts_by_khanda'], (counts_by_khanda,boundary)
else:
    assert set(counts_by_khanda) == {'1'}, 'Multi-khanda coverage requires chapter_counts_by_khanda'
    assert counts_by_khanda['1'] == boundary['chapter_counts'], (counts_by_khanda,boundary)
completed_rows = json.loads((root/'translation/completed-chapters.json').read_text(encoding='utf-8'))
completed = [chapter_key(item) for item in completed_rows]
assert len(completed) == len(set(completed)), 'Duplicate completed chapters'
assert set(completed) <= chapter_keys, 'Unknown completed chapter'
assert not set(completed) & {key[:2] for key in partials}, 'Partial chapter marked completed'
assert len(doc.xpath('//p[@class="colophon"]')) == len(completed)
for khanda, chapter in chapter_keys:
    prefix = f'chapter-{chapter}-' if khanda == 1 else f'chapter-kh{khanda}-{chapter}-'
    sections = doc.xpath('//section[starts-with(@id,$prefix)]', prefix=prefix)
    colophons = [p for section in sections for p in section.xpath('.//p[@class="colophon"]')]
    assert len(colophons) == int((khanda, chapter) in completed), (khanda, chapter)
assert not doc.xpath('//script|//button|//form')
assert 'ಹಿಂದಿನ ಖಂಡದ ವಿಷಯ ಸೂಚಿ (ಮುಂದುವರಿಕೆ)' not in source
foreign_indic = sorted({c for p in actual for c in p.text_content() if 0x0900 <= ord(c) <= 0x0DFF and not 0x0C80 <= ord(c) <= 0x0CFF and c not in "।॥"})
assert not foreign_indic, ('Unexpected non-Kannada Indic characters', foreign_indic)
font = TTFont(root/'book/assets/TiroKannada-Regular.ttf')
cmap = font.getBestCmap()
missing = sorted({c for c in doc.text_content() if 0xC80 <= ord(c) <= 0xCFF and ord(c) not in cmap})
assert not missing, missing
print(f'Structure passed: {len(merged)} unique verse entries, source pages through {expected}, {len(partials)} explicitly checked partials, Kannada glyphs and plain-book markup.')

from reference_only import load as load_reference_only, validate_rendered as validate_reference_rendered
reference_stats=validate_reference_rendered(load_reference_only(root),doc)
print('Reference-only reading checks passed:',reference_stats)
