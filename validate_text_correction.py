"""Validate append-only reviewed text repairs without changing source evidence."""
import json,hashlib

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
