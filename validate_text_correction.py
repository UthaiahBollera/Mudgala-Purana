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
    base_file=record.get('base_file',review['base_file']);commit=review['base_snapshot_commit'];assert re.fullmatch('[0-9a-f]{40}',commit)and item['base_snapshot_commit']==commit and Path(base_file).parts[0]=='translation' and '..'not in Path(base_file).parts and base_file.endswith('.tsv'),'Unpinned base translation'
    raw=subprocess.check_output(['git','show',commit+':'+base_file],cwd=root);assert raw==subprocess.check_output(['git','show','dcd504671e5ed48c84344c20174bb7c6b28c37f8:'+base_file],cwd=root),'Base TSV differs from immutable reviewed source';source=[r for r in csv.DictReader(io.StringIO(raw.decode()),delimiter='\t')if(1,int(r['chapter']),int(r['verse']))==key];assert len(source)==1 and all(source[0][f]==old[f]for f in fields),'Immutable base row differs'
    def evidence(name,digest):
        p=(root/name).resolve();assert p.is_relative_to((root/'translation').resolve())and p.is_file(),'Base translation evidence missing'
        assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,'Base translation evidence checksum mismatch'
        return p
    assert json.loads(evidence(item['adjudication_file'],item['adjudication_sha256']).read_text())==review,'Base adjudication differs'
    for f in review['evidence_files']:evidence(f['file'],f['sha256'])
    proposal=json.loads(evidence(review['candidate_file'],review['candidate_sha256']).read_text());units=proposal.get('items',proposal.get('records',[dict(proposal,key=proposal.get('scope'))]));p=next(x for x in units if tuple(x['key'])==key)
    assert all(x['accepted_sanskrit']is None and x['accepted_kannada']is None for x in units),'Worker candidate acceptance promoted'
    assert p.get('base_sanskrit',p.get('candidate_sanskrit',p.get('provisional_sanskrit',p.get('source_sanskrit_diplomatic_reading',p.get('source_reading')))))==record['source_sanskrit'],'Base Sanskrit changed'
    independent=record['independent_review'];evidence(independent['file'],independent['sha256'])
    ref=record['reference_source']
    if record.get('correction_mode','').startswith('original_only_'):
        assert all(ref[k] is None for k in ('page_id','page_url','crop_file','crop_sha256'))and p.get('google_books_page_id',p.get('google_page_id'))is None and p.get('google_books_page_url',p.get('google_page_url'))is None,'Unverified Google target invented'
    else:
        assert ref['book_id']=='Lh0FEQAAQBAJ'and ref['page_url']=='https://books.google.co.in/books?id='+ref['book_id']+'&pg='+ref['page_id'],'Base reference identity mismatch';evidence(ref['crop_file'],ref['crop_sha256'])
    original=record['additional_original_source'];evidence(original['file'],original['sha256']);assert original['Mac_bytes_archive_identical_and_pixels_checked']and original['dimensions']==[3840,2508],'Original pixels not checked'
    if record.get('correction_mode')in ('original_only_reviewed_partial','original_only_partial_clauses','original_only_bounded_meaning'):
        assert record['issues'],'Partial meaning hold omitted'
    if record.get('meaning_scope')=='transcription_only_interpretation_unsettled':
        assert record['issues']and record['accepted_translation']is None,'Transcription-only meaning hold closed'
    if record.get('correction_mode')=='original_only_mantra_token':
        replacements=record.get('replacements',[record.get('replacement')]);expected=old['text']
        assert replacements and old['type']==new['type']=='mantra','Mantra treatment changed'
        for replacement in replacements:
            assert replacement and expected.count(replacement['before'])==1,'Declared mantra token absent or repeated'
            expected=expected.replace(replacement['before'],replacement['after'])
        assert expected==new['text']==p['proposed_full_replacement']and record['accepted_transliteration']==new['text']and record['accepted_translation']is None,'Mantra repair exceeds declared source edits'
        if 'minimal_edits'in p:
            assert [x['before']+' → '+x['after']for x in replacements]==p['minimal_edits'],'Mantra edits differ from independent review'
            assert bool(record['issues'])==p['status'].endswith('_with_meaning_hold'),'Independent mantra meaning hold omitted'
        if(p['status'].startswith('transcription_correction_ready_')and p['status'].endswith('_hold'))or p['status']=='transcription_correction_ready_interpretation_not_asserted':
            assert record['issues'],'Independent mantra interpretation hold omitted'
        status='accepted_transliteration_with_meaning_hold'if record['issues']else'accepted'
        assert record['review_status']==status and all(x['status']=='open'and x['reading']is None for x in record['issues']),'Mantra meaning hold closed'
    elif record['issues']:
        assert new['type']=='translation-review'and 'ಪರಿಶೀಲನೆ'in new['text']and record['accepted_translation']is None and record['review_status']=='accepted_with_unresolved_meaning','Base meaning hold hidden/promoted'
        assert all(x['status']=='open'and x['reading']is None for x in record['issues']),'Unresolved meaning accepted'
        if record.get('correction_mode')=='original_only_reviewed_partial':
            expected=p['proposed_partial_text'].replace('[','(ಪರಿಶೀಲನೆ: ').replace(']',')')+record['partial_suffix']
            assert new['text']==expected and p['proposed_full_replacement']is None,'Reviewed partial proposal changed or completed'
            assert not record['partial_suffix']or record['partial_suffix'].startswith(' (ಪರಿಶೀಲನೆ:'),'Partial suffix must be explicit hold'
            assert record['edition_variant']is None,'Unavailable edition variant invented'
        elif record.get('correction_mode')=='original_only_partial_clauses':
            expected=p['proposed_partial_after'].replace('[','(ಪರಿಶೀಲನೆ: ').replace(']',')')
            assert new['text']==expected and p['proposed_full_final_after']is None,'Partial clear-clause proposal changed or completed'
            assert {x['kind']for x in record['issues']}=={'dense_glyph_reading','instrumental_attachment'},'Partial lexical/attachment hold omitted'
            assert record['edition_variant']is None and record['source_reading_status']=='provisional_dense_cluster_unaccepted','Provisional source certified'
        elif record.get('correction_mode')=='original_only_bounded_meaning':
            assert record['display_note'].startswith(' (ಪರಿಶೀಲನೆ:')and 'ಉಲ್ಲೇಖ ಯಾರಿಗೆ' in record['display_note']and new['text']==p['proposed_after']+record['display_note'],'Antecedent hold omitted or proposal changed'
            assert 'ಅವನ ಐಶ್ವರ್ಯ' in new['text']and 'ನಿನ್ನ ಐಶ್ವರ್ಯ'not in new['text']and 'ಕಳೆಯುವ'not in new['text'],'Unsupported possession/removal restored'
            assert record['edition_variant']is None,'Unavailable edition difference invented'
        else:
            expected=p['optional_explicitly_partial_draft'].replace('[','(ಪರಿಶೀಲನೆ: ').replace(']',')');assert new['text']==expected,'Partial draft changed beyond reviewed proposal'
            assert record['edition_variant']=={'base':'सुविस्तार्य','Google':'सविस्तारं','status':'retained_not_harmonized'},'Edition difference harmonized'
    elif record.get('correction_mode')=='original_only_full_translation':
        assert not record['issues']and new['type']=='translation'and record['accepted_translation']==new['text']==p['proposed_full_replacement']and record['review_status']=='accepted','Full original-only correction differs from independent proposal'
        assert record['edition_variant']is None,'Unavailable edition variant invented'
    else:
        assert new['type']=='translation'and record['accepted_translation']==new['text']and record['review_status']=='accepted','Base correction treatment differs'
        assert new['text'].startswith(p['proposed_kannada'])and 'ಇದನ್ನು'in new['text']and 'ನಿರ್ದಿಷ್ಟ ಉಲ್ಲೇಖ'in new['text'],'Demonstrative referent invented or note omitted'
    assert item['rationale'],'Base correction rationale missing'


def validate_no_change_base_adjudications(root,review,replayed,batch):
    """No-change decisions must never enter a replacement TSV or close holds."""
    records=review.get('no_change_adjudications',[])
    assert [x['key']for x in records]==batch.get('no_change_keys',[]),'Unlisted no-change review'
    for x in records:
        key=tuple(x['key']);old={k:replayed[key][k]for k in ('source_pages','type','text')}
        assert old==x['old_row']==x['new_row'],'No-change text altered'
        assert key not in {tuple(y['key'])for y in batch['text_corrections']},'No-change verse inserted as correction'
        assert x['review_status']=='reviewed_no_text_change_hold'and x['accepted_translation']is None and x['issues']and all(i['status']=='open'and i['reading']is None for i in x['issues']),'No-change hold closed'
        candidate=json.loads((root/review['candidate_file']).read_text());unit=next(p for p in candidate['records']if tuple(p['key'])==key)
        assert unit['before']==old['text']and unit['proposed_full_replacement']is None and unit.get('proposed_partial_text')is None,'No-change differs from independent proposal'
        if unit['status']in {'no_change_source_reading_confirmed','no_change_number_preserved_comparison_hold','no_change_printed_svam_contextual_kham_hold','no_change_compressed_meaning_hold'}:
            assert x['counted_as_new_correction']is False and x['accepted_transliteration']is None and x['source_sanskrit']==unit['source_reading'],'No-change evidence promoted or source altered'
            assert x['reference_source']['page_id']is None and x['reference_source']['page_url']is None,'Unknown no-change Google location invented'
            if unit['status']=='no_change_printed_svam_contextual_kham_hold':
                assert x['printed_disputed_token']=='तस्मात्स्वं'and x['source_emendation_accepted']is False and x['sky_is_contextual_interpretation_not_diplomatic_reading']is True and x['current_wording_source_verified']is False,'Printed svam falsely certified as kham'
            if unit['status']=='no_change_number_preserved_comparison_hold':
                assert x['printed_earth_extent']=='fifty crore'and x['comparison_10_2_extent']=='five crore yojanas'and x['comparison_10_2_referent']=='Virat body'and x['same_referent_assumed']is False and x['yojana_unit_printed_in_9_38']is False and x['numerals_harmonized']is False,'Source measurements harmonized or referents/units invented'
            if unit['status']=='no_change_compressed_meaning_hold':
                assert x['current_wording_source_verified']is False,'Compressed meaning falsely certified'
        if unit['status']=='unchanged_source_confirmed':
            assert x['target_readings_source_verified']is True and x['counted_as_new_correction']is False and x['accepted_transliteration']is None and x['source_sanskrit']==unit['source_reading'],'Unchanged source confirmation promoted or source altered'
            assert x['reference_source']['page_id']is None and x['reference_source']['page_url']is None,'Unknown confirmed-source Google page invented'
            if 'printed_sequence'in x:
                assert x['printed_numeral']==x['logical_numeral']==33 and x['printed_sequence']==[31,32,33,34,35]and x['historical_duplicate32_not_this_original']is True,'Printed/logical numeral confirmation altered'
        if unit['status']=='no_change_current_target_readings_confirmed':
            assert x['target_readings_source_verified']is True and x['counted_as_new_correction']is False and x['accepted_transliteration']is None,'Confirmed no-change target promoted to new correction'
            assert x['source_sanskrit']==unit['source_reading']and x['reference_source']['page_id']is None and x['reference_source']['page_url']is None,'No-change source or unknown Google field altered'
        if unit['status']=='retained_reading_and_meaning_hold_no_accepted_change':
            assert x['current_wording_source_verified']is False and x['accepted_transliteration']is None,'Unresolved unchanged wording certified'
