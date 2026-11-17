"""Materialize the immutable review baseline plus ID-addressed checkpoint deltas.
Never feeds canonical readers, search, sitemap, or downloads.
"""
from pathlib import Path
import copy
import hashlib
import html
import json
from collections import Counter

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parent / 'review/checkpoints'

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

def main():
    manifest, chapters = load_review()
    target = SITE / '.generated/review'
    target.mkdir(parents=True, exist_ok=True)
    index = []
    for c in chapters:
        slug = f'khanda-{c["khanda"]}/{c["chapter"]}'
        item = {'khanda': c['khanda'], 'chapter': c['chapter'], 'count': len(c['entries']), 'slug': slug}
        index.append(item)
        (target / f'{c["khanda"]}-{c["chapter"]}.json').write_text(json.dumps({**item, 'html': render(c)}, ensure_ascii=False))
    (target / 'index.json').write_text(json.dumps({'manifest': manifest, 'chapters': index}, ensure_ascii=False))
    print('Prepared isolated review: 300 chapters / 16,734 records; canonical content unchanged.')

if __name__ == '__main__':
    main()
