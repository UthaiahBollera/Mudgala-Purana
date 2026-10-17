"""A completed verse may replace only a previously reviewed, declared fragment."""
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from validate_pdf_review import validate_declared_fragment_completion

class FragmentCompletionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'translation').mkdir()
        self.key=(2,39,50);self.old={'source_pages':'pdf:prior:p30','type':'translation','text':'explicit50afragment'}
        self.record=dict(self.old,key=list(self.key),fragment='a_only');self.file='translation/old-review.json'
        self.prior=[{'review_file':self.file,'coverage_boundary':'old'}];self.coverage={'old':{'fragment_only_keys':[list(self.key)]}};self.item={'old_fragment_review_file':self.file};self.write()
    def write(self):
        (self.root/self.file).write_text(json.dumps({'verses':[self.record]}))
    def check(self):
        validate_declared_fragment_completion(self.root,self.old,self.key,self.item,self.prior,self.coverage)
    def test_reviewed_declared_fragment_is_allowed(self):self.check()
    def test_ordinary_translation_cannot_be_replaced(self):
        self.record.pop('fragment');self.write()
        with self.assertRaises(AssertionError):self.check()
    def test_fragment_must_have_been_declared_before_completion(self):
        self.coverage['old']['fragment_only_keys']=[]
        with self.assertRaises(AssertionError):self.check()
    def test_historical_text_cannot_be_rewritten_to_justify_completion(self):
        self.record['text']='changed';self.write()
        with self.assertRaises(AssertionError):self.check()
    def test_current_or_unlisted_review_cannot_authorize_replacement(self):
        self.prior=[]
        with self.assertRaises(AssertionError):self.check()

if __name__=='__main__':unittest.main()
