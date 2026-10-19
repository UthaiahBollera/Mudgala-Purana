"""Validate append-only reviewed text repairs without changing source evidence."""
import json,hashlib

def validate_base_text_correction(root, old, new, item, review):
    """Replay a token-only repair while preserving the immutable base edition."""
    import csv, io, subprocess
    from pathlib import Path
    fields = ('source_pages', 'type', 'text')
    assert {k: old[k] for k in fields} == item['old_row'] == review['old_row'], 'Base repair old row mismatch'
    assert {k: new[k] for k in fields} == item['new_row'] == review['new_row'], 'Base repair new row mismatch'
    assert old['source_pages'] == new['source_pages'] and old['type'] == new['type'], 'Base repair changed source mapping or treatment'
    assert item['review_status'] == review['review_status'] == review['independent_review']['status'] == 'accepted', 'Unreviewed base repair'
    key = tuple(item['key'])
    assert list(key) == review['key'] and key[0] == 1, 'Base repair identity mismatch'
    assert review['base_snapshot_commit'] == 'dcd504671e5ed48c84344c20174bb7c6b28c37f8' and review['base_file'] == 'translation/narrative.tsv', 'Unpinned base repair'
    raw = subprocess.check_output(['git', 'show', review['base_snapshot_commit']+':'+review['base_file']], cwd=root)
    matches = [r for r in csv.DictReader(io.StringIO(raw.decode()), delimiter='\t') if (1, int(r['chapter']), int(r['verse'])) == key]
    assert len(matches) == 1 and all(matches[0][f] == old[f] for f in fields), 'Base repair differs from immutable row'
    replacement = item['replacement']
    assert replacement == review['replacement'] and replacement['before'] != replacement['after'], 'Invalid base replacement'
    assert old['text'].count(replacement['before']) == 1 and new['text'] == old['text'].replace(replacement['before'], replacement['after']), 'Base repair exceeds one declared token'
    path = (root/item['adjudication_file']).resolve()
    assert path.is_relative_to((root/'translation').resolve()) and path.is_file(), 'Base repair evidence missing'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['adjudication_sha256'], 'Base repair evidence hash mismatch'
    assert json.loads(path.read_text()) == review, 'Base repair evidence differs'
    ref = review['reference_source']
    crop = (root/ref['crop_file']).resolve()
    assert crop.is_relative_to((root/'translation').resolve()) and crop.is_file(), 'Base repair crop missing'
    assert hashlib.sha256(crop.read_bytes()).hexdigest() == ref['crop_sha256'], 'Base repair crop hash mismatch'
    assert ref['book_id'] == 'Lh0FEQAAQBAJ' and ref['page_url'] == 'https://books.google.co.in/books?id='+ref['book_id']+'&pg='+ref['page_id'], 'Base repair reference identity mismatch'
    assert review['edition_policy']['no_silent_edition_harmonization'] and review['edition_policy']['retain_base_cha'], 'Base edition policy missing'
    assert item['rationale'], 'Base repair rationale missing'

def validate_text_correction(root, old, new, item, prior_batches):
    fields=('source_pages','type','text')
    assert {k:old[k]for k in fields}==item['old_row'], 'Correction old row mismatch'
    assert {k:new[k]for k in fields}==item['new_row'], 'Correction new row mismatch'
    assert old['source_pages']==new['source_pages'], 'Text correction changed source mapping'
    assert old['text']!=new['text'] and item['review_status']=='accepted', 'Unreviewed/no-op text correction'
    key=tuple(item['key']);prior=[]
    for batch in prior_batches:
        review=json.loads((root/batch['review_file']).read_text())
        prior.extend(x for x in review.get('verses',[])if tuple(x['key'])==key)
    assert prior and prior[-1]['source_sanskrit']==item['source_sanskrit'], 'Text correction changed Sanskrit'
    assert prior[-1]['source_parts']==item['source_parts'], 'Text correction changed source parts'
    path=(root/item['adjudication_file']).resolve()
    assert path.is_relative_to((root/'translation').resolve()) and path.is_file(), 'Correction evidence missing'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==item['adjudication_sha256'], 'Correction evidence hash mismatch'
    evidence=json.loads(path.read_text());record=next(x for x in evidence['reviews']if tuple(x['key'])==key)
    assert record['source_sanskrit']==item['source_sanskrit'] and record['source_evidence']==item['source_parts'], 'Correction addendum source mismatch'
    assert record['reviewed_kannada_candidate']==item['accepted_translation'], 'Correction candidate mismatch'
    assert item['accepted_translation'] in new['text'] and item['rationale'], 'Correction candidate/rationale absent'
