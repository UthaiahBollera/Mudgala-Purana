"""Append-only repairs must retain source identities and exact review evidence."""
from pathlib import Path
import sys,json,copy,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from validate_text_correction import validate_text_correction
class TextCorrections(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.batches=json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches'];cls.position=next(i for i,b in enumerate(cls.batches)if b.get('text_corrections'));cls.fixture=cls.batches[cls.position]['text_corrections'][0]
 def setUp(self):self.item=copy.deepcopy(self.fixture);self.old=copy.deepcopy(self.item['old_row']);self.new=copy.deepcopy(self.item['new_row'])
 def check(self):validate_text_correction(ROOT,self.old,self.new,self.item,self.batches[:self.position])
 def rejects(self):
  with self.assertRaises(AssertionError):self.check()
 def test_valid(self):self.check()
 def test_changed_source_mapping(self):self.new['source_pages']+='0';self.item['new_row']=copy.deepcopy(self.new);self.rejects()
 def test_changed_sanskrit(self):self.item['source_sanskrit']+=' अन्य';self.rejects()
 def test_changed_source_parts(self):self.item['source_parts'][0]['text']+=' अन्य';self.rejects()
 def test_wrong_prior_text(self):self.old['text']='wrong';self.rejects()
 def test_unaccepted(self):self.item['review_status']='pending';self.rejects()
 def test_wrong_addendum_hash(self):self.item['adjudication_sha256']='0'*64;self.rejects()
 def test_wrong_candidate(self):self.item['accepted_translation']='ಇನ್ನೊಂದು';self.rejects()
if __name__=='__main__':unittest.main()
