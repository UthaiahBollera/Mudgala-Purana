"""Closed fragment issues need immutable full-verse evidence, not a status toggle."""
import json,hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from validate_pdf_review import validate_boundary_resolution
class ResolutionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'translation').mkdir();self.key=(2,40,45);self.row={'key':list(self.key),'source_sanskrit':'एवम्','source_pages':'page32,page33','text':'reviewedfullverse','review_status':'accepted','issues':[]};self.issue={'source_pages':'page32','resolution':{'key':list(self.key),'review_file':'translation/new.json','source_sanskrit':'एवम्','source_pages':'page32,page33','text':'reviewedfullverse'}};self.write()
 def write(self):
  p=self.root/'translation/new.json';p.write_text(json.dumps({'verses':[self.row]}));self.issue['resolution']['review_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 def check(self):validate_boundary_resolution(self.root,self.issue,self.key)
 def test_reviewed_full_verse_resolves_old_fragment(self):self.check()
 def test_edited_review_is_rejected(self):
  (self.root/'translation/new.json').write_text('{}')
  with self.assertRaises(AssertionError):self.check()
 def test_another_fragment_cannot_resolve_issue(self):
  self.row['fragment']='a_only';self.write()
  with self.assertRaises(AssertionError):self.check()
 def test_open_issues_cannot_resolve_issue(self):
  self.row['issues']=[{'status':'open'}];self.write()
  with self.assertRaises(AssertionError):self.check()
 def test_resolution_requires_new_primary_page(self):
  self.issue['source_pages']='page32,page33'
  with self.assertRaises(AssertionError):self.check()
if __name__=='__main__':unittest.main()
