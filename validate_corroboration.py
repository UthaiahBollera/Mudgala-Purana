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
        assert review['source_kind'] in ('Google_corroboration_only', 'Google_comparison_only') and review['new_text_changes'] == 0, 'Evidence-only scope changed'
        assert review['whole_chapter_validation'] is False and review['modern_English_used_as_textual_or_grammatical_source'] is False, 'Corroboration scope overstated'
        receipt = json.loads(evidence(review['independent_receipt_file'], review['independent_receipt_sha256']).read_text())
        evidence(review['independent_review_file'], review['independent_review_sha256'])
        for f in review['evidence_files']:
            evidence(f['file'], f['sha256'])
        assert [r['key'] for r in review['records']] == chapter['keys'] == [r['key'] for r in receipt['records']], 'Corroboration keys differ'
        scopes = [r.get('evidence_scope', 'all_applied_spans') for r in review['records']]
        assert all(scope in ('all_applied_spans', 'partial_applied_spans', 'edition_difference_retained', 'Google_glyph_comparison_hold') for scope in scopes), 'Unknown comparison scope'
        assert receipt['new_text_changes'] == 0 and review.get('compared_existing_records', len(scopes)) == len(scopes), 'Comparison count differs'
        assert review['corroborated_existing_records'] == scopes.count('all_applied_spans'), 'Partial/different wording falsely counted as corroborated'
        assert review.get('partial_records', 0) == scopes.count('partial_applied_spans') and review.get('edition_difference_records', 0) == scopes.count('edition_difference_retained'), 'Comparison limitations miscounted'
        assert review.get('glyph_comparison_hold_records', 0) == scopes.count('Google_glyph_comparison_hold'), 'Glyph holds miscounted'
        if 'fully_wording_corroborated_records' in receipt:
            assert receipt['fully_wording_corroborated_records'] == review['corroborated_existing_records'] and receipt['partial_records'] == review['partial_records'] and receipt['edition_difference_records'] == review['edition_difference_records'], 'Independent comparison counts changed'
        elif 'corroborated_existing_records' in receipt:
            assert receipt['corroborated_existing_records'] == review['corroborated_existing_records'], 'Independent corroboration count changed'
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
            previous = prior_record.get('replacements', [prior_record.get('replacement')])
            approved_previous = approved.get('previously_applied_spans', approved.get('previously_applied_spans_corroborated'))
            assert previous == record.get('previously_applied_spans', record['previously_applied_spans_corroborated']) == approved_previous, 'Prior applied spans differ'
            scope = record.get('evidence_scope', 'all_applied_spans')
            assert record['status'] == approved['status'], 'Independent comparison status changed'
            if scope == 'all_applied_spans':
                assert record['previously_applied_spans_corroborated'] == previous and 'partial' not in approved['status'] and 'edition_wording_difference' not in approved['status'] and approved['status'] != 'Google_conjunct_comparison_hold', 'Uncorroborated wording promoted'
            else:
                approved_holds = approved.get('additional_holds', [approved['additional_hold']] if approved.get('additional_hold') else [])
                assert record['additional_source_holds'] == approved_holds and record['additional_source_holds'] and record['no_silent_edition_harmonization'] is True, 'Edition/partial hold hidden'
                if scope == 'partial_applied_spans':
                    allowed_partial = {(1, 8, 46): ('partial_corroboration_initial_compound_comparison_hold', {'original': 'हृद्विज्ञबोधात्मक', 'Google': 'द्विज्ञबोधात्मक'}), (1, 12, 24): ('partial_corroboration_edition_difference_retained', {'original': 'गाणपत्यास्ते', 'Google': 'गाणपत्याः स्युः'})}
                    assert key in allowed_partial and approved['status'] == allowed_partial[key][0] and record['previously_applied_spans_corroborated'] == previous[1:], 'Disagreeing initial wording falsely corroborated'
                    assert record['source_disagreement'] == allowed_partial[key][1], 'Initial wording disagreement altered'
                elif scope == 'Google_glyph_comparison_hold':
                    assert key == (1, 28, 18) and approved['status'] == 'Google_conjunct_comparison_hold' and record['previously_applied_spans_corroborated'] == [], 'Uncertain Google conjunct falsely corroborated'
                    assert record['source_comparison_hold'] == {'original': 'पंचवक्त्रधरायैव', 'Google_provisional': approved['google_evidence']['reading'], 'Google_conjunct_certain': False, 'English_gloss_used_to_supply_letters': False}, 'Google uncertainty hidden or English supplied letters'
                else:
                    assert key == (1, 8, 54) and approved['status'] == 'edition_wording_difference_retained' and record['previously_applied_spans_corroborated'] == [], 'Edition difference falsely corroborated'
                    assert record['source_disagreement'] == {'original': 'अभेदैकात्मक', 'Google': 'अभेदमेकात्मक'}, 'Eka compound difference altered'
            assert prior_record['issues'] == record['retained_review_issues'] == approved['retained_review_issues'], 'Previous hold altered'
            for span in record['previously_applied_spans_corroborated']:
                assert span['before'] in prior_record['old_row']['text'] and span['after'] in row['text'], 'Corroborated span absent'
            ref = record['reference_source']
            approved_ref = approved.get('google_evidence', approved)
            approved_page = approved_ref.get('google_page_id', approved_ref.get('page_id'))
            approved_url = approved_ref.get('google_url', approved_ref.get('verified_url'))
            assert ref['book_id'] == 'Lh0FEQAAQBAJ' and ref['page_id'] == approved_page and ref['page_url'] == approved_url, 'Observed Google identity altered'
            url = urlparse(ref['page_url'])
            query = parse_qs(url.query)
            assert url.scheme == 'https' and url.netloc == 'books.google.co.in' and query.get('id') == [ref['book_id']] and query.get('pg') == [ref['page_id']], 'Wrong Google volume/page'
            assert Path(ref['crop_file']).name == approved_ref.get('google_capture', approved_ref.get('screenshot')), 'Wrong target capture'
            evidence(ref['crop_file'], ref['crop_sha256'])
            original = record['original_source']
            if key == (1, 32, 36):
                historical = approved['original_source']
                assert record['historical_original_source'] == historical and historical['bbox_xyxy'] == [270, 320, 3720, 920], 'Frozen wrong-coordinate input changed'
                active = dict(historical)
                active['bbox_xyxy'] = approved['independently_inspected_source_bbox_xyxy']
                active.pop('input_bbox_incorrect_for_target', None)
                assert active['bbox_xyxy'] == [270, 2070, 3720, 2370] and original == active, 'Active source coordinate incorrect'
                assert record['source_coordinate_correction'] == {'prior_bbox_xyxy': historical['bbox_xyxy'], 'active_bbox_xyxy': active['bbox_xyxy'], 'note': approved['source_coordinate_note'], 'historical_artifacts_unchanged': True}, 'Coordinate correction not transparent'
            else:
                assert original == approved['original_source'], 'Original evidence identity altered'
            evidence(original['file'], original['sha256'])
            current = registry[f'kh{key[0]}-ch{key[1]}-v{key[2]}']
            latest = current['latest_source_corroboration']
            assert latest['review_file'] == chapter['review_file'] and latest['review_sha256'] == chapter['review_sha256'] and latest['reference_source'] == ref, 'Registry corroboration pointer differs'
            assert current['google_books_pages'] == [ref['page_id']] and current['google_books_page_url'] == ref['page_url'], 'Registry Google identity differs'
            assert latest['whole_verse_correctness_certified'] is latest['meaning_certified'] is False and latest['new_text_change'] is None, 'Registry scope overstated'
            if key == (1, 32, 36):
                assert latest['original_source'] == original and latest['source_coordinate_correction'] == record['source_coordinate_correction'], 'Registry active coordinate stale'
            if approved.get('orthography_note'):
                assert record.get('orthography_note') == latest.get('orthography_note') == approved['orthography_note'] and record.get('no_orthography_harmonization') is latest.get('no_orthography_harmonization') is True, 'Recorded orthographic distinction hidden or normalized'
            if scope != 'all_applied_spans':
                assert latest['scope'] == scope and latest['additional_source_holds'] == record['additional_source_holds'] and current['hard_hold'], 'Registry edition/partial hold hidden'
                if scope == 'Google_glyph_comparison_hold':
                    assert latest['source_comparison_hold'] == record['source_comparison_hold'], 'Registry glyph hold hidden'
                else:
                    assert latest['source_disagreement'] == record['source_disagreement'], 'Registry edition difference hidden'
            if record['retained_review_issues']:
                assert current['hard_hold'] and current['accepted_translation'] is None and current['current_translation_review']['issues'] == record['retained_review_issues'], 'Meaning hold closed'
    return len(seen)


if __name__ == '__main__':
    print('Existing-span Google comparison checks passed:', validate(Path(__file__).resolve().parent), 'records; partial/different readings retained; no new text accepted.')
