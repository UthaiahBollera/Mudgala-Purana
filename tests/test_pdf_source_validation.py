"""Focused scan-provenance and treatment regression tests, no source edits."""
import copy,csv,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from validate_pdf_review import validate_pdf_batch
class PDFReview(unittest.TestCase):
 def setUp(self):
  m=json.loads((ROOT/'translation/batch-manifest.json').read_text());self.batch=copy.deepcopy(next(x for x in m['batches'] if x.get('source_kind')=='local_pdf'))
  self.review=json.loads((ROOT/self.batch['review_file']).read_text());self.registry=json.loads((ROOT/'translation/unresolved-passages.json').read_text())
  with(ROOT/'translation'/self.batch['file']).open() as f:self.rows={(int(x['khanda']),int(x['chapter']),int(x['verse'])):x for x in csv.DictReader(f,delimiter='\t')}
 def check(self):return validate_pdf_batch(ROOT,self.batch,self.rows,self.review,self.registry)
 def reject(self):
  with self.assertRaises(AssertionError):self.check()
 def test_valid(self):self.assertEqual(self.check()[1],{(2,2,30)})
 def test_source_hash(self):self.batch['source_sha256']='bad';self.reject()
 def test_wrong_primary(self):self.review['primary_source']['filename']='wrong.pdf';self.reject()
 def test_wrong_page(self):self.batch['source_pages'][0]['id']+='0';self.reject()
 def test_unverified_print_page(self):self.batch['source_pages'][0]['printed_page_verified']=False;self.reject()
 def test_missing_review(self):self.review['verses'].pop();self.reject()
 def test_false_acceptance(self):self.review['verses'][-1]['review_status']='accepted';self.reject()
 def test_missing_notice(self):
  self.review['verses'][-1]['text']=self.rows[(2,2,30)]['text']='ಸರಳ ಪಠ್ಯ';self.reject()
 def test_missing_registry(self):self.registry['records']=[x for x in self.registry['records'] if x['id']!='kh2-ch2-v30'];self.reject()
 def test_wrong_treatment(self):self.review['verses'][0]['classification']['required_treatment']='Kannada-script Sanskrit transliteration';self.reject()
 def test_overstated_independent_pixels(self):self.review['verses'][0]['independent_review']['scope']='independent_pixel_review';self.reject()
if __name__=='__main__':unittest.main()
