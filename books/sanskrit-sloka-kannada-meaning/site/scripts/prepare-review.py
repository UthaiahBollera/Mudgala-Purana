"""Materialize the immutable review baseline plus ID-addressed checkpoint deltas.
Never feeds canonical readers, search, sitemap, or downloads.
"""
from pathlib import Path
from ornamental import draft_chapter
import copy
import hashlib
import gzip
import html
import json
from collections import Counter
from html.parser import HTMLParser

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parent / 'review/checkpoints'
RELEASE = ROOT / '2026-11-22'
MARK = '⟦ಅಸ್ಪಷ್ಟ⟧'
REVIEW_DISPOSITIONS = {'resolved': 217, 'partial': 166, 'held': 78, 'first-pass': 87}

def load_review():
    chapters = {}
    for path in sorted((ROOT / '2026-11-12').glob('khanda-*/chapter-*.json')):
        chapter = json.loads(path.read_text())
        chapters[chapter['khanda'], chapter['chapter']] = chapter
    manifest = json.loads((ROOT / '2026-11-17/manifest.json').read_text())
    replacements = 0
    for filename, integrity in manifest['files'].items():
        raw = (ROOT / '2026-11-17' / filename).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == integrity['sha256']
        for delta in json.loads(raw)['chapters']:
            chapter = chapters[delta['khanda'], delta['chapter']]
            positions = {e['id']: i for i, e in enumerate(chapter['entries'])}
            assert len({e['id'] for e in delta['replace_entries']}) == len(delta['replace_entries'])
            for entry in delta['replace_entries']:
                chapter['entries'][positions[entry['id']]] = copy.deepcopy(entry)
                replacements += 1
            for name in ('groups', 'colophon'):
                if 'replace_' + name in delta:
                    chapter[name] = delta['replace_' + name]
            for name, value in delta.items():
                if name.startswith('separate_invocation_'):
                    chapter[name] = value
    rows = [e for c in chapters.values() for e in c['entries']]
    assert len(chapters) == manifest['total_chapters'] == 300
    assert len(rows) == len({e['id'] for e in rows}) == manifest['total_records'] == 16734
    assert replacements == manifest['replacement_rows']
    statuses = Counter(e['meaning_status'] for e in rows)
    assert statuses['accepted-qualified-draft'] == manifest['accepted_total'] == 985
    assert statuses['pending'] == manifest['pending_total'] == 548
    for c in chapters.values():
        assert [i for g in c['groups'] for i in g['verse_ids']] == [e['id'] for e in c['entries']]
    overlay = json.loads((RELEASE / 'meaning-overlay.json').read_text())
    updates = {item['id']: item for item in overlay['entries']}
    pending = {row['id']: row for row in rows if row['meaning_status'] == 'pending'}
    assert len(overlay['entries']) == len(updates) == len(pending) == 548
    assert updates.keys() == pending.keys()
    assert Counter(entry['disposition'] for entry in updates.values()) == REVIEW_DISPOSITIONS
    for ident, entry in updates.items():
        assert set(entry) == {'id', 'disposition', 'kannada_meaning'}
        row = pending[ident]
        status = entry['disposition']
        meaning = entry['kannada_meaning']
        if ident == 'kh05-ch041-v035':
            assert not row['sanskrit_devanagari'] and status == 'held'
        assert bool(meaning) and (MARK in meaning) == (status in ('partial', 'held')), ident
        row['kannada_meaning'] = meaning
        row['meaning_status'] = {
            'resolved': 'reviewed-working-draft',
            'partial': 'partial-review-draft',
            'held': 'unresolved-review-draft',
            'first-pass': 'provisional-first-pass',
        }[status]
    return manifest, list(chapters.values())

def esc(value):
    return html.escape(str(value), quote=True)

def paragraph(value, language):
    return f'<p lang="{language}" style="white-space:pre-wrap">{esc(value)}</p>' if value else ''

def render(chapter):
    parts = [paragraph(chapter.get('separate_invocation_kannada_script'), 'sa-Knda')]
    entries = {e['id']: e for e in chapter['entries']}
    for group in chapter['groups']:
        parts.append(f'<section id="{esc(group["id"])}" class="review-group">')
        for ident in group['verse_ids']:
            e = entries[ident]
            parts.append(f'<section id="{esc(ident)}" class="review-sloka" tabindex="-1"><h2><a href="#{esc(ident)}">{esc(e.get("printed_verse_label", e["verse"]))}</a></h2>')
            for prefix in ('invocation_', 'speaker_', 'sanskrit_'):
                parts.append(paragraph(e.get(prefix + 'kannada_script'), 'sa-Knda'))
            parts.append('</section>')
        parts.append('<hr/>')
        for ident in group['verse_ids']:
            e = entries[ident]
            parts.append(f'<section class="review-meaning"><h3>{esc(e.get("printed_verse_label", e["verse"]))}</h3><div data-meaning-for="{esc(ident)}">{paragraph(e["kannada_meaning"], "kn")}</div>')
            parts.append(f'<p lang="en" class="review-status">Meaning status: {esc(e["meaning_status"])}</p>')
            # Original Devanagari is review/source data, not reader-facing scripture.
            extra = {k: v for k, v in e.items() if k != 'kannada_meaning'}
            parts.append('<details><summary lang="en">Original source, numbering and historical qualifications</summary><pre lang="en">' + esc(json.dumps(extra, ensure_ascii=False, indent=2)) + '</pre></details></section>')
        parts.append('</section>')
    colophon = chapter.get('colophon')
    if colophon:
        parts.append(f'<section id="{esc(colophon.get("id", "colophon"))}" class="review-entry"><h2>ಅಧ್ಯಾಯ ಸಮಾಪ್ತಿ</h2>')
        for key, language in [('sanskrit_kannada_script','sa-Knda'), ('kannada_meaning','kn')]:
            parts.append(paragraph(colophon.get(key), language))
        parts.append('<details><summary lang="en">Colophon source and qualifications</summary><pre>' + esc(json.dumps(colophon, ensure_ascii=False, indent=2)) + '</pre></details></section>')
    return ''.join(parts)

class DraftMarkup(HTMLParser):
    """Structural defense in depth for the separately packaged K1–2 draft."""
    tags = set('section h2 h3 p a div hr abbr'.split())
    attrs = {'id', 'class', 'lang', 'style', 'data-meaning-for', 'data-reading-uncertain',
             'href', 'tabindex', 'title'}

    def __init__(self):
        super().__init__()
        self.ids = []
        self.meanings = []

    def handle_starttag(self, tag, pairs):
        assert tag in self.tags, tag
        for name, value in pairs:
            assert name in self.attrs, (tag, name)
            if name == 'id':
                assert value and value != 'reading'
                self.ids.append(value)
            elif name == 'data-meaning-for':
                assert value
                self.meanings.append(value)
            elif name == 'href':
                assert tag == 'a' and value and value.startswith('#'), value
            elif name == 'style':
                assert tag == 'p' and value == 'white-space:pre-wrap', value

    def handle_endtag(self, tag):
        assert tag in self.tags, tag


def load_k12():
    packed = (RELEASE / 'k12-review.json.gz').read_bytes()
    assert hashlib.sha256(packed).hexdigest() == '93c1470ce09a71066579dd61916210eca34e12366d54af8aeb022ccc06458538'
    raw = gzip.decompress(packed)
    chapters = json.loads(raw)
    assert [(c['khanda'], c['chapter']) for c in chapters] == [
        (k, n) for k, total in ((1, 54), (2, 74)) for n in range(1, total + 1)]
    for chapter in chapters:
        k, n = chapter['khanda'], chapter['chapter']
        assert chapter['count'] > 0 and chapter['slug'] == f'khanda-{k}/{n}'
        markup = DraftMarkup()
        markup.feed(chapter['html'])
        markup.close()
        assert len(set(markup.ids)) == len(markup.ids)
        assert len(set(markup.meanings)) == len(markup.meanings) == chapter['count'], (k, n, markup.meanings[:2])
        assert set(markup.meanings) <= set(markup.ids)
    assert sum(c['count'] for c in chapters) == 6410
    return chapters


def main():
    manifest, chapters = load_review()
    target = SITE / '.generated/review'
    target.mkdir(parents=True, exist_ok=True)
    index = []
    all_chapters = load_k12()
    for c in all_chapters:
        if c['khanda'] == 1:
            c = {**c, 'html': draft_chapter(c['html'])}
        (target / f'{c["khanda"]}-{c["chapter"]}.json').write_text(json.dumps(c, ensure_ascii=False))
        index.append({k: c[k] for k in ('khanda', 'chapter', 'count', 'slug')})
    for c in sorted(chapters, key=lambda c: (c['khanda'], c['chapter'])):
        slug = f'khanda-{c["khanda"]}/{c["chapter"]}'
        item = {'khanda': c['khanda'], 'chapter': c['chapter'], 'count': len(c['entries']), 'slug': slug}
        index.append(item)
        (target / f'{c["khanda"]}-{c["chapter"]}.json').write_text(json.dumps({**item, 'html': render(c)}, ensure_ascii=False))
    stats = {'chapters': len(index), 'records': sum(c['count'] for c in index),
             'reviewed_queue': 461, 'working_resolved': REVIEW_DISPOSITIONS['resolved'],
             'still_marked': REVIEW_DISPOSITIONS['partial'] + REVIEW_DISPOSITIONS['held'],
             'provisional': REVIEW_DISPOSITIONS['first-pass']}
    assert stats['chapters'] == 428
    (target / 'index.json').write_text(json.dumps({'stats': stats, 'chapters': index}, ensure_ascii=False))
    print(f"Prepared isolated draft reader: {stats['chapters']} chapters / {stats['records']:,} numbered records; canonical content unchanged.")

if __name__ == '__main__':
    main()
