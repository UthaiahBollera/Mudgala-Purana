"""Verify source-backed base translation repairs and unaccepted meaning holds."""
from pathlib import Path
import unittest,json,copy,hashlib,tempfile,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from validate_text_correction import validate_base_translation_correction
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
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'.git').write_text('gitdir: '+str(ROOT/'.git')+'\n');b=next(b for b in reversed(json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches'])if b.get('source_kind')=='reviewed_base_translation');self.items=copy.deepcopy(b['text_corrections']);self.review=json.loads((ROOT/b['review_file']).read_text())
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
if __name__=='__main__':unittest.main()
