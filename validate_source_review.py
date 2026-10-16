"""Validate correction provenance and publication integrity, not linguistic accuracy."""
import csv
import ast
import io
import hashlib
from html import unescape
import json
from pathlib import Path
import posixpath
import re
import subprocess
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile
from lxml import etree, html

ROOT = Path(__file__).resolve().parent
REVIEW = ROOT / 'translation/source-review'
BASE = '116167343385b25f2c9791cc391789ccc14ed65d'

def load_rows(old=False):
    merged = {}
    paths = [ROOT/'translation/narrative.tsv', *sorted((ROOT/'translation').glob('batch-*.tsv'))]
    for path in paths:
        raw = (subprocess.check_output(['git','show',f'{BASE}:{path.relative_to(ROOT)}'],cwd=ROOT).decode() if old else path.read_text())
        for row in csv.DictReader(io.StringIO(raw), delimiter='\t'):
            merged[int(row['chapter']),int(row['verse'])] = row
    return merged

before, after = load_rows(True), load_rows()
ledger = json.loads((REVIEW/'corrections.json').read_text())
# Optional local reference copy is deliberately not redistributed in the book.
reference_path = ROOT / 'review-work/sanskrit-source.html'
reference_verses = {}
if reference_path.exists():
    raw_reference = reference_path.read_bytes()
    expected_hash = json.loads((REVIEW/'sources.json').read_text())['sanskrit_reference']['sha256']
    assert hashlib.sha256(raw_reference).hexdigest() == expected_hash, 'Reference checksum changed'
    devanagari_digits = str.maketrans('०१२३४५६७८९','0123456789')
    for match in re.finditer(r'<h2[^>]*>१\.([०-९]+).*?</h2>(.*?)(?=<h2|$)',raw_reference.decode(),re.S):
        chapter = int(match[1].translate(devanagari_digits))
        text = unescape(re.sub('<[^>]+>', '', match[2]))
        pos = 0
        for verse in re.finditer(r'॥\s*([०-९]+)\s*॥',text):
            number = int(verse[1].translate(devanagari_digits))
            # Documented reference typo: the second verse labelled 33 occurs
            # between 62 and 64 and is the existing book's verse 63.
            if chapter == 11 and number == 32 and (chapter,number) in reference_verses:
                assert 'प्राणाय प्राणनाथाय' in text[pos:verse.end()]
                number = 33
            if chapter == 50 and number == 33 and (chapter,number) in reference_verses:
                assert 'वयं विहारहीनाश्च' in text[pos:verse.end()]
                number = 63
            assert (chapter,number) not in reference_verses, ('Duplicate reference number',chapter,number)
            reference_verses[chapter,number] = re.sub(r'\(Page[^)]*\)', '', text[pos:verse.end()]).strip()
            pos = verse.end()
def normalized(text):
    text = re.sub(r'^.*खं.*पान.*$', '', text, flags=re.M)
    return re.sub(r'\s+', '', text)
seen = set()
for item in ledger:
    key = int(item['chapter']), int(item['verse'])
    assert key not in seen, ('Duplicate correction', key)
    seen.add(key)
    assert before[key]['text'] == item['old_text'], ('Original mismatch',key)
    assert after[key]['text'] == item['new_text'], ('Applied text mismatch',key)
    assert item['source_sanskrit'] and item['rationale'] and item['source_url'].startswith('https://'), key
    assert item['independent_review'] == 'accepted', ('Unreviewed correction',key)
    if reference_verses:
        assert normalized(item['source_sanskrit']) in normalized(reference_verses[key]), ('Quote/reference mismatch',key)
changed = {key for key in before if before[key]['text'] != after[key]['text']}
assert changed == seen, ('Unlogged or unapplied changes', changed ^ seen)
assert before.keys() == after.keys(), 'No verse may be silently added or removed'
for key in before:
    assert before[key]['source_pages'] == after[key]['source_pages'], ('Source mapping changed',key)
    if before[key]['type'] == 'mantra':
        assert after[key]['type'] == 'mantra', ('Mantra treatment changed',key)

def chapter_titles(code):
    titles = {}
    for node in ast.parse(code).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='chapter_names' for t in node.targets):
            titles.update(ast.literal_eval(node.value))
        if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
            call = node.value
            if isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name) and call.func.value.id=='chapter_names' and call.func.attr=='update':
                titles.update(ast.literal_eval(call.args[0]))
    return titles
old_titles = chapter_titles(subprocess.check_output(['git','show',f'{BASE}:build_book.py'],cwd=ROOT).decode())
new_titles = chapter_titles((ROOT/'build_book.py').read_text())
title_path = REVIEW/'title-corrections.json'
assert title_path.exists(), 'Title correction ledger missing'
if title_path.exists():
    titles_ledger = json.loads(title_path.read_text())
    assert len(titles_ledger) == len({x['chapter'] for x in titles_ledger}), 'Duplicate title corrections'
    for item in titles_ledger:
        assert old_titles.get(item['chapter']) == item['old_text']
        assert new_titles.get(item['chapter']) == item['new_text']
        assert item['independent_review'] == 'accepted'
    title_changed = {k for k in old_titles.keys() | new_titles.keys() if old_titles.get(k) != new_titles.get(k)}
    assert title_changed == {r['chapter'] for r in titles_ledger}

checklist = json.loads((REVIEW/'checklist.json').read_text())
assert len(checklist) == len({item['chapter'] for item in checklist}), 'Duplicate checklist chapters'
assert {item['chapter'] for item in checklist} == {k[0] for k in after}
for item in checklist:
    count = sum(k[0] == item['chapter'] for k in after)
    assert item['included_verses'] == count
    assert 0 <= item['reviewed_verses'] <= count
    if item['status'] == 'reviewed':
        assert item['reviewed_verses'] == count

unresolved = json.loads((REVIEW/'unresolved.json').read_text())
issue_keys = [(int(x['chapter']),int(x['verse'])) for x in unresolved]
assert len(issue_keys) == len(set(issue_keys)), 'Duplicate unresolved verse records'
for key, item in zip(issue_keys, unresolved):
    assert key in after, ('Unknown unresolved verse',key)
    expected = 'partially_corrected_issue_remains' if key in seen else 'unchanged_pending_source_confirmation'
    assert item['status'] == expected, ('Incorrect unresolved status',key)
    assert item['issues'] and all(isinstance(x,str) and x.strip() for x in item['issues']), key
supplementary = json.loads((REVIEW/'supplementary-unresolved.json').read_text())
assert supplementary and all(x.get('issue') and x.get('status') for x in supplementary)

raw = (ROOT/'book/index.html').read_text()
assert '\ufffd' not in raw, 'Replacement character in HTML'
doc = html.fromstring(raw)
ids = doc.xpath('//@id')
assert len(ids) == len(set(ids)), 'Duplicate HTML IDs'
actual_order = [(int(m[1]),int(m[2])) for p in doc.xpath('//p[@id]') if (m := re.fullmatch(r'ch(\d+)-v(\d+)',p.get('id')))]
assert actual_order == sorted(after), 'HTML verse order differs'
for el in doc.xpath('//*[@href or @src]'):
    ref = el.get('href') or el.get('src')
    parsed = urlsplit(ref)
    if parsed.scheme: continue
    if parsed.path: assert (ROOT/'book'/unquote(parsed.path)).exists(), ref
    elif parsed.fragment: assert unquote(parsed.fragment) in ids, ref

with ZipFile(ROOT/'dist/mudgala_purana.epub') as archive:
    names = set(archive.namelist())
    parsed_xml = {name: etree.fromstring(archive.read(name)) for name in names if name.endswith(('.xhtml','.opf','.xml'))}
    for name, root in parsed_xml.items():
        ids = root.xpath('//@id')
        assert len(ids) == len(set(ids)), ('Duplicate EPUB IDs',name)
        for el in root.xpath('//*[@href or @src]'):
            ref = el.get('href') or el.get('src')
            url = urlsplit(ref)
            if url.scheme: continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(name),unquote(url.path))) if url.path else name
            assert target in names, (name,ref)
            if url.fragment and target in parsed_xml:
                assert unquote(url.fragment) in parsed_xml[target].xpath('//@id'), (name,ref)
print(f'Provenance/integrity passed: {len(ledger)} logged corrections; {len(after)} retained entries; HTML/EPUB references and verse order checked.')
print(f'Sanskrit quotation comparison: {len(ledger)} checked against pinned local reference.' if reference_verses else 'Sanskrit quotation comparison not rerun: local reference cache absent; see sources.json and review record.')
print('This does not replace EPUBCheck, reader testing, or Sanskrit/Kannada scholarly review.')
