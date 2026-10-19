"""Verify source-backed base translation repairs and unaccepted meaning holds."""
from pathlib import Path
import unittest,json,copy,hashlib,tempfile,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from validate_text_correction import validate_base_translation_correction,validate_no_change_base_adjudications
class BaseTranslation(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'.git').write_text('gitdir: '+str(ROOT/'.git')+'\n');b=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('source_kind')=='reviewed_base_translation');self.items=copy.deepcopy(b['text_corrections']);self.review=json.loads((ROOT/b['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def check(self,index=0):
  item=self.items[index];p=self.root/item['adjudication_file'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(self.review,ensure_ascii=False));item['adjudication_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();validate_base_translation_correction(self.root,item['old_row'],item['new_row'],item,self.review)
 def reject(self,index=0):
  with self.assertRaises(AssertionError):self.check(index)
 def test_both_valid(self):self.check();self.check(1)
 def test_source_mapping_preserved(self):self.items[0]['new_row']['source_pages']='18';self.review['reviews'][0]['new_row']['source_pages']='18';self.reject()
 def test_hold_not_promoted(self):self.items[0]['new_row']['type']='translation';self.review['reviews'][0]['new_row']['type']='translation';self.reject()
 def test_uncertain_ending_not_completed(self):self.items[0]['new_row']['text']='ಅವನ ಭಕ್ತನಾಗುವೆನು';self.review['reviews'][0]['new_row']['text']='ಅವನ ಭಕ್ತನಾಗುವೆನು';self.reject()
 def test_edition_variant_not_harmonized(self):self.review['reviews'][0]['edition_variant']['base']='सविस्तारं';self.reject()
 def test_unchanged_sanskrit(self):self.review['reviews'][0]['source_sanskrit']='altered';self.reject()
 def test_exact_google_page(self):self.review['reviews'][0]['reference_source']['page_url']='https://books.google.co.in/books?id=Lh0FEQAAQBAJ&pg=PT85';self.reject()
 def test_no_guessed_demonstrative(self):
  for x in [self.items[1]['new_row'],self.review['reviews'][1]['new_row']]:x['text']=x['text'].replace('ಇದನ್ನು','ವೇದವನ್ನು')
  self.reject(1)
 def test_missing_original_pixels(self):(self.root/self.review['reviews'][0]['additional_original_source']['file']).unlink();self.reject()
 def test_missing_independent_review(self):self.review['reviews'][0]['independent_review']['status']='pending';self.reject()
 def test_unpinned_base(self):self.review['base_snapshot_commit']='HEAD';self.reject()
 def test_worker_acceptance_remains_null(self):
  p=self.root/self.review['candidate_file'];d=json.loads(p.read_text());d['items'][0]['accepted_kannada']='promoted';p.write_text(json.dumps(d));h=hashlib.sha256(p.read_bytes()).hexdigest();self.review['candidate_sha256']=h;next(x for x in self.review['evidence_files']if x['file']==self.review['candidate_file'])['sha256']=h;self.reject()
class OriginalOnlyRepair(BaseTranslation):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'.git').write_text('gitdir: '+str(ROOT/'.git')+'\n');b=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/khanda1-ch3-v12-writer-review.json');self.items=copy.deepcopy(b['text_corrections']);self.review=json.loads((ROOT/b['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def test_both_valid(self):self.check()
 def test_edition_variant_not_harmonized(self):self.review['reviews'][0]['edition_variant']={'guessed':'variant'};self.reject()
 def test_exact_google_page(self):self.review['reviews'][0]['reference_source']['page_id']='PT100';self.reject()
 def test_no_guessed_demonstrative(self):
  for x in [self.items[0]['new_row'],self.review['reviews'][0]['new_row']]:x['text']=x['text'].replace('ಅವನ ಐಶ್ವರ್ಯ','ನಿನ್ನ ಐಶ್ವರ್ಯ')
  self.reject()
 def test_worker_acceptance_remains_null(self):
  p=self.root/self.review['candidate_file'];d=json.loads(p.read_text());d['accepted_kannada']='promoted';p.write_text(json.dumps(d));h=hashlib.sha256(p.read_bytes()).hexdigest();self.review['candidate_sha256']=h;next(x for x in self.review['evidence_files']if x['file']==self.review['candidate_file'])['sha256']=h;self.reject()
 def test_note_cannot_be_omitted(self):self.review['reviews'][0]['display_note']='';self.reject()
class PartialClauseRepair(OriginalOnlyRepair):
 def setUp(self):
  super().setUp();b=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/khanda1-ch3-v63-writer-review.json');self.items=copy.deepcopy(b['text_corrections']);self.review=json.loads((ROOT/b['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def test_no_guessed_demonstrative(self):
  self.review['reviews'][0]['issues']=self.review['reviews'][0]['issues'][:1];self.reject()
 def test_note_cannot_be_omitted(self):
  for x in [self.items[0]['new_row'],self.review['reviews'][0]['new_row']]:x['text']=x['text'].split(' (ಪರಿಶೀಲನೆ:')[0]
  self.reject()
 def test_glyph_cannot_be_certified(self):self.review['reviews'][0]['source_reading_status']='accepted';self.reject()
class FivePassageRepair(OriginalOnlyRepair):
 def setUp(self):
  super().setUp();self.batch=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/khanda1-ch4-five-writer-review.json');self.items=copy.deepcopy(self.batch['text_corrections']);self.review=json.loads((ROOT/self.batch['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def test_both_valid(self):
  for i in range(4):self.check(i)
 def test_no_guessed_demonstrative(self):
  for x in [self.items[0]['new_row'],self.review['reviews'][0]['new_row']]:x['text']=x['text'].replace('ಅಲ್ಲಿ','ಶೂಲಪಾಣಿಯನ್ನು ಹೊಗಳಿ ಅಲ್ಲಿ')
  self.reject()
 def test_note_cannot_be_omitted(self):self.review['reviews'][0]['partial_suffix']='';self.reject()
 def test_worker_acceptance_remains_null(self):
  p=self.root/self.review['candidate_file'];d=json.loads(p.read_text());d['records'][0]['accepted_kannada']='promoted';p.write_text(json.dumps(d));h=hashlib.sha256(p.read_bytes()).hexdigest();self.review['candidate_sha256']=h;next(x for x in self.review['evidence_files']if x['file']==self.review['candidate_file'])['sha256']=h;self.reject()
 def test_mantra_single_token_only(self):
  for x in [self.items[2]['new_row'],self.review['reviews'][2]['new_row']]:x['text']=x['text'].replace('ಲಂಬೋದರಾಯ','ಲಂಬೋದರ')
  self.reject(2)
 def test_mantra_treatment_preserved(self):self.items[3]['new_row']['type']='translation';self.review['reviews'][3]['new_row']['type']='translation';self.reject(3)
 def nochange(self):
  x=self.review['no_change_adjudications'][0];validate_no_change_base_adjudications(self.root,self.review,{tuple(x['key']):x['old_row']},self.batch)
 def test_15_valid_no_change(self):self.nochange()
 def test_15_cannot_rewrite(self):
  self.review['no_change_adjudications'][0]['new_row']['text']='rewritten'
  with self.assertRaises(AssertionError):self.nochange()
 def test_15_cannot_close_hold(self):
  self.review['no_change_adjudications'][0]['accepted_translation']='accepted'
  with self.assertRaises(AssertionError):self.nochange()
class FourTranscriptionRepairs(unittest.TestCase):
 check=BaseTranslation.check
 reject=BaseTranslation.reject
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'.git').write_text('gitdir: '+str(ROOT/'.git')+'\n');self.batch=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/khanda1-ch4-remaining-writer-review.json');self.items=copy.deepcopy(self.batch['text_corrections']);self.review=json.loads((ROOT/self.batch['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def nochange(self):
  x=self.review['no_change_adjudications'][0];validate_no_change_base_adjudications(self.root,self.review,{tuple(x['key']):x['old_row']},self.batch)
 def test_all_valid(self):
  for i in range(4):self.check(i)
  self.nochange()
 def test_30_all_declared_tokens_required(self):self.review['reviews'][0]['replacements'].pop();self.reject()
 def test_30_meaning_hold_not_closed(self):self.review['reviews'][0].update(issues=[],review_status='accepted');self.reject()
 def test_mantra_treatment_preserved(self):self.items[0]['new_row']['type']='translation-review';self.review['reviews'][0]['new_row']['type']='translation-review';self.reject()
 def test_only_authorized_token_repairs(self):
  for x in [self.items[1]['new_row'],self.review['reviews'][1]['new_row']]:x['text']=x['text'].replace('ನ ಶಕ್ನೋಮಿ','ಶಕ್ನೋಮಿ')
  self.reject(1)
 def test_100_cannot_certify_current(self):
  self.review['no_change_adjudications'][0]['current_wording_source_verified']=True
  with self.assertRaises(AssertionError):self.nochange()
 def test_100_cannot_replace(self):
  self.review['no_change_adjudications'][0]['new_row']['text']='conjecture'
  with self.assertRaises(AssertionError):self.nochange()
 def test_100_cannot_accept_meaning(self):
  self.review['no_change_adjudications'][0]['accepted_translation']='accepted'
  with self.assertRaises(AssertionError):self.nochange()
 def test_unknown_google_stays_null(self):self.review['reviews'][0]['reference_source']['page_id']='PT1';self.reject()
 def test_source_reading_immutable(self):self.review['reviews'][0]['source_sanskrit']='emended';self.reject()
class TwoMeaningCorrections(unittest.TestCase):
 check=BaseTranslation.check
 reject=BaseTranslation.reject
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'.git').write_text('gitdir: '+str(ROOT/'.git')+'\n');self.batch=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/khanda1-ch5-ch6-writer-review.json');self.items=copy.deepcopy(self.batch['text_corrections']);self.review=json.loads((ROOT/self.batch['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def nochange(self):validate_no_change_base_adjudications(self.root,self.review,{tuple(x['key']):x['old_row']for x in self.review['no_change_adjudications']},self.batch)
 def test_all_valid(self):self.check();self.check(1);self.nochange()
 def test_full_must_match_supported_proposal(self):
  for x in [self.items[0]['new_row'],self.review['reviews'][0]['new_row']]:x['text']=x['text'].replace('ದೇವನು','ದೇವತೆಗಳು')
  self.reject()
 def test_partial_hold_not_closed(self):self.review['reviews'][1]['issues']=[];self.reject(1)
 def test_partial_note_not_stripped(self):
  for x in [self.items[1]['new_row'],self.review['reviews'][1]['new_row']]:x['text']=x['text'].split(' (ಪರಿಶೀಲನೆ:')[0]
  self.reject(1)
 def test_no_google_guess(self):self.review['reviews'][0]['reference_source']['page_id']='PT200';self.reject()
 def test_6_8_negation_not_rewritten(self):
  self.review['no_change_adjudications'][0]['new_row']['text']=self.review['no_change_adjudications'][0]['new_row']['text'].replace('ಉಂಟಾಗಲಿಲ್ಲ','ಉಂಟಾಯಿತು')
  with self.assertRaises(AssertionError):self.nochange()
 def test_6_13_not_accepted(self):
  self.review['no_change_adjudications'][1]['accepted_translation']='accepted'
  with self.assertRaises(AssertionError):self.nochange()
 def test_6_20_coverage_gloss_flags_present(self):
  x=self.review['no_change_adjudications'][2];self.assertEqual(x['unrendered_source_tokens'],['वृथा']);self.assertTrue(x['interpretive_gloss_concerns']);self.assertFalse(x['current_wording_source_verified'])
 def test_6_20_not_fixed(self):
  self.review['no_change_adjudications'][2]['issues']=[]
  with self.assertRaises(AssertionError):self.nochange()
 def test_source_not_emended(self):self.review['reviews'][0]['source_sanskrit']='harmonized';self.reject()
class MixedFiveCorrections(unittest.TestCase):
 check=BaseTranslation.check
 reject=BaseTranslation.reject
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'.git').write_text('gitdir: '+str(ROOT/'.git')+'\n');self.batch=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/khanda1-ch6-ch7-writer-review.json');self.items=copy.deepcopy(self.batch['text_corrections']);self.review=json.loads((ROOT/self.batch['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def test_all_valid(self):
  for i in range(5):self.check(i)
 def test_grammar_hold_cannot_close(self):self.review['reviews'][2].update(issues=[],review_status='accepted');self.reject(2)
 def test_partial_hold_cannot_close(self):self.review['reviews'][0]['issues']=[];self.reject()
 def test_svarat_hold_cannot_close(self):self.review['reviews'][4]['accepted_translation']='guessed';self.reject(4)
 def test_note_not_stripped(self):
  for x in [self.items[4]['new_row'],self.review['reviews'][4]['new_row']]:x['text']=x['text'].split(' (ಪರಿಶೀಲನೆ:')[0]
  self.reject(4)
 def test_both_inflections_required(self):self.review['reviews'][2]['replacements'].pop();self.reject(2)
 def test_preserve_other_mantra_text(self):
  for x in [self.items[1]['new_row'],self.review['reviews'][1]['new_row']]:x['text']=x['text'].replace('ಹ್ಯಸತ್','ಸತ್')
  self.reject(1)
 def test_unknown_google_null(self):self.review['reviews'][0]['reference_source']['page_id']='PT200';self.reject()
 def test_source_reading_immutable(self):self.review['reviews'][0]['source_sanskrit']='emended';self.reject()
 def test_prose_not_fully_accepted(self):self.review['reviews'][0]['accepted_translation']=self.review['reviews'][0]['new_row']['text'];self.reject()
class FiveMantraCorrections(unittest.TestCase):
 check=BaseTranslation.check
 reject=BaseTranslation.reject
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'.git').write_text('gitdir: '+str(ROOT/'.git')+'\n');self.batch=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/khanda1-ch7-ch8-writer-review.json');self.items=copy.deepcopy(self.batch['text_corrections']);self.review=json.loads((ROOT/self.batch['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def test_all_valid(self):
  for i in range(5):self.check(i)
 def test_45_segmentation_hold_not_closed(self):self.review['reviews'][3].update(issues=[],review_status='accepted');self.reject(3)
 def test_46_compound_hold_not_closed(self):self.review['reviews'][4].update(issues=[],review_status='accepted');self.reject(4)
 def test_only_second_laghave_changed(self):
  self.assertIn('ಲಘವೇ ಲಘುರೂಪಾಯ ಲಘೂನಾಂ ಲಾಘವೇ',self.items[1]['new_row']['text'])
  for x in [self.items[1]['new_row'],self.review['reviews'][1]['new_row']]:x['text']=x['text'].replace('ಲಘವೇ ಲಘುರೂಪಾಯ','ಲಾಘವೇ ಲಘುರೂಪಾಯ')
  self.reject(1)
 def test_45_all_declared_changes_required(self):self.review['reviews'][3]['replacements'].pop();self.reject(3)
 def test_46_all_declared_changes_required(self):self.review['reviews'][4]['replacements'].pop();self.reject(4)
 def test_mantra_meaning_not_accepted(self):self.review['reviews'][3]['accepted_translation']='settled';self.reject(3)
 def test_unknown_google_null(self):self.review['reviews'][0]['reference_source']['page_id']='PT1';self.reject()
 def test_source_reading_immutable(self):self.review['reviews'][4]['source_sanskrit']='normalized';self.reject(4)
 def test_42_other_yoginam_preserved(self):
  for x in [self.items[2]['new_row'],self.review['reviews'][2]['new_row']]:x['text']=x['text'].replace('ಯೋಗಿನಾಂ','ಯೋಗನಾಂ')
  self.reject(2)
class FourChapterEightRepairs(unittest.TestCase):
 check=BaseTranslation.check
 reject=BaseTranslation.reject
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'.git').write_text('gitdir: '+str(ROOT/'.git')+'\n');self.batch=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/khanda1-ch8-writer-review.json');self.items=copy.deepcopy(self.batch['text_corrections']);self.review=json.loads((ROOT/self.batch['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def nochange(self):validate_no_change_base_adjudications(self.root,self.review,{tuple(x['key']):x['old_row']for x in self.review['no_change_adjudications']},self.batch)
 def test_all_four_valid_and_51_unchanged(self):
  for i in range(4):self.check(i)
  self.nochange()
 def test_54_interpretation_hold_not_closed(self):self.review['reviews'][1].update(issues=[],review_status='accepted');self.reject(1)
 def test_54_not_harmonized_to_irregular_quote(self):
  for x in [self.items[1]['new_row'],self.review['reviews'][1]['new_row']]:x['text']=x['text'].replace('ಮಭೇದೈಕಾ','ಮಭೇದೋಕಾ')
  self.reject(1)
 def test_65_both_phrase_changes_required(self):self.review['reviews'][3]['replacements'].pop();self.reject(3)
 def test_61_retroflex_nakara_preserved(self):
  for x in [self.items[2]['new_row'],self.review['reviews'][2]['new_row']]:x['text']=x['text'].replace('ಣಕಾರಮ್','ನಕಾರಮ್')
  self.reject(2)
 def test_51_not_newly_corrected(self):
  self.review['no_change_adjudications'][0]['counted_as_new_correction']=True
  with self.assertRaises(AssertionError):self.nochange()
 def test_51_anusvara_not_removed(self):
  self.review['no_change_adjudications'][0]['new_row']['text']=self.review['no_change_adjudications'][0]['new_row']['text'].replace('ವಿಜ್ಞಾನಕರಂ','ವಿಜ್ಞಾನಕರ')
  with self.assertRaises(AssertionError):self.nochange()
 def test_51_not_newly_accepted_transliteration(self):
  self.review['no_change_adjudications'][0]['accepted_transliteration']='accepted'
  with self.assertRaises(AssertionError):self.nochange()
 def test_unknown_google_null(self):self.review['reviews'][0]['reference_source']['page_id']='PT1';self.reject()
 def test_source_reading_immutable(self):self.review['reviews'][0]['source_sanskrit']='normalized';self.reject()
class OneTokenFourNoChanges(unittest.TestCase):
 check=BaseTranslation.check
 reject=BaseTranslation.reject
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'.git').write_text('gitdir: '+str(ROOT/'.git')+'\n');self.batch=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/khanda1-ch9-ch10-writer-review.json');self.items=copy.deepcopy(self.batch['text_corrections']);self.review=json.loads((ROOT/self.batch['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def nochange(self):validate_no_change_base_adjudications(self.root,self.review,{tuple(x['key']):x['old_row']for x in self.review['no_change_adjudications']},self.batch)
 def rejects_nochange(self):
  with self.assertRaises(AssertionError):self.nochange()
 def test_all_valid(self):self.check();self.nochange()
 def test_39_not_scan_certified_kham(self):self.review['no_change_adjudications'][2]['printed_disputed_token']='तस्मात्खं';self.rejects_nochange()
 def test_39_not_accepted_emendation(self):self.review['no_change_adjudications'][2]['source_emendation_accepted']=True;self.rejects_nochange()
 def test_38_referents_not_identified(self):self.review['no_change_adjudications'][1]['same_referent_assumed']=True;self.rejects_nochange()
 def test_38_unit_not_invented(self):self.review['no_change_adjudications'][1]['yojana_unit_printed_in_9_38']=True;self.rejects_nochange()
 def test_38_numerals_not_harmonized(self):self.review['no_change_adjudications'][1]['numerals_harmonized']=True;self.rejects_nochange()
 def test_14_meaning_not_accepted(self):self.review['no_change_adjudications'][3]['accepted_translation']='settled';self.rejects_nochange()
 def test_2_not_counted_as_fixed(self):self.review['no_change_adjudications'][0]['counted_as_new_correction']=True;self.rejects_nochange()
 def test_23_only_declared_token_changes(self):
  for x in [self.items[0]['new_row'],self.review['reviews'][0]['new_row']]:x['text']=x['text'].replace('ಸಮಭಾವಾಯ','ವಿಷಮಭಾವಾಯ')
  self.reject()
 def test_unknown_google_null(self):self.review['no_change_adjudications'][0]['reference_source']['page_id']='PT1';self.rejects_nochange()
class ThreePhraseTwoConfirmations(unittest.TestCase):
 check=BaseTranslation.check
 reject=BaseTranslation.reject
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'.git').write_text('gitdir: '+str(ROOT/'.git')+'\n');self.batch=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/khanda1-ch10-ch11-writer-review.json');self.items=copy.deepcopy(self.batch['text_corrections']);self.review=json.loads((ROOT/self.batch['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def nochange(self):validate_no_change_base_adjudications(self.root,self.review,{tuple(x['key']):x['old_row']for x in self.review['no_change_adjudications']},self.batch)
 def reject_nochange(self):
  with self.assertRaises(AssertionError):self.nochange()
 def test_all_valid(self):
  for i in range(3):self.check(i)
  self.nochange()
 def test_27_not_counted_fixed(self):self.review['no_change_adjudications'][0]['counted_as_new_correction']=True;self.reject_nochange()
 def test_27_name_not_corrupted(self):self.review['no_change_adjudications'][0]['new_row']['text']='ದುಢಿರಾಜಾಯ';self.reject_nochange()
 def test_33_not_renumbered(self):self.review['no_change_adjudications'][1]['printed_numeral']=32;self.reject_nochange()
 def test_33_sequence_preserved(self):self.review['no_change_adjudications'][1]['printed_sequence']=[31,32,32,34,35];self.reject_nochange()
 def test_29_vocatives_not_dative_compound(self):
  for x in [self.items[1]['new_row'],self.review['reviews'][1]['new_row']]:x['text']=x['text'].replace('ಧರಣೀಧರ','ಧರಣೀಧರಾಯ')
  self.reject(1)
 def test_34_referents_remain_held(self):self.review['reviews'][2].update(issues=[],review_status='accepted');self.reject(2)
 def test_25_other_words_preserved(self):
  for x in [self.items[0]['new_row'],self.review['reviews'][0]['new_row']]:x['text']=x['text'].replace('ನಿರ್ಮಲಾಯ','ಮಲಾಯ')
  self.reject()
 def test_unknown_google_null(self):self.review['no_change_adjudications'][0]['reference_source']['page_id']='PT1';self.reject_nochange()
 def test_raw_source_unchanged(self):self.review['reviews'][1]['source_sanskrit']='harmonized';self.reject(1)
class FiveChapterElevenRepairs(unittest.TestCase):
 check=BaseTranslation.check
 reject=BaseTranslation.reject
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'.git').write_text('gitdir: '+str(ROOT/'.git')+'\n');self.batch=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/khanda1-ch11-writer-review.json');self.items=copy.deepcopy(self.batch['text_corrections']);self.review=json.loads((ROOT/self.batch['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def test_all_five_valid(self):
  for i in range(5):self.check(i)
 def test_36_yatnaya_unchanged(self):
  for x in [self.items[0]['new_row'],self.review['reviews'][0]['new_row']]:x['text']=x['text'].replace('ಯತ್ನಾಯ','ಯತ್ತಾಯ')
  self.reject()
 def test_36_chetana_unchanged(self):
  for x in [self.items[0]['new_row'],self.review['reviews'][0]['new_row']]:x['text']=x['text'].replace('ಚೇತನಾಧಾರಿಣೇ','ಚೈತನ್ಯಧಾರಿಣೇ')
  self.reject()
 def test_37_both_edits_required(self):self.review['reviews'][1]['replacements'].pop();self.reject(1)
 def test_37_jyoti_vowel_preserved(self):
  for x in [self.items[1]['new_row'],self.review['reviews'][1]['new_row']]:x['text']=x['text'].replace('ಜ್ಯೋತೀರೂಪಾಯ','ಜ್ಯೋತಿರೂಪಾಯ')
  self.reject(1)
 def test_38_avagraha_preserved(self):
  for x in [self.items[2]['new_row'],self.review['reviews'][2]['new_row']]:x['text']=x['text'].replace('ಸೋಽಹಂ','ಸೋಹಂ')
  self.reject(2)
 def test_39_vocative_not_normalized(self):
  for x in [self.items[3]['new_row'],self.review['reviews'][3]['new_row']]:x['text']=x['text'].replace('ಸರ್ವಾತ್ಮಕ','ಸರ್ವಾತ್ಮಕಾಯ')
  self.reject(3)
 def test_42_compound_ending_preserved(self):
  for x in [self.items[4]['new_row'],self.review['reviews'][4]['new_row']]:x['text']=x['text'].replace('ವಿವರ್ಜಿತ','ವಿವರ್ಜಿತಾಯ')
  self.reject(4)
 def test_meaning_limit_not_closed(self):self.review['reviews'][1].update(issues=[],review_status='accepted');self.reject(1)
 def test_google_target_unknown(self):self.review['reviews'][0]['reference_source']['page_id']='PT1';self.reject()
class TwoRepairsThreeHolds(unittest.TestCase):
 check=BaseTranslation.check
 reject=BaseTranslation.reject
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'.git').write_text('gitdir: '+str(ROOT/'.git')+'\n');self.batch=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/khanda1-ch11-ch13-writer-review.json');self.items=copy.deepcopy(self.batch['text_corrections']);self.review=json.loads((ROOT/self.batch['review_file']).read_text())
  for f in self.review['evidence_files']:
   p=self.root/f['file'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/f['file'],p)
 def nochange(self):validate_no_change_base_adjudications(self.root,self.review,{tuple(x['key']):x['old_row']for x in self.review['no_change_adjudications']},self.batch)
 def reject_nochange(self):
  with self.assertRaises(AssertionError):self.nochange()
 def test_all_valid(self):
  self.check();self.check(1);self.nochange()
 def test_46_meaning_not_accepted(self):self.review['reviews'][0].update(issues=[],review_status='accepted');self.reject()
 def test_24_both_replacements_required(self):self.review['reviews'][1]['replacements'].pop();self.reject(1)
 def test_chitte_not_new_correction(self):self.review['no_change_adjudications'][0]['counted_as_new_correction']=True;self.reject_nochange()
 def test_chitte_source_verified(self):self.review['no_change_adjudications'][0]['target_readings_source_verified']=False;self.reject_nochange()
 def test_segmentation_not_settled(self):self.review['no_change_adjudications'][1]['alternative_segmentation_settled']=True;self.reject_nochange()
 def test_source_word_break_not_invented(self):self.review['no_change_adjudications'][1]['word_boundary_printed']=True;self.reject_nochange()
 def test_dual_speakers_preserved(self):self.review['no_change_adjudications'][2]['printed_dual_speakers']=False;self.reject_nochange()
 def test_singular_me_preserved(self):self.review['no_change_adjudications'][2]['printed_singular_possessive']='अस्माकम्';self.reject_nochange()
 def test_no_guessed_google(self):self.review['no_change_adjudications'][1]['reference_source']['page_id']='PT1';self.reject_nochange()
if __name__=='__main__':unittest.main()
