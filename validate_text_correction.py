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

def validate_base_translation_correction(root,old,new,item,review):
    """Replay a reviewed Kannada repair; retain base text and unresolved meaning."""
    import csv,io,re,subprocess
    from pathlib import Path
    fields=('source_pages','type','text');key=tuple(item['key'])
    assert key[0]==1 and review['source_kind']=='reviewed_base_translation','Wrong base translation identity'
    record=next(x for x in review['reviews']if tuple(x['key'])==key)
    assert {k:old[k]for k in fields}==item['old_row']==record['old_row'],'Base translation old row mismatch'
    assert {k:new[k]for k in fields}==item['new_row']==record['new_row'],'Base translation new row mismatch'
    assert old['source_pages']==new['source_pages'] and old['text']!=new['text'],'Base source changed or no-op repair'
    assert item['review_status']==review['review_status']==record['independent_review']['status']=='accepted','Independent base translation review missing'
    commit=review['base_snapshot_commit'];assert re.fullmatch('[0-9a-f]{40}',commit)and item['base_snapshot_commit']==commit and review['base_file']=='translation/narrative.tsv','Unpinned base translation'
    raw=subprocess.check_output(['git','show',commit+':'+review['base_file']],cwd=root);source=[r for r in csv.DictReader(io.StringIO(raw.decode()),delimiter='\t')if(1,int(r['chapter']),int(r['verse']))==key];assert len(source)==1 and all(source[0][f]==old[f]for f in fields),'Immutable base row differs'
    def evidence(name,digest):
        p=(root/name).resolve();assert p.is_relative_to((root/'translation').resolve())and p.is_file(),'Base translation evidence missing'
        assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,'Base translation evidence checksum mismatch'
        return p
    assert json.loads(evidence(item['adjudication_file'],item['adjudication_sha256']).read_text())==review,'Base adjudication differs'
    for f in review['evidence_files']:evidence(f['file'],f['sha256'])
    proposal=json.loads(evidence(review['candidate_file'],review['candidate_sha256']).read_text());p=next(x for x in proposal['items']if tuple(x['key'])==key)
    assert all(x['accepted_sanskrit']is None and x['accepted_kannada']is None for x in proposal['items']),'Worker candidate acceptance promoted'
    assert p['base_sanskrit']==record['source_sanskrit'],'Base Sanskrit changed'
    independent=record['independent_review'];evidence(independent['file'],independent['sha256'])
    ref=record['reference_source'];assert ref['book_id']=='Lh0FEQAAQBAJ'and ref['page_url']=='https://books.google.co.in/books?id='+ref['book_id']+'&pg='+ref['page_id'],'Base reference identity mismatch';evidence(ref['crop_file'],ref['crop_sha256'])
    original=record['additional_original_source'];evidence(original['file'],original['sha256']);assert original['Mac_bytes_archive_identical_and_pixels_checked']and original['dimensions']==[3840,2508],'Original pixels not checked'
    if record['issues']:
        assert new['type']=='translation-review'and 'ಪರಿಶೀಲನೆ'in new['text']and record['accepted_translation']is None and record['review_status']=='accepted_with_unresolved_meaning','Base meaning hold hidden/promoted'
        assert all(x['status']=='open'and x['reading']is None for x in record['issues']),'Unresolved meaning accepted'
        expected=p['optional_explicitly_partial_draft'].replace('[','(ಪರಿಶೀಲನೆ: ').replace(']',')');assert new['text']==expected,'Partial draft changed beyond reviewed proposal'
        assert record['edition_variant']=={'base':'सुविस्तार्य','Google':'सविस्तारं','status':'retained_not_harmonized'},'Edition difference harmonized'
    else:
        assert new['type']=='translation'and record['accepted_translation']==new['text']and record['review_status']=='accepted','Base correction treatment differs'
        assert new['text'].startswith(p['proposed_kannada'])and 'ಇದನ್ನು'in new['text']and 'ನಿರ್ದಿಷ್ಟ ಉಲ್ಲೇಖ'in new['text'],'Demonstrative referent invented or note omitted'
    assert item['rationale'],'Base correction rationale missing'
