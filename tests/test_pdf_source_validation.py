"""Focused scan-provenance and treatment regression tests, no source edits."""
import copy,csv,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from json_storage import load_json_document
from validate_pdf_review import validate_pdf_batch
class PDFReview(unittest.TestCase):
 def setUp(self):
  m=json.loads((ROOT/'translation/batch-manifest.json').read_text());self.batch=copy.deepcopy(next(x for x in m['batches'] if x.get('source_kind')=='local_pdf'))
  self.review=json.loads((ROOT/self.batch['review_file']).read_text());self.registry=load_json_document(ROOT/'translation/unresolved-passages.json')
  with(ROOT/'translation'/self.batch['file']).open() as f:self.rows={(int(x['khanda']),int(x['chapter']),int(x['verse'])):x for x in csv.DictReader(f,delimiter='\t')}
 def check(self):return validate_pdf_batch(ROOT,self.batch,self.rows,self.review,self.registry)
 def reject(self):
  with self.assertRaises(AssertionError):self.check()
 def test_valid(self):self.assertEqual(self.check()[1],{(2,2,30)})
 def add_cross_file(self):
  source={'filename':'continuation.pdf','sha256':'a'*64}
  self.batch['additional_source_pdfs']=[source];self.review['additional_source_pdfs']=[copy.deepcopy(source)]
  page=copy.deepcopy(self.batch['source_pages'][0]);page.update(source_sha256=source['sha256'],id='pdf:'+source['sha256']+':p'+str(page['pdf_page']))
  self.batch['source_pages'].append(page)
  item=self.review['verses'][0];key=tuple(item['key']);item['source_pages']+=','+page['id'];self.rows[key]['source_pages']=item['source_pages']
 def test_actual_chapter5_cross_pdf_verse(self):
  manifest=json.loads((ROOT/'translation/batch-manifest.json').read_text())
  batch=next(x for x in manifest['batches'] if x['file']=='batch-19-local-pdf-01.tsv')
  review=json.loads((ROOT/batch['review_file']).read_text())
  with (ROOT/'translation'/batch['file']).open() as f:
   rows={(int(x['khanda']),int(x['chapter']),int(x['verse'])):x for x in csv.DictReader(f,delimiter='\t')}
  tokens=rows[(2,5,20)]['source_pages'].split(',')
  self.assertEqual(len(tokens),2)
  self.assertEqual(len({x.split(':')[1] for x in tokens}),2)
  validate_pdf_batch(ROOT,batch,rows,review,self.registry)
  batch['additional_source_pdfs']=[];review['additional_source_pdfs']=[]
  with self.assertRaises(AssertionError):validate_pdf_batch(ROOT,batch,rows,review,self.registry)
 def test_cross_file_verse(self):
  self.add_cross_file();self.check()
 def test_undeclared_cross_file(self):
  self.add_cross_file();self.batch['additional_source_pdfs']=[];self.review['additional_source_pdfs']=[];self.reject()
 def test_mismatched_additional_identity(self):
  self.add_cross_file();self.review['additional_source_pdfs'][0]['filename']='other.pdf';self.reject()
 def test_wrong_cross_file_token(self):
  self.add_cross_file();self.batch['source_pages'][-1]['id']+='0';self.reject()
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
