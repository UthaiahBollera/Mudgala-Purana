"""Guard against overclaiming in the additional held-reading pass."""
from pathlib import Path
import copy,json,sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from validate_four_reference import check_record
ROOT=Path(__file__).resolve().parents[1]
class HeldComparison(unittest.TestCase):
 def setUp(self):self.record=copy.deepcopy(json.loads((ROOT/'translation/khanda1-ch8-four-reference-comparison.json').read_text())['records'][1])
 def rejected(self,fn):
  fn(self.record)
  with self.assertRaises(AssertionError):check_record(self.record)
 def test_retained_third_distinct_reading(self):check_record(self.record)
 def test_majority_vote_rejected(self):self.rejected(lambda x:x.update(majority_vote_used=True))
 def test_ocr_witness_rejected(self):self.rejected(lambda x:x['independent_comparison']['user_uploaded_OCR'].update(status='independent witness'))
 def test_third_form_not_harmonized(self):self.rejected(lambda x:x['independent_comparison'].update(sanskritdocuments_reading='अभेदैकात्मकमात्मरूपम्'))
 def test_closed_hold_rejected(self):self.rejected(lambda x:x.update(hold_retained=False))
 def test_new_text_rejected(self):self.rejected(lambda x:x.update(accepted_new_replacement='replacement'))
 def test_physical_pdf_page_not_footer(self):self.rejected(lambda x:x['independent_comparison'].update(sanskritdocuments_pdf_physical_page=41))
 def test_unobserved_original_bbox_rejected(self):self.rejected(lambda x:x['original_source'].update(bbox_xyxy=[0,0,1,1]))
 def test_scan_misreading_claim_rejected(self):self.rejected(lambda x:x.update(base_scan_misreading_established=True))
 def test_Mac_full_ocr_verification_not_claimed(self):self.rejected(lambda x:x.update(OCR_full_bytes_independently_reverified_on_Mac=True))
if __name__=='__main__':unittest.main()
