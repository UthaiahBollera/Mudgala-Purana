"""Original-scan recoveries must retain frozen evidence, holds and one-time joins."""
from pathlib import Path
import unittest,tempfile,json,csv,hashlib,copy,shutil,sys,io
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from validate_png_review import validate_png_batch
class PNGRecovery(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.batch=next(b for b in json.loads((ROOT/'translation/batch-manifest.json').read_text())['batches']if b.get('review_file')=='translation/original-png-khanda2-gap1-review.json');cls.review=json.loads((ROOT/cls.batch['review_file']).read_text());cls.rows={(int(r['khanda']),int(r['chapter']),int(r['verse'])):r for r in csv.DictReader(io.StringIO((ROOT/'translation'/cls.batch['file']).read_text()),delimiter='\t')};d=json.loads((ROOT/'translation/unresolved-passages.json').read_text());ids={'kh2-ch36-v85','kh2-ch37-v20','kh2-ch37-v4',cls.review['recovered_gap_id']};cls.registry={'records':[x for x in d['records']if x['id']in ids]}
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.b=copy.deepcopy(self.batch);self.v=copy.deepcopy(self.review);self.r=copy.deepcopy(self.rows);self.reg=copy.deepcopy(self.registry)
  names=[self.v[k]for k in['candidate_file','frozen_candidate_file','independent_review_file']]+[p['historical_review_file']for x in self.v['verses']for p in x['source_parts']if p.get('historical_review_file')]
  for n in names:p=self.root/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,p)
 def check(self):return validate_png_batch(self.root,self.b,self.r,self.v,self.reg)
 def reject(self):
  with self.assertRaises(AssertionError):self.check()
 def test_valid(self):a,u=self.check();self.assertEqual(len(a),1);self.assertEqual(u,{(2,36,85),(2,37,4)})
 def test_wrong_archive(self):self.b['source_archive']['sha256']='0'*64;self.reject()
 def test_guessed_image_index(self):self.b['source_pages'][0]['image_index']=206;self.v['source_pages'][0]['image_index']=206;self.reject()
 def test_wrong_zip_member(self):self.b['source_pages'][0]['member']='Page Images/page_0206.png';self.v['source_pages'][0]['member']='Page Images/page_0206.png';self.reject()
 def test_changed_source_pixels(self):self.b['source_pages'][0]['image_sha256']='0'*64;self.v['source_pages'][0]['image_sha256']='0'*64;self.reject()
 def test_duplicate_existing_fragment(self):self.v['verses'][0]['source_parts'].insert(0,copy.deepcopy(self.v['verses'][0]['source_parts'][0]));self.reject()
 def test_omitted_gap_owned_verse(self):self.r.pop((2,37,2));self.v['verses']=[x for x in self.v['verses']if x['key']!=[2,37,2]];self.reject()
 def test_noninsertable_aid(self):self.v['verses'][0]['candidate_entry_ids']=['2.36.85.assembled_reading_aid'];self.reject()
 def test_hidden_hold(self):self.r[(2,37,4)]['type']='translation';self.v['verses'][5]['type']='translation';self.reject()
 def test_missing_independent_review(self):(self.root/self.v['independent_review_file']).unlink();self.reject()
 def test_worker_acceptance_cannot_be_promoted(self):
  p=self.root/self.v['candidate_file'];d=json.loads(p.read_text());d['entries'][0]['accepted_sanskrit']='accepted';p.write_text(json.dumps(d,ensure_ascii=False));self.v['candidate_sha256']=hashlib.sha256(p.read_bytes()).hexdigest();self.reject()
if __name__=='__main__':unittest.main()
