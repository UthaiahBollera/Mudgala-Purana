"""Structural checks only; not a substitute for Sanskrit/Kannada review."""
import csv, re, sys, json
from pathlib import Path
from lxml import html
from fontTools.ttLib import TTFont

root = Path(__file__).resolve().parent
coverage = json.loads((root/'translation/coverage.json').read_text(encoding='utf-8'))
expected = int(sys.argv[1]) if len(sys.argv) > 1 else max(map(int,coverage))
boundary = coverage[str(expected)]
merged = {}
for path in [root/'translation/narrative.tsv', *sorted((root/'translation').glob('batch-*.tsv'))]:
    with path.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    keys = [(int(r['chapter']), int(r['verse'])) for r in rows]
    assert len(keys) == len(set(keys)), path
    for key, row in zip(keys, rows):
        assert row['text'] and row['type'] in {'translation','translation-partial','translation-review','mantra'}, (path,key)
        merged[key] = row
source = (root/'book/index.html').read_text(encoding='utf-8')
doc = html.fromstring(source)
actual = doc.xpath('//p[starts-with(@id,"ch")]')
assert len(actual) == len(merged)
assert len({p.get('id') for p in actual}) == len(actual)
for key, row in merged.items():
    ch,v = key
    p = doc.get_element_by_id(f'ch{ch}-v{v}')
    assert p.text_content() == re.sub(r'\s*\[[^\]]*\]', '',row['text'])
    assert p.get('lang') == ('sa-Knda' if row['type']=='mantra' else 'kn')
    assert p.get('data-source-pages') == row['source_pages']
for ch in {k[0] for k in merged}:
    verses = sorted(v for c,v in merged if c==ch)
    assert verses == list(range(1,max(verses)+1)), ch
pages = {int(p) for r in merged.values() for p in r['source_pages'].split(',')}
assert set(range(14,expected+1)) <= pages, sorted(set(range(14,expected+1))-pages)
assert max(pages) == expected
partials = [k for k,r in merged.items() if r['type']=='translation-partial']
assert partials == ([max(merged)] if boundary['tail_partial'] else []), partials
counts = [sum(c==ch for c,v in merged) for ch in range(1,max(c for c,v in merged)+1)]
assert counts == boundary['chapter_counts'], (counts,boundary)
completed = json.loads((root/'translation/completed-chapters.json').read_text(encoding='utf-8'))
assert len(doc.xpath('//p[@class="colophon"]')) == len(completed)
assert not doc.xpath('//script|//button|//form')
assert 'ಹಿಂದಿನ ಖಂಡದ ವಿಷಯ ಸೂಚಿ (ಮುಂದುವರಿಕೆ)' not in source
foreign_indic = sorted({c for p in actual for c in p.text_content() if 0x0900 <= ord(c) <= 0x0DFF and not 0x0C80 <= ord(c) <= 0x0CFF and c not in "।॥"})
assert not foreign_indic, ('Unexpected non-Kannada Indic characters', foreign_indic)
font = TTFont(root/'book/assets/TiroKannada-Regular.ttf')
cmap = font.getBestCmap()
missing = sorted({c for c in doc.text_content() if 0xC80 <= ord(c) <= 0xCFF and ord(c) not in cmap})
assert not missing, missing
print(f'Structure passed: {len(merged)} unique verse entries, source pages through {expected}, {len(partials)} tail partials, Kannada glyphs and plain-book markup.')
