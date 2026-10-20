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
    if review.get('review_mode')=='independent_google_eight_target_adjudication':
        return validate_google_minimal_correction(root,old,new,item,review)
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
        if 'printed_target_form' in record:
            assert record['printed_target_form'] in record['source_sanskrit'] and record['unusual_form_not_grammatically_normalized'] is True,'Unusual printed form normalized'
            if key== (1,21,41):assert record['printed_target_form']=='सुधात्रे' and record['avagraha_convention_preserved'] is True,'Sudhatre or preserved avagraha altered'
            if key== (1,21,45):assert record['printed_target_form']=='तेषामपारप्रधात्रे' and record['sandhi_and_negation_preserved'] is True,'Aparapradhatre, sandhi or negation altered'
        if 'replacements'in p:
            assert replacements==p['replacements'],'Declared spans differ from independent proposal'
        if 'minimal_edits'in p:
            assert [x['before']+' → '+x['after']for x in replacements]==p['minimal_edits'],'Mantra edits differ from independent review'
            assert bool(record['issues'])==p['status'].endswith('_with_meaning_hold'),'Independent mantra meaning hold omitted'
        if(p['status'].startswith('transcription_correction_ready_')and p['status'].endswith('_hold'))or p['status']=='transcription_correction_ready_interpretation_not_asserted':
            assert record['issues'],'Independent mantra interpretation hold omitted'
        if p['status']=='correction_ready_transcription_with_grammar_hold':
            assert key==(1,46,35) and record['issues'] and record['printed_target_form']=='अभक्तविघ्नादात्रे' and record['unusual_form_not_grammatically_normalized'] is True,'Printed extra aa or grammar hold omitted'
            assert record['source_normalization_accepted'] is False and record['negated_giver_interpretation_accepted'] is False,'Problematic printed form silently normalized or interpreted'
        if p['status']=='correction_ready_printed_name':
            assert key==(1,46,41) and record['issues'] and record['printed_name']=='शुक्र' and record['name_scope']=='target_edition_transcription_only','Printed rakara or name scope omitted'
            assert record['authorial_intent_established'] is False and record['cross_edition_unanimity_claimed'] is False and record['uninspected_edition_variant_accepted'] is False,'Printed name promoted to authorial or cross-edition certainty'
        status='accepted_transliteration_with_meaning_hold'if record['issues']else'accepted'
        assert record['review_status']==status and all(x['status']=='open'and x['reading']is None for x in record['issues']),'Mantra meaning hold closed'
    elif record['issues']:
        assert new['type']=='translation-review'and 'ಪರಿಶೀಲನೆ'in new['text']and record['accepted_translation']is None and record['review_status']=='accepted_with_unresolved_meaning','Base meaning hold hidden/promoted'
        assert all(x['status']=='open'and x['reading']is None for x in record['issues']),'Unresolved meaning accepted'
        if record.get('correction_mode')=='original_only_reviewed_full_with_hold':
            assert p['status']=='correction_ready_with_name_identity_hold' and record['printed_name']=='विजयप्रियम्' and record['cross_narrative_identity_settled'] is False and record['uninspected_edition_variant_accepted'] is False,'Printed name or identity hold altered'
            expected=old['text']
            for change in p['replacements']:
                assert expected.count(change['before'])==1,'Reviewed name span absent or repeated'
                expected=expected.replace(change['before'],change['after'])
            assert expected==p['proposed_full_replacement'] and record['replacements']==p['replacements'],'Name restoration exceeds independent proposal'
            marker=old['text'][old['text'].rfind(' ॥'):];note=record['display_note']
            assert note.startswith(' (ಪರಿಶೀಲನೆ:') and new['text']==expected.replace(marker,note+marker) and record['edition_variant'] is None,'Visible identity hold omitted or unsupported edition invented'
        elif record.get('correction_mode')=='original_only_reviewed_full_with_nuance_hold':
            assert key==(1,37,5) and p['status']=='correction_ready_with_meaning_nuance_hold','Wrong nuance-held full replacement'
            expected=old['text']
            for change in p['replacements']:
                assert expected.count(change['before'])==1,'Reviewed nuance span absent or repeated'
                expected=expected.replace(change['before'],change['after'])
            assert expected==p['proposed_full_replacement'] and record['replacements']==p['replacements'],'Nuance replacement exceeds independent proposal'
            marker=old['text'][old['text'].rfind(' ॥'):];note=record['display_note']
            assert note.startswith(' (ಪರಿಶೀಲನೆ:') and new['text']==expected.replace(marker,note+marker) and record['edition_variant'] is None,'Visible nuance hold omitted or edition invented'
            assert record['printed_abhaya_cluster']=='मेऽभयप्राप्तिः' and record['printed_abhaya_cluster'] in record['source_sanskrit'] and record['meaning_nuance_settled'] is False and record['westward_sunrise_is_interpretation'] is True,'Abhaya or sunrise interpretation falsely settled'
            assert record['slain_daityas_not_in_verse5'] is True and record['following_verse6_unchanged'] is True and 'ಮೃತಾ ದೈತ್ಯಾ' not in new['text'],'Adjacent slain-daityas wording misplaced'
            assert record['uninspected_edition_variant_accepted'] is False,'Uninspected edition variant accepted'
        elif record.get('correction_mode')=='original_only_reviewed_partial_edits':
            assert key==(1,39,32) and p['status']=='partial_correction_second_half_hold' and p['proposed_full_replacement'] is None,'Partial edits promoted to full translation'
            expected=old['text']
            for change in p['replacements']:
                assert expected.count(change['before'])==1,'Reviewed partial span absent or repeated'
                expected=expected.replace(change['before'],change['after'])
            assert expected==p['proposed_text_after_partial_edits'] and record['replacements']==p['replacements'],'Partial edits exceed independent proposal'
            marker=old['text'][old['text'].rfind(' ॥'):];note=record['display_note']
            assert note.startswith(' (ಪರಿಶೀಲನೆ:') and new['text']==expected.replace(marker,note+marker) and record['edition_variant'] is None,'Visible second-half hold omitted or edition invented'
            assert record['whole_target_resolved'] is False and record['remaining_second_half_syntax_settled'] is False and record['retained_second_half_paraphrase_certified'] is False,'Unresolved second half falsely certified'
            assert record['printed_numeral']==21 and record['unsupported_yogi_removed'] is True and 'ಮುನಿಯೋಗಿಗಳೇ' not in new['text'],'Numeral or unsupported yogi altered'
        elif record.get('correction_mode')=='original_only_reviewed_sentence_replacement':
            assert p['status']=='partial_source_term_correction_meaning_hold' and p['proposed_full_replacement'] is None,'Partial source-term repair promoted to complete translation'
            assert record['replace_from']==p['replace_from'] and record['replacement_sentence']==p['proposed_partial_text'] and old['text'].count(p['replace_from'])==1,'Source-term repair differs from reviewed sentence'
            marker=old['text'][old['text'].rfind(' ॥'):];note=record['display_note']
            assert note.startswith(' (ಪರಿಶೀಲನೆ:') and record['whole_target_resolved'] is False and record['edition_variant'] is None,'Partial source-term hold omitted or resolved'
            assert new['text']==old['text'].replace(p['replace_from'],p['proposed_partial_text']).replace(marker,note+marker),'Unrelated sentence or verse marker changed'
        elif record.get('correction_mode')=='original_only_reviewed_partial':
            expected=p['proposed_partial_text'].replace('[','(ಪರಿಶೀಲನೆ: ').replace(']',')')+record['partial_suffix']
            assert new['text']==expected and p['proposed_full_replacement']is None,'Reviewed partial proposal changed or completed'
            assert not record['partial_suffix']or record['partial_suffix'].startswith(' (ಪರಿಶೀಲನೆ:'),'Partial suffix must be explicit hold'
            assert record['edition_variant']is None,'Unavailable edition variant invented'
            if p['status']=='partial_first_clause_only':
                assert record['printed_disputed_token']=='नारकाः' and record['source_emendation_accepted'] is False and record['remaining_sentence_accepted'] is False,'Printed naraka emended or unresolved remainder certified'
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
        if key==(1,32,15):
            assert record['following_verse_16_unchanged'] is True and record['abhaya_belongs_to_16'] is True and record['continuous_description_does_not_deny_abhaya'] is True,'Adjacent abhaya boundary misrepresented'
            assert 'ಅಭಯ' not in new['text'] and 'ಅಭಯ' in record['following_verse_16_row']['text'],'Abhaya duplicated in15 or omitted from16 context'
    else:
        assert new['type']=='translation'and record['accepted_translation']==new['text']and record['review_status']=='accepted','Base correction treatment differs'
        assert new['text'].startswith(p['proposed_kannada'])and 'ಇದನ್ನು'in new['text']and 'ನಿರ್ದಿಷ್ಟ ಉಲ್ಲೇಖ'in new['text'],'Demonstrative referent invented or note omitted'
    assert item['rationale'],'Base correction rationale missing'


def validate_no_change_base_adjudications(root,review,replayed,batch):
    """No-change decisions must never enter a replacement TSV or close holds."""
    if review.get('review_mode')=='independent_google_eight_target_adjudication':
        return validate_google_retained_holds(root,review,replayed,batch)
    records=review.get('no_change_adjudications',[])
    assert [x['key']for x in records]==batch.get('no_change_keys',[]),'Unlisted no-change review'
    if records:
        for f in review['evidence_files']:
            path=(root/f['file']).resolve()
            assert path.is_relative_to((root/'translation').resolve()) and path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==f['sha256'],'No-change source evidence checksum mismatch'
        cp=root/review['candidate_file'];assert hashlib.sha256(cp.read_bytes()).hexdigest()==review['candidate_sha256'],'No-change candidate checksum mismatch'
        candidate=json.loads(cp.read_text());assert all(p['accepted_sanskrit'] is None and p['accepted_kannada'] is None for p in candidate['records']),'No-change raw candidate accepted'

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
        if unit['status'] in {'unchanged_segmentation_hold','unchanged_number_mismatch_preserved'}:
            assert x['counted_as_new_correction'] is False and x['accepted_transliteration'] is None and x['current_wording_source_verified'] is False,'Unsettled no-change meaning certified'
            assert x['source_sanskrit']==unit['source_reading'] and x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Source or unknown Google location altered'
            if unit['status']=='unchanged_segmentation_hold':
                assert x['printed_continuous_compound']=='ईश्वराज्ञानभाविताः' and x['word_boundary_printed'] is False and x['alternative_segmentation_settled'] is False,'Continuous-source segmentation falsely settled'
            else:
                assert x['printed_dual_speakers'] is True and x['printed_singular_possessive']=='मे' and x['ownership_rendering_neutral'] is True,'Source speaker number or neutral ownership altered'
        if unit['status'] in {'unchanged_printed_grammar_meaning_hold','unchanged_context_supported_sandhi'}:
            assert x['counted_as_new_correction'] is False and x['accepted_transliteration'] is None and x['current_wording_source_verified'] is False,'Unchanged interpretation promoted'
            assert x['source_sanskrit']==unit['source_reading'] and x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Source or unknown Google reference altered'
            if unit['status']=='unchanged_printed_grammar_meaning_hold':
                assert x['printed_ending']=='लक्ष्य उन्मनसा भवेः' and x['grammar_normalized'] is False,'Irregular printed grammar normalized'
            else:
                assert x['printed_continuous_token']=='नयाम्यहम्' and x['contextual_negative_sandhi_supported'] is True and x['separate_negative_word_printed'] is False and x['source_emendation_accepted'] is False,'Negative sandhi or printed spacing misrepresented'
        if unit['status'] in {'unchanged_lexical_hold','unchanged_name_source_discrepancy_hold','unchanged_segmentation_doctrinal_hold'}:
            assert x['counted_as_new_correction'] is False and x['accepted_transliteration'] is None and x['current_wording_source_verified'] is False,'Unsettled unchanged interpretation certified'
            assert x['source_sanskrit']==unit['source_reading'] and x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Source or unknown Google location altered'
            if unit['status']=='unchanged_lexical_hold':
                assert x['printed_disputed_noun']=='वत्साः' and x['dwelling_is_contextual_not_diplomatic'] is True,'Contextual dwelling falsely scan-certified'
            elif unit['status']=='unchanged_name_source_discrepancy_hold':
                assert x['printed_name']=='लोमासुर' and x['retained_Kannada_name']=='ಲೋಭಾಸುರ' and x['retained_name_is_editorial_not_scan_confirmed'] is True and x['independent_narrative_name_scan_checked'] is False,'Name discrepancy or unseen evidence misrepresented'
            else:
                assert x['printed_continuous_junction']=='शक्तिब्रह्माखुगः सद्यत्तस्य' and x['segmentation_settled'] is False and x['absent_a_inserted'] is False,'Compressed source harmonized or settled'
        if unit['status'] in {'unchanged_source_confirmed_meaning_hold','unchanged_base_reading_preserved'}:
            assert x['counted_as_new_correction'] is False and x['target_readings_source_verified'] is True and x['accepted_transliteration'] is None,'Unchanged source confirmation promoted'
            assert x['source_sanskrit']==unit['source_reading'] and x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Source or unknown Google page altered'
            if unit['status']=='unchanged_source_confirmed_meaning_hold':
                assert x['numerical_compound_expansion_accepted'] is False and x['current_wording_source_verified'] is False,'Difficult compound interpretation certified'
            else:
                assert x['printed_base_token']=='धात्रे' and x['historical_comparison_token']=='धाम्ने' and x['named_edition_variant_established'] is False,'Base dhatre harmonized or uninspected edition invented'
        if unit['status'] in {'unchanged_source_supported_meaning_hold','unchanged_source_supported_segmentation_hold'}:
            assert x['counted_as_new_correction'] is False and x['target_readings_source_verified'] is True and x['accepted_transliteration'] is None and x['current_wording_source_verified'] is False,'Unchanged transcription promoted to settled meaning'
            assert x['source_sanskrit']==unit['source_reading'] and x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Source or unknown Google location altered'
            if unit['status']=='unchanged_source_supported_meaning_hold':
                assert x['compound_paraphrase_accepted'] is False,'Compressed compound paraphrase accepted'
            else:
                assert x['printed_negation_cluster']=='न पुंस्त्री' and x['segmentation_settled'] is False and x['editorial_avagraha_claimed_printed'] is False,'Negation segmentation or editorial avagraha falsely certified'
        if unit['status'] in {'unchanged_source_supported','unchanged_meaning_hold_known_omission'}:
            assert x['counted_as_new_correction'] is False and x['accepted_transliteration'] is None and x['source_sanskrit']==unit['source_reading'],'Unchanged target promoted or source altered'
            assert x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Unknown Google location invented'
            if unit['status']=='unchanged_source_supported':
                assert x['target_readings_source_verified'] is True,'Source-supported target confirmation lost'
                if key==(1,23,48):
                    assert x['duration_in_23_48'] is False and x['printed_23_43_duration']=='दिव्यवर्षसहस्रं' and x['duration_23_43_divine_years']==1000 and x['input_packet_ten_year_suggestion_rejected'] is True and x['count_text_unchanged'] is True,'Duration moved or erroneous inventory count adopted'
            else:
                assert x['current_wording_source_verified'] is False and x['unrendered_source_tokens']==['बाधादं'] and x['known_omission_retained_as_hold'] is True and x['source_emendation_accepted'] is False,'Known omission or compressed syntax falsely resolved'
        if unit['status'] in {'unchanged_idiom_meaning_hold','unchanged_lexical_meaning_hold','unchanged_junction_meaning_hold','unchanged_source_supported_narrative_hold','unchanged_sword_supported_action_hold'}:
            assert x['counted_as_new_correction'] is False and x['current_wording_source_verified'] is False and x['accepted_transliteration'] is None and x['target_readings_source_verified'] is True and x['source_emendation_accepted'] is False,'Evidence-only hold promoted to correction or settled meaning'
            assert x['source_sanskrit']==unit['source_reading'] and x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Source or unknown Google location altered'
            if unit['status']=='unchanged_idiom_meaning_hold':assert x['printed_idiom']=='कालानां कलनात्मकैः' and x['trembling_is_contextual_gloss'] is True,'Idiom falsely resolved'
            elif unit['status']=='unchanged_lexical_meaning_hold':
                if key==(1,25,27):assert x['printed_lexical_cluster']=='कुंतलाद्यस्त्रकैः' and x['la_preserved'] is True and x['precise_weapon_list_accepted'] is False,'Printed la normalized or weapon list invented'
                elif key==(1,31,29):assert x['printed_lexical_cluster']=='द्वंद्वकारकः' and x['freedom_from_duality_substituted'] is False,'Childlike duality/conflict meaning harmonized'
                else:assert key==(1,45,33) and x['printed_lexical_cluster']=='हीनस्वभावतः' and x['humility_gloss_is_contextual'] is True and x['lexical_meaning_settled'] is False,'Contextual humility gloss falsely certified'
            elif unit['status']=='unchanged_junction_meaning_hold':assert x['printed_junction']=='रथाश्वालंकृतास्तत्र' and x['shva_not_emended_to_shcha'] is True and x['horses_added'] is False,'Shva junction silently normalized or interpreted'
            elif unit['status']=='unchanged_source_supported_narrative_hold':assert x['printed_narrative_clause']=='नराणां हृद्यताडयत्' and x['men_not_replaced_with_diseases'] is True,'Narrative logic silently repaired'
            else:assert x['printed_weapon']=='खड्गेनैरावतं' and x['printed_action']=='पदाग्रहीत्' and x['Airavata_unconscious_source_supported'] is True and x['Indra_unconsciousness_claimed'] is False and x['precise_foot_action_settled'] is False,'Sword or elephant/Indra action falsely resolved'
        if unit['status'] in {'unchanged_source_anomaly_meaning_hold','unchanged_name_compound_hold'}:
            assert x['counted_as_new_correction'] is False and x['current_wording_source_verified'] is False and x['accepted_transliteration'] is None and x['target_readings_source_verified'] is True,'Unchanged anomaly/meaning hold promoted'
            assert x['source_sanskrit']==unit['source_reading'] and x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Source anomaly or unknown Google location altered'
            if unit['status']=='unchanged_source_anomaly_meaning_hold':assert x['printed_anomalous_token']=='निर्विकपल्कम्' and x['retained_Kannada_normalization']=='ನಿರ್ವಿಕಲ್ಪ' and x['normalization_not_literal_print'] is True and x['source_anomaly_resolved'] is False,'Editorial nirvikalpa normalized into literal source claim'
            else:assert x['printed_continuous_name_cluster']=='पुष्पदंतमहाकालरवाः' and x['additional_Rava_name_established'] is False and x['compound_meaning_settled'] is False,'Unsettled Rava name/compound certified'
        if unit['status'] in {'unchanged_source_label_hold','unchanged_lexical_nuance_hold','unchanged_syntax_hold_known_unsupported_clause','unchanged_temporal_meaning_hold'}:
            assert x['counted_as_new_correction'] is False and x['accepted_transliteration'] is None and x['current_wording_source_verified'] is False and x['target_readings_source_verified'] is True and x['source_sanskrit']==unit['source_reading'],'Unchanged evidence/meaning hold promoted'
            assert x['source_emendation_accepted'] is False and x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Source emendation or Google location invented'
            if key==(1,34,25):assert x['printed_label']=='सुराः' and x['source_label_harmonized'] is False and x['unrendered_source_tokens']==['सुराः'] and x['narrative_label_discrepancy_resolved'] is False,'Printed label harmonized or omission hidden'
            elif key==(1,34,42):assert x['printed_lexical_token']=='प्रबोध्य' and x['combat_nuance_settled'] is False,'Combat nuance falsely settled'
            elif key==(1,35,1):assert x['printed_syntax_cluster']=='कर्म चैव यथासुरम्' and x['known_unsupported_Kannada_clause']=='ಕರ್ಮದ ಗತಿಯೂ ಹಾಗೆಯೇ ಇದೆ.' and x['unsupported_clause_certified'] is False and x['syntax_settled'] is False,'Known unsupported karma clause falsely certified'
            else:assert key==(1,36,13) and x['printed_temporal_cluster']=='अधुना स गतः कालो विपरीतेन कर्मणा' and x['temporal_reference_and_agency_settled'] is False,'Temporal/agency meaning falsely settled'
        if unit['status'] in {'unchanged_grammatical_relationship_hold','unchanged_first_half_syntax_hold','unchanged_transcription_confirmed'}:
            assert x['counted_as_new_correction'] is False and x['accepted_transliteration'] is None and x['current_wording_source_verified'] is False and x['target_readings_source_verified'] is True and x['source_sanskrit']==unit['source_reading'],'No-change transcription evidence promoted to meaning acceptance'
            assert x['source_emendation_accepted'] is False and x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Unverified source emendation or Google target invented'
            if key==(1,37,39):assert x['printed_instrumentals']=='अष्टावरणैर्देहधारिभिः' and x['instrumental_coordination_certified'] is False and x['weapons_reading_accepted'] is False,'Instrumental relationship falsely certified'
            elif key==(1,38,34):assert x['printed_first_half_cluster']=='न समं चात्मना न च' and x['atmana_nominalization_certified'] is False and x['first_half_syntax_settled'] is False,'Atmana nominalization falsely certified'
            else:assert key==(1,39,7) and x['printed_organ_token']=='घ्राण' and x['printed_form_token']=='स्वरूप' and x['compound_segmentation_and_philosophical_meananing_certified'] is False,'Organ transcription confirmation promoted to philosophical certainty'
        if unit['status']=='unchanged_printed_grammar_hold':
            assert key==(1,41,29) and x['counted_as_new_correction'] is False and x['accepted_transliteration'] is None and x['current_wording_source_verified'] is False and x['target_readings_source_verified'] is True and x['source_sanskrit']==unit['source_reading'],'Printed grammar hold promoted'
            assert x['printed_grammar_cluster']=='प्रभावान् मे' and x['conjectural_ablative_accepted'] is False and x['unrendered_source_tokens']==['प्रभावान् मे'] and x['irregular_phrase_meaning_settled'] is False,'Printed final na emended or omitted phrase certified'
            assert x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Unknown Google location invented'
        if unit['status'] in {'unchanged_coordination_hold','unchanged_number_anomaly_hold'}:
            assert x['counted_as_new_correction'] is False and x['accepted_transliteration'] is None and x['current_wording_source_verified'] is False and x['target_readings_source_verified'] is True and x['source_sanskrit']==unit['source_reading'],'Unchanged coordination/number hold promoted'
            assert x['source_emendation_accepted'] is False and x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Unverified source emendation or Google location invented'
            if key==(1,43,16):assert x['printed_coordination_cluster']=='ताभ्यां सह' and x['participant_coordination_settled'] is False and x['co_participants_not_silently_reassigned'] is True,'Praise participants silently reassigned'
            else:assert key==(1,44,25) and x['printed_dual_token']=='पुत्रौ' and x['printed_singular_verb']=='हरति' and x['source_number_emended'] is False and x['singular_Kannada_is_contextual'] is True and x['literal_number_match_certified'] is False,'Printed number anomaly silently normalized or contextual reading certified as literal'
        if unit['status']=='unchanged_syntax_meaning_hold':
            assert x['counted_as_new_correction'] is False and x['accepted_transliteration'] is None and x['current_wording_source_verified'] is False and x['source_sanskrit']==unit['source_reading'],'Unchanged syntax hold promoted'
            assert x['printed_syntax_cluster']=='न भिन्नौ मयि तिष्ठतः' and x['negation_dual_and_first_person_locative_preserved'] is True and x['syntax_settled'] is False,'Dual/locative syntax altered or settled'
            assert x['reference_source']['page_id'] is None and x['reference_source']['page_url'] is None,'Unknown Google location invented'
        if key==(1,30,12):assert x['deva_sura_labels_harmonized'] is False and x['dust_confusion_context_preserved'] is True,'Supported gods-striking-gods context harmonized'
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


def _google_evidence(root,review):
    """Validate actual captured identities without constructing absent Google URLs."""
    from urllib.parse import urlparse,parse_qs
    def evidence(name,digest):
        p=(root/name).resolve()
        assert p.is_relative_to((root/'translation').resolve()) and p.is_file(),'Google review evidence missing'
        assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,'Google review evidence checksum mismatch'
        return p
    for x in review['evidence_files']:evidence(x['file'],x['sha256'])
    adjudication=json.loads(evidence(review['independent_adjudication_file'],review['independent_adjudication_sha256']).read_text())
    assert adjudication['accepted_changes']==3 and len(adjudication['records'])==8,'Google review scope changed'
    candidates=json.loads(evidence(review['candidate_file'],review['candidate_sha256']).read_text())['records']
    assert len(candidates)==8 and all(x['accepted_sanskrit'] is None and x['accepted_kannada'] is None and x['proposed_full_replacement'] is None and x['publication_ready'] is False for x in candidates),'Raw candidate acceptance promoted'
    scope=review.get('chapter_scope')
    accepted={(1,46,46),(1,47,24),(1,47,47)};held={(1,21,41),(1,21,45),(1,46,35),(1,46,51),(1,47,29)}
    assert scope is None or scope in (21,46,47),'Invalid chapter scope'
    assert {tuple(x['key'])for x in review['reviews']}=={k for k in accepted if scope is None or k[1]==scope},'Unexpected Google correction key'
    assert {tuple(x['key'])for x in review['no_change_adjudications']}=={k for k in held if scope is None or k[1]==scope},'Google retained holds omitted'
    for x in review['reviews']+review['no_change_adjudications']:
        key='.'.join(map(str,x['key']));a=next(z for z in adjudication['records']if z['key']==key);ref=x['reference_source']
        assert ref['book_id']=='Lh0FEQAAQBAJ' and ref['page_id']==a['google_page_id'] and ref['page_url']==a['google_captured_url'],'Observed Google identity changed or unknown URL invented'
        if ref['page_url'] is not None:
            u=urlparse(ref['page_url']);q=parse_qs(u.query)
            assert u.scheme=='https' and u.netloc=='books.google.co.in' and q.get('id')==[ref['book_id']] and q.get('pg')==[ref['page_id']],'Wrong captured volume/page URL'
        evidence(ref['crop_file'],ref['crop_sha256']);original=x['additional_original_source'];evidence(original['file'],original['sha256'])
        assert original['Mac_bytes_archive_identical_and_pixels_checked'] is True and original['dimensions']==[3840,2508],'Original verification missing'
        assert x['whole_verse_correctness_certified'] is False and x['meaning_certified'] is False and x['no_silent_edition_harmonization'] is True,'Bounded evidence promoted to whole mantra certainty'
        evidence(x['independent_review']['file'],x['independent_review']['sha256'])
    return adjudication


def validate_google_minimal_correction(root,old,new,item,review):
    import csv,io,re,subprocess
    from pathlib import Path
    a=_google_evidence(root,review);key=tuple(item['key']);x=next(z for z in review['reviews']if tuple(z['key'])==key)
    unit=next(z for z in a['records']if z['key']=='.'.join(map(str,key)))
    fields=('source_pages','type','text')
    assert {f:old[f]for f in fields}==item['old_row']==x['old_row'],'Google minimal old row differs'
    assert {f:new[f]for f in fields}==item['new_row']==x['new_row'],'Google minimal new row differs'
    assert old['source_pages']==new['source_pages'] and old['type']==new['type']=='mantra','Google minimal mapping/treatment changed'
    assert item['review_status']==review['review_status']==x['review_status']==x['independent_review']['status']=='accepted','Google independent approval missing'
    assert x['correction_mode']=='google_corroborated_minimal_mantra_span' and x['replacements']==[unit['accepted_replacement_span']],'Google minimal span differs from adjudication'
    expected_spans={(1,46,46):{'before':'ಕುಲಂ ಧನ್ಯಂ','after':'ಸ್ಥಲಂ ಧನ್ಯಂ'},(1,47,24):{'before':'ಜನದೇವಾಸುರಾತ್ಮಕಮ್','after':'ಜಗದೇತಚ್ಚರಾಚರಮ್'},(1,47,47):{'before':'ನಮಃ ಕ್ಷುದ್ರಾಧಾರಿಣೇ','after':'ನಮಶ್ಚಂದ್ರಾರ್ಧಧಾರಿಣೇ'}}
    span=unit['accepted_replacement_span'];assert span==expected_spans[key] and old['text'].count(span['before'])==1 and old['text'].replace(span['before'],span['after'])==new['text'],'Google repair exceeds accepted minimal span'
    assert x['accepted_translation'] is None and x['accepted_transliteration']==new['text'] and not x['issues'],'Google mantra translated or acceptance changed'
    commit=review['base_snapshot_commit'];base=x['base_file'];assert re.fullmatch('[0-9a-f]{40}',commit) and item['base_snapshot_commit']==commit and Path(base).parts[0]=='translation' and '..'not in Path(base).parts,'Google base unpinned'
    raw=subprocess.check_output(['git','show',commit+':'+base],cwd=root);rows=[z for z in csv.DictReader(io.StringIO(raw.decode()),delimiter='\t')if (int(z.get('khanda')or 1),int(z['chapter']),int(z['verse']))==key]
    assert len(rows)==1 and all(rows[0][f]==old[f]for f in fields),'Google correction differs from historical row'
    path=root/item['adjudication_file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['adjudication_sha256'] and json.loads(path.read_text())==review,'Google writer review differs'
    if key==(1,46,46):assert x['edition_variant']=={'original_surrounding':'धन्यौ मातापिता','Google_surrounding':'धन्य माता पिता','status':'surrounding_base_text_retained_not_harmonized'},'Surrounding edition difference hidden'


def validate_google_retained_holds(root,review,replayed,batch):
    a=_google_evidence(root,review);holds=review['no_change_adjudications']
    assert [x['key']for x in holds]==batch.get('no_change_keys',[]),'Google hold list differs'
    for x in holds:
        key=tuple(x['key']);old={f:replayed[key][f]for f in ('source_pages','type','text')}
        unit=next(z for z in a['records']if z['key']=='.'.join(map(str,key)))
        assert old==x['old_row']==x['new_row'] and not x['replacements'] and unit['accepted_replacement_span'] is None,'Held Google target changed'
        assert x['review_status']=='reviewed_no_text_change_hold' and x['accepted_translation'] is None and x['accepted_transliteration'] is None and x['counted_as_new_correction'] is False,'Held target falsely accepted'
        assert x['issues'] and all(i['status']=='open' and i['reading'] is None for i in x['issues']),'Google hold closed'
        if key[1]==21:assert x['older_scan_reading_certain'] is False and x['edition_difference_established'] is False and x['earlier_categorical_older_ligature_certainty_superseded'] is True,'Older ligature certainty overstated'
        if key==(1,46,35):assert x['google_printing_corroborated'] is True and x['grammar_certified'] is False,'Printed agreement promoted to grammar correctness'
        if key==(1,47,29):assert x['original_spelling']=='गणाध्याक्ष' and x['google_spelling']=='गणाध्यक्ष' and x['current_standard_epithet_retained'] is True,'Spelling discrepancy hidden'
        if key==(1,46,51):assert x['source_spacing_difference']=={'original':'परापदि','Google':'परा पदि'} and x['meaning_certified'] is False,'Spacing difference promoted to meaning'
