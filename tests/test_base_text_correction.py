"""A base-edition repair may change one reviewed token, never its source/treatment."""
from pathlib import Path
import sys,json,copy,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from validate_text_correction import validate_base_text_correction
class BaseRepair(unittest.TestCase):
 def setUp(self):
  b=json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches'][-1];self.item=copy.deepcopy(b['text_corrections'][0]);self.review=json.loads((ROOT/b['review_file']).read_text());self.old=copy.deepcopy(self.item['old_row']);self.new=copy.deepcopy(self.item['new_row'])
 def check(self):validate_base_text_correction(ROOT,self.old,self.new,self.item,self.review)
 def reject(self):
  with self.assertRaises(AssertionError):self.check()
 def test_accepted_name_only(self):self.check();self.assertIn('ಶೇಷನಾಗಂ ಚ ನರಂ',self.new['text'])
 def test_delete_edition_cha(self):self.new['text']=self.new['text'].replace(' ಚ ನರಂ',' ನರಂ');self.item['new_row']=copy.deepcopy(self.new);self.review['new_row']=copy.deepcopy(self.new);self.reject()
 def test_change_treatment(self):self.new['type']='translation';self.item['new_row']=copy.deepcopy(self.new);self.review['new_row']=copy.deepcopy(self.new);self.reject()
 def test_reassign_primary_page(self):self.new['source_pages']='gb:Lh0FEQAAQBAJ:PT65';self.item['new_row']=copy.deepcopy(self.new);self.review['new_row']=copy.deepcopy(self.new);self.reject()
 def test_unaccepted_review(self):self.review['independent_review']['status']='pending';self.reject()
 def test_reference_crop_hash(self):self.review['reference_source']['crop_sha256']='0'*64;self.reject()
 def test_unpinned_base(self):self.review['base_snapshot_commit']='HEAD';self.reject()
 def test_other_old_name(self):self.old['text']=self.old['text'].replace('ಶೌನಕಂ','ಶೇಷನಾಗಂ');self.item['old_row']=copy.deepcopy(self.old);self.review['old_row']=copy.deepcopy(self.old);self.reject()
if __name__=='__main__':unittest.main()
