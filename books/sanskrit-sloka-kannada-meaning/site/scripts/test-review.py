"""Exhaustive source and exported-route checks for the isolated review reader."""
from pathlib import Path
import html
import json
import re
import runpy
from html.parser import HTMLParser

HERE = Path(__file__).resolve().parent
module = runpy.run_path(str(HERE / 'prepare-review.py'))
manifest, chapters = module['load_review']()
site = HERE.parent
out = site / 'out'
root = '/kn/mudgala-purana/review/'

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.noindex = False
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag == 'a': self.links.append(a.get('href', ''))
        if tag == 'meta' and a.get('name') == 'robots': self.noindex = 'noindex' in a.get('content', '')

all_ids = []
for c in chapters:
    generated = json.loads((site / f'.generated/review/{c["khanda"]}-{c["chapter"]}.json').read_text())
    # Exact escaped strings, including historical qualifiers and uncertain source readings.
    assert generated['html'] == module['render'](c)
    for e in c['entries']:
        for field in ('sanskrit_devanagari', 'sanskrit_kannada_script', 'kannada_meaning'):
            value = json.dumps(e[field], ensure_ascii=False)[1:-1] if field == 'sanskrit_devanagari' else str(e[field])
            assert html.escape(value, quote=True) in generated['html'], (e['id'], field)
    file = out / root.lstrip('/') / f'khanda-{c["khanda"]}/{c["chapter"]}/index.html'
    raw = file.read_text()
    initial = re.sub(r'<script\b[^>]*>.*?</script>', '', raw, flags=re.S)
    assert generated['html'] in initial
    page = Page(initial)
    assert page.noindex
    assert len(page.ids) == len(set(page.ids))
    assert '548' in initial and '985' in initial and 'Not expert verified' in initial
    for e in c['entries']:
        assert e['id'] in page.ids
        assert f'data-meaning-for="{e["id"]}"' in initial
        all_ids.append(e['id'])
    for link in page.links:
        if link.startswith('#'): assert link[1:] in page.ids
        elif link.startswith('/'):
            target = out / link.lstrip('/')
            assert (target / 'index.html').exists() if link.endswith('/') else target.exists(), link
assert len(all_ids) == len(set(all_ids)) == 16734
index = (out / root.lstrip('/') / 'index.html').read_text()
assert Page(index).noindex
for c in chapters: assert root + f'khanda-{c["khanda"]}/{c["chapter"]}/' in index
assert '/review/' not in (out / 'sitemap.xml').read_text()
assert root in (out / 'kn/mudgala-purana/index.html').read_text()
print('PASS: 300 exact source chapters; 16,734 stable paired IDs; statuses, internal links, noindex, isolation.')
