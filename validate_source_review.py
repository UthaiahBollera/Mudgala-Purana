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

# Public correction commit (identical tree to the local review snapshot).
REVIEWED = 'dcd504671e5ed48c84344c20174bb7c6b28c37f8'

def git_bytes(commit, path):
    return subprocess.check_output(['git','show',f'{commit}:{path}'], cwd=ROOT)
def translation_paths(commit=None):
    if commit:
        names = subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'translation'], cwd=ROOT).decode().splitlines()
        return [name for name in names if name == 'translation/narrative.tsv'] + sorted(
            name for name in names if re.fullmatch(r'translation/batch-[^/]+\.tsv', name))
    return ['translation/narrative.tsv'] + sorted(str(path.relative_to(ROOT)) for path in (ROOT/'translation').glob('batch-*.tsv'))
def verse_key(row):
    return int(row.get('khanda') or 1), int(row['chapter']), int(row['verse'])
def parse_rows(raw):
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8')), delimiter='\t'))
    keys = [verse_key(row) for row in rows]
    assert len(keys) == len(set(keys)), 'Duplicate key within TSV'
    return dict(zip(keys, rows))
def load_rows(commit=None):
    merged = {}
    for name in translation_paths(commit):
        raw = git_bytes(commit, name) if commit else (ROOT/name).read_bytes()
        merged.update(parse_rows(raw))
    return merged

GOOGLE_BOOKS_BY_KHANDA = {1: 'Lh0FEQAAQBAJ', 2: 'fZcHEQAAQBAJ'}

def source_ids(value, khanda=None):
    ids = value.split(',')
    assert ids and len(ids) == len(set(ids)), ('Invalid or duplicate source identifiers', value)
    for page in ids:
        if re.fullmatch(r'[1-9]\d*', page):
            assert khanda in (None, 1), ('Historical PDF source belongs to Khanda 1', khanda, page)
            continue
        match = re.fullmatch(r'gb:([^:]+):PT[1-9]\d*', page)
        assert match and match[1] in GOOGLE_BOOKS_BY_KHANDA.values(), ('Invalid or duplicate source identifiers', value)
        if khanda is not None:
            assert match[1] == GOOGLE_BOOKS_BY_KHANDA.get(khanda), ('Google Books source does not match khanda', khanda, page)
    return set(ids)

def row_content(row):
    return {field: row[field] for field in ('source_pages', 'type', 'text')}

# The correction audit remains pinned to its original, completed review.
# Continuation is checked separately below; new files never enter this audit.
before, after = load_rows(BASE), load_rows(REVIEWED)
current = load_rows()
for name in subprocess.check_output(['git','ls-tree','-r','--name-only',REVIEWED,'translation/source-review'], cwd=ROOT).decode().splitlines():
    assert (ROOT/name).read_bytes() == git_bytes(REVIEWED, name), ('Historical review file changed', name)
for name in translation_paths(REVIEWED):
    assert (ROOT/name).read_bytes() == git_bytes(REVIEWED, name), ('Reviewed translation file changed; use a logged continuation batch', name)
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
            if chapter == 11 and number == 32 and (1,chapter,number) in reference_verses:
                assert 'प्राणाय प्राणनाथाय' in text[pos:verse.end()]
                number = 33
            if chapter == 50 and number == 33 and (1,chapter,number) in reference_verses:
                assert 'वयं विहारहीनाश्च' in text[pos:verse.end()]
                number = 63
            assert (1,chapter,number) not in reference_verses, ('Duplicate reference number',chapter,number)
            reference_verses[1,chapter,number] = re.sub(r'\(Page[^)]*\)', '', text[pos:verse.end()]).strip()
            pos = verse.end()
def normalized(text):
    text = re.sub(r'^.*खं.*पान.*$', '', text, flags=re.M)
    return re.sub(r'\s+', '', text)
seen = set()
for item in ledger:
    key = 1, int(item['chapter']), int(item['verse'])
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
new_titles = chapter_titles(git_bytes(REVIEWED, 'build_book.py').decode())
current_titles = chapter_titles((ROOT/'build_book.py').read_text())
assert all(current_titles.get(key) == value for key,value in new_titles.items()), 'Reviewed chapter title changed'
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
assert {item['chapter'] for item in checklist} == {k[1] for k in after}
for item in checklist:
    count = sum(k[1] == item['chapter'] for k in after)
    assert item['included_verses'] == count
    assert 0 <= item['reviewed_verses'] <= count
    if item['status'] == 'reviewed':
        assert item['reviewed_verses'] == count

unresolved = json.loads((REVIEW/'unresolved.json').read_text())
issue_keys = [(1,int(x['chapter']),int(x['verse'])) for x in unresolved]
assert len(issue_keys) == len(set(issue_keys)), 'Duplicate unresolved verse records'
for key, item in zip(issue_keys, unresolved):
    assert key in after, ('Unknown unresolved verse',key)
    expected = 'partially_corrected_issue_remains' if key in seen else 'unchanged_pending_source_confirmation'
    assert item['status'] == expected, ('Incorrect unresolved status',key)
    assert item['issues'] and all(isinstance(x,str) and x.strip() for x in item['issues']), key
supplementary = json.loads((REVIEW/'supplementary-unresolved.json').read_text())
assert supplementary and all(x.get('issue') and x.get('status') for x in supplementary)

# Replay every continuation batch against the reviewed snapshot. Existing
# entries are immutable except exact, independently accepted partial completions.
manifest_path = ROOT/'translation/batch-manifest.json'
new_paths = sorted(set(translation_paths()) - set(translation_paths(REVIEWED)))
manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else None
assert manifest is not None or not new_paths, 'Continuation batch manifest missing'
replayed = dict(after)
addition_count = completion_count = 0
if manifest is not None:
    assert manifest['schema_version'] in (1, 2), 'Unknown batch manifest version'
    assert manifest['reviewed_commit'] == REVIEWED, 'Wrong reviewed snapshot'
    batches = manifest['batches']
    manifest_paths = ['translation/'+batch['file'] for batch in batches]
    assert manifest_paths == new_paths, ('Unlisted, duplicate, or out-of-order continuation batches', manifest_paths, new_paths)
    previous_end = 133
    google_pages = set()
    google_unresolved_keys = set()
    coverage = json.loads((ROOT/'translation/coverage.json').read_text(encoding='utf-8'))
    for batch, name in zip(batches, manifest_paths):
        assert Path(batch['file']).name == batch['file'], 'Batch file must be a filename'
        raw_batch = (ROOT/name).read_bytes()
        assert hashlib.sha256(raw_batch).hexdigest() == batch['sha256'], ('Batch checksum mismatch', name)
        assert batch['review_status'] == 'accepted', ('Unreviewed continuation batch', name)
        review_path = Path(batch['review_file'])
        assert not review_path.is_absolute() and review_path.parts[0] == 'translation' and '..' not in review_path.parts, ('Review must be inside translation', name)
        review_path = (ROOT/review_path).resolve()
        assert review_path.is_relative_to((ROOT/'translation').resolve()) and review_path.is_file(), ('Review artifact missing or outside translation', name)
        assert hashlib.sha256(review_path.read_bytes()).hexdigest() == batch['review_sha256'], ('Review artifact checksum mismatch', name)
        google_batch = manifest['schema_version'] == 2
        if google_batch:
            assert batch['source_kind'] == 'google_books' and batch['book_id'] in GOOGLE_BOOKS_BY_KHANDA.values(), ('Wrong Google Books source', name)
            if 'volume' in batch:
                assert type(batch['volume']) is int and GOOGLE_BOOKS_BY_KHANDA.get(batch['volume']) == batch['book_id'], ('Batch volume does not match Google Books source', name)
            assert not {'source_pdf', 'source_sha256', 'pdf_page_range', 'source_page_range'} & batch.keys(), ('Google Books batch must not claim PDF coverage', name)
            source_pages = batch['source_pages']
            assert source_pages, ('Missing Google Books pages', name)
            allowed_pages = set()
            for page in source_pages:
                page_id = page['page_id']
                assert re.fullmatch(r'PT[1-9]\d*', page_id), ('Invalid Google Books page ID', name)
                assert page['id'] == f"gb:{batch['book_id']}:{page_id}", ('Mislabeled Google Books page', name)
                assert page['url'] == f"https://books.google.com/books?id={batch['book_id']}&pg={page_id}", ('Wrong Google Books page URL', name)
                assert page['id'] not in allowed_pages, ('Duplicate Google Books page', name)
                allowed_pages.add(page['id'])
            google_pages.update(allowed_pages)
            boundary_key = batch['coverage_boundary']
            assert isinstance(boundary_key, str) and not boundary_key.isdecimal() and boundary_key in coverage, ('Named Google Books coverage missing', name)
            boundary = coverage[boundary_key]
            assert {'chapter_counts_by_khanda', 'partial_keys', 'non_narrative_source_pages', 'source_pages'} <= boundary.keys(), ('Incomplete Google Books coverage', name)
            assert boundary['non_narrative_source_pages'] == [], ('Unexpected Google Books interstitial coverage', name)
            assert len(boundary['source_pages']) == len(set(boundary['source_pages'])) and set(boundary['source_pages']) == google_pages, ('Google Books coverage differs from declared pages', name)
        else:
            assert batch['source_pdf'] and re.fullmatch(r'[0-9a-f]{64}', batch['source_sha256']), ('Missing source identity', name)
            pdf_start, pdf_end = map(int, batch['pdf_page_range'])
            page_start, page_end = map(int, batch['source_page_range'])
            assert 1 <= pdf_start <= pdf_end and page_end-page_start == pdf_end-pdf_start, ('Invalid page ranges', name)
            assert page_start == previous_end+1, ('Nonconsecutive batch source coverage', name)
            assert batch['coverage_boundary'] == page_end and str(page_end) in coverage, ('Coverage boundary missing', name)
            previous_end = page_end
            allowed_pages = {str(page) for page in range(page_start,page_end+1)}
        rows = parse_rows(raw_batch)
        if google_batch:
            review = json.loads(review_path.read_text(encoding='utf-8'))
            assert review['source_kind'] == 'google_books' and review['book_id'] == batch['book_id'], ('Wrong review source', name)
            if 'volume' in review:
                assert type(review['volume']) is int and GOOGLE_BOOKS_BY_KHANDA.get(review['volume']) == review['book_id'], ('Review volume does not match Google Books source', name)
            records = review['verses']
            reviewed_keys = [tuple(map(int, record['key'])) for record in records]
            assert len(reviewed_keys) == len(set(reviewed_keys)) and set(reviewed_keys) == set(rows), ('Missing, duplicate or extra verse reviews', name)
            for key, record in zip(reviewed_keys, records):
                assert len(key) == 3 and GOOGLE_BOOKS_BY_KHANDA.get(key[0]) == batch['book_id'], ('Reviewed verse khanda does not match Google Books volume', key)
                source_ids(rows[key]['source_pages'], key[0])
                status = record['review_status']
                assert status in {'accepted', 'accepted_with_unresolved_reading'}, ('Verse review not accepted', key)
                open_issues = [issue for issue in record.get('issues', []) if isinstance(issue, dict) and issue.get('status') == 'open']
                if status == 'accepted_with_unresolved_reading':
                    assert rows[key]['type'] == 'translation-review', ('Unresolved verse must be marked for review', key)
                    assert open_issues, ('Unresolved verse has no open issues', key)
                    visible_text = re.sub(r'\s*\[[^\]]*\]', '', rows[key]['text'])
                    notices = re.findall(r'\([^()]+\)', visible_text)
                    assert any(re.search(r'[\u0c80-\u0cff]', notice) and any(word in notice for word in ('ಪರಿಶೀಲನೆ', 'ಅನಿಶ್ಚಿತ', 'ಖಚಿತವಾಗಿಲ್ಲ')) for notice in notices), ('Missing visible Kannada uncertainty notice', key)
                    registry_path = ROOT/'translation/unresolved-passages.json'
                    assert registry_path.is_file(), ('Unresolved registry missing', key)
                    registry = json.loads(registry_path.read_text(encoding='utf-8'))
                    matches = [item for item in registry['records'] if item.get('id') == f'kh{key[0]}-ch{key[1]}-v{key[2]}']
                    assert len(matches) == 1, ('Missing or duplicate unresolved registry entry', key)
                    issue_record = matches[0]
                    assert issue_record['book_id'] == batch['book_id'] and issue_record.get('khanda', 1) == key[0] and issue_record['chapter'] == key[1] and issue_record['verse_start'] == issue_record['verse_end'] == key[2], ('Unresolved registry verse identity mismatch', key)
                    assert issue_record['status'] == 'open_google_books_reading_question', ('Unresolved registry is not open', key)
                    assert issue_record['issues'] == record['issues'] and issue_record['source_sanskrit'] == record['source_sanskrit'], ('Unresolved registry evidence mismatch', key)
                    page_ids = [page.rsplit(':', 1)[1] for page in rows[key]['source_pages'].split(',') if page.startswith('gb:')]
                    assert issue_record['google_books_pages'] == page_ids, ('Unresolved registry source pages mismatch', key)
                    assert issue_record['google_books_page_url'] in [f"https://books.google.com/books?id={batch['book_id']}&pg={page}" for page in page_ids], ('Unresolved registry page URL mismatch', key)
                    google_unresolved_keys.add(key)
                else:
                    assert not open_issues and rows[key]['type'] != 'translation-review', ('Unresolved verse falsely marked accepted', key)
                    google_unresolved_keys.discard(key)
                assert record['text'] == rows[key]['text'] and record['source_pages'] == rows[key]['source_pages'], ('Review differs from accepted verse', key)
                assert isinstance(record['source_sanskrit'], str) and re.search(r'[\u0900-\u097f]', record['source_sanskrit']), ('Missing Sanskrit evidence', key)
                if rows[key].get('source_sanskrit'):
                    assert record['source_sanskrit'] == rows[key]['source_sanskrit'], ('Review Sanskrit differs from batch', key)
            review_required = [tuple(map(int, key)) for key in boundary.get('review_required_keys', [])]
            assert len(review_required) == len(set(review_required)) and set(review_required) == google_unresolved_keys, ('Coverage unresolved keys mismatch', name)
        additions = {key for key in rows if key not in replayed}
        listed_additions = [tuple(map(int, key)) for key in batch['added_keys']]
        assert all(len(key) == 3 and all(x > 0 for x in key) for key in listed_additions), name
        assert len(listed_additions) == len(set(listed_additions)), ('Duplicate added key', name)
        assert additions == set(listed_additions), ('Unlogged batch additions', name, additions ^ set(listed_additions))
        completions = batch['boundary_completions']
        completion_keys = [tuple(map(int, item['key'])) for item in completions]
        assert len(completion_keys) == len(set(completion_keys)), ('Duplicate boundary completion', name)
        assert set(rows) - additions == set(completion_keys), ('Unlogged replacement of existing verse', name)
        for item, key in zip(completions, completion_keys):
            old_row, new_row = replayed[key], rows[key]
            assert row_content(old_row) == item['old_row'], ('Boundary old row mismatch', key)
            assert row_content(new_row) == item['new_row'], ('Boundary new row mismatch', key)
            assert old_row['type'] == 'translation-partial' and new_row['type'] != 'translation-partial', ('Only partial completions may replace an existing verse', key)
            assert item['rationale'] and item['source_evidence'] and item['review_status'] == 'accepted', ('Unreviewed boundary completion', key)
            old_pages = source_ids(old_row['source_pages'])
            new_pages = source_ids(new_row['source_pages'])
            assert old_pages < new_pages and new_pages-old_pages <= allowed_pages, ('Boundary source mapping mismatch', key)
        for key in additions:
            source_pages = source_ids(rows[key]['source_pages'])
            assert source_pages and source_pages <= allowed_pages, ('Addition outside batch source pages', key)
        replayed.update(rows)
        addition_count += len(additions)
        completion_count += len(completions)
assert set(replayed) == set(current), 'Continuation replay differs from current verse keys'
for key in replayed:
    assert row_content(replayed[key]) == row_content(current[key]), ('Continuation replay differs from current verse', key)

raw = (ROOT/'book/index.html').read_text()
assert '\ufffd' not in raw, 'Replacement character in HTML'
doc = html.fromstring(raw)
ids = doc.xpath('//@id')
assert len(ids) == len(set(ids)), 'Duplicate HTML IDs'
actual_order = [(int(m[1] or 1),int(m[2]),int(m[3])) for p in doc.xpath('//p[@id]') if (m := re.fullmatch(r'(?:kh(\d+)-)?ch(\d+)-v(\d+)',p.get('id')))]
assert actual_order == sorted(current), 'HTML verse order differs'
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
print(f'Provenance/integrity passed: {len(ledger)} logged corrections; {len(after)} reviewed entries retained; {addition_count} logged additions; {completion_count} boundary completions; HTML/EPUB references and verse order checked.')
print(f'Sanskrit quotation comparison: {len(ledger)} checked against pinned local reference.' if reference_verses else 'Sanskrit quotation comparison not rerun: local reference cache absent; see sources.json and review record.')
print('This does not replace EPUBCheck, reader testing, or Sanskrit/Kannada scholarly review.')
