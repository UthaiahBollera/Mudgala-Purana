"""Verify chapter-scoped evidence for already published spans, without text edits."""
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import csv
import hashlib
import json

from json_storage import load_json_document


def validate(root):
    root = Path(root)
    index_path = root / 'translation/Google-corroboration-index.json'
    if not index_path.exists():
        return 0

    def evidence(name, digest):
        path = (root / name).resolve()
        assert path.is_relative_to((root / 'translation').resolve()) and path.is_file(), 'Corroboration evidence missing'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'Corroboration checksum mismatch'
        return path

    merged = {}
    paths = [root / 'translation/narrative.tsv', *sorted((root / 'translation').glob('batch-*.tsv'), key=lambda p: (int(p.name.split('-')[1]), p.name))]
    for path in paths:
        with path.open() as stream:
            for row in csv.DictReader(stream, delimiter='\t'):
                merged[(int(row.get('khanda') or 1), int(row['chapter']), int(row['verse']))] = row
    registry = {x['id']: x for x in load_json_document(root / 'translation/unresolved-passages.json')['records']}
    index = json.loads(index_path.read_text())
    seen = set()
    for chapter in index['chapters']:
        review = json.loads(evidence(chapter['review_file'], chapter['review_sha256']).read_text())
        assert review['source_kind'] == 'Google_corroboration_only' and review['new_text_changes'] == 0, 'Evidence-only scope changed'
        assert review['whole_chapter_validation'] is False and review['modern_English_used_as_textual_or_grammatical_source'] is False, 'Corroboration scope overstated'
        receipt = json.loads(evidence(review['independent_receipt_file'], review['independent_receipt_sha256']).read_text())
        evidence(review['independent_review_file'], review['independent_review_sha256'])
        for f in review['evidence_files']:
            evidence(f['file'], f['sha256'])
        assert [r['key'] for r in review['records']] == chapter['keys'] == [r['key'] for r in receipt['records']], 'Corroboration keys differ'
        assert receipt['new_text_changes'] == 0 and receipt.get('corroborated_existing_records', len(receipt['records'])) == review['corroborated_existing_records'] == len(review['records']), 'Corroboration count differs'
        for record, approved in zip(review['records'], receipt['records']):
            key = tuple(record['key'])
            assert key not in seen and key[:2] == (chapter['khanda'], chapter['chapter']), 'Duplicate or wrong chapter corroboration'
            seen.add(key)
            row = merged[key]
            assert row['text'] == record['current_text'] == approved['current_text'] and row['type'] == record['current_type'] and row['source_pages'] == record['historical_source_pages'], 'Corroborated text changed'
            assert record['new_text_change'] is record['accepted_new_replacement'] is record['accepted_translation'] is None, 'New text accepted by evidence-only review'
            assert record['whole_verse_correctness_certified'] is record['whole_chapter_validation'] is record['meaning_certified'] is False, 'Printing agreement promoted to complete correctness'
            prior = json.loads(evidence(record['prior_review_file'], record['prior_review_sha256']).read_text())
            prior_record = next(r for r in prior['reviews'] if tuple(r['key']) == key)
            assert prior_record['new_row']['text'] == row['text'], 'Prior corrected text differs'
            assert prior_record.get('replacements', [prior_record.get('replacement')]) == record['previously_applied_spans_corroborated'] == approved['previously_applied_spans_corroborated'], 'Corroborated spans differ'
            assert prior_record['issues'] == record['retained_review_issues'] == approved['retained_review_issues'], 'Previous hold altered'
            for span in record['previously_applied_spans_corroborated']:
                assert span['before'] in prior_record['old_row']['text'] and span['after'] in row['text'], 'Corroborated span absent'
            ref = record['reference_source']
            assert ref['book_id'] == 'Lh0FEQAAQBAJ' and ref['page_id'] == approved['google_page_id'] and ref['page_url'] == approved['google_url'], 'Observed Google identity altered'
            url = urlparse(ref['page_url'])
            query = parse_qs(url.query)
            assert url.scheme == 'https' and url.netloc == 'books.google.co.in' and query.get('id') == [ref['book_id']] and query.get('pg') == [ref['page_id']], 'Wrong Google volume/page'
            assert Path(ref['crop_file']).name == approved['google_capture'], 'Wrong target capture'
            evidence(ref['crop_file'], ref['crop_sha256'])
            original = record['original_source']
            assert original == approved['original_source'], 'Original evidence identity altered'
            evidence(original['file'], original['sha256'])
            current = registry[f'kh{key[0]}-ch{key[1]}-v{key[2]}']
            latest = current['latest_source_corroboration']
            assert latest['review_file'] == chapter['review_file'] and latest['review_sha256'] == chapter['review_sha256'] and latest['reference_source'] == ref, 'Registry corroboration pointer differs'
            assert current['google_books_pages'] == [ref['page_id']] and current['google_books_page_url'] == ref['page_url'], 'Registry Google identity differs'
            assert latest['whole_verse_correctness_certified'] is latest['meaning_certified'] is False and latest['new_text_change'] is None, 'Registry scope overstated'
            if record['retained_review_issues']:
                assert current['hard_hold'] and current['accepted_translation'] is None and current['current_translation_review']['issues'] == record['retained_review_issues'], 'Meaning hold closed'
    return len(seen)


if __name__ == '__main__':
    print('Existing-span Google corroboration checks passed:', validate(Path(__file__).resolve().parent), 'records; no new text accepted.')
