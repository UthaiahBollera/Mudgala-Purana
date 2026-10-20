"""Validate bounded additional comparisons without promoting held readings."""
from pathlib import Path
import csv
import hashlib
import json
from urllib.parse import parse_qs,urlparse
from json_storage import load_json_document

EXPECTED = {
 (1,8,46):('हृद्विज्ञबोधात्मक','द्विज्ञबोधात्मक','हृद्विज्ञबोधात्मक',41,21),
 (1,8,54):('अभेदैकात्मकमात्मरूपम्','अभेदमेकात्मकमात्मरूपम्','अभेदोकात्मकमात्मरूपम्',42,22),
 (1,12,24):('गाणपत्यास्ते','गाणपत्याः स्युः','गाणपत्यास्ते',59,31),
 (1,28,18):('पंचवक्त्रधरायैव','पञ्चवकाधरायैव (appears; conjunct hold)','पञ्चवक्त्रधरायैव',120,65),
 (1,21,41):('सुधात्रे? (base ligature still held)','सुधाम्ने','सुधाम्ने',94,51),
 (1,21,45):('प्रधात्रे? (base ligature still held)','प्रधाने','प्रधाम्ने',94,52),
}

def check_record(record):
 k=tuple(record['key']);a=record['independent_comparison'];expected=EXPECTED[k]
 assert tuple(a[x]for x in ['original_reading','google_reading','sanskritdocuments_reading','sanskritdocuments_pdf_physical_page','original_printed_page'])==expected,'Distinct source readings or coordinates changed'
 assert a['key']=='.'.join(map(str,k)) and a['accepted_new_replacement']is a['new_replacement_proposal']is None,'Independent candidate changed'
 assert record['new_text_change']is record['accepted_new_replacement']is record['accepted_translation']is None,'New text accepted'
 assert record['hold_retained'] is True,'Hold closed'
 for f in ['whole_verse_correctness_certified','meaning_certified','underlying_SanskritDocuments_edition_identified','independent_witness_status_established','majority_vote_used','base_scan_misreading_established','OCR_full_bytes_independently_reverified_on_Mac']:assert record[f]is False,'Scope overstated'
 assert a['user_uploaded_OCR']['status']=='derivative OCR, not independent witness or printed-glyph evidence','OCR promoted to witness'
 assert a['sanskritdocuments_printed_pdf_page']==expected[3]-1 and urlparse(a['sanskritdocuments_url']).fragment==f'page={expected[3]}','PDF physical/printed page confused'
 q=parse_qs(urlparse(a['google_verified_url']).query);assert q['id']==['Lh0FEQAAQBAJ']and q['pg']==[a['google_page_id']],'Google identity changed'
 o=record['original_source'];assert o['printed_page']==expected[4] and o['member']==f'Page Images/page_{expected[4]:04d}.png' and o['bbox_xyxy']is None,'Original coordinate invented'
 if k==(1,21,45):assert record['active_source_coordinate_note']=={'disputed_tail_printed_page':52,'verse_begins_previous_printed_page':51,'historical_TSV_source_pages_unchanged':'64,65','prior_review_already_identified_page52':True,'historical_artifacts_unchanged':True},'Continuation coordinate/history changed'

def validate(root):
 root=Path(root);p=root/'translation/four-reference-comparison-index.json'
 if not p.exists():return 0
 def evidence(n,h):
  p=(root/n).resolve();assert p.is_relative_to((root/'translation').resolve())and p.is_file(),'Missing or external evidence';assert hashlib.sha256(p.read_bytes()).hexdigest()==h,'Evidence hash differs';return p
 rows={}
 for f in [root/'translation/narrative.tsv',*sorted((root/'translation').glob('batch-*.tsv'),key=lambda p:(int(p.name.split('-')[1]),p.name))]:
  for r in csv.DictReader(f.open(),delimiter='\t'):rows[(int(r.get('khanda')or 1),int(r['chapter']),int(r['verse']))]=r
 reg={x['id']:x for x in load_json_document(root/'translation/unresolved-passages.json')['records']};seen=set()
 for entry in json.loads(p.read_text())['chapters']:
  r=json.loads(evidence(entry['review_file'],entry['review_sha256']).read_text());assert r['source_kind']=='four_reference_comparison_only'and r['new_text_changes']==0
  assert r['whole_chapter_validation']is r['four_references_are_four_independent_witnesses']is r['full_SanskritDocuments_book_or_full_OCR_published']is r['modern_English_used_as_textual_or_grammatical_source']is False,'Review scope overstated'
  packet=json.loads(evidence(r['independent_receipt_file'],r['independent_receipt_sha256']).read_text());assert r['provenance']==packet['provenance'] and r['provenance']['new_manuscript_changes']==0
  assert [x['key']for x in r['records']]==entry['keys']
  for f in r['evidence_files']:assert Path(f['file']).suffix.lower()in ['.json','.md','.jpg','.png'],'Full book/OCR included';evidence(f['file'],f['sha256'])
  for x in r['records']:
   check_record(x);k=tuple(x['key']);assert k not in seen and k[1]==entry['chapter'];seen.add(k);assert x['independent_comparison']==next(a for a in packet['records']if a['key']=='.'.join(map(str,k)))
   assert x['current_row']=={f:rows[k][f]for f in ['source_pages','type','text']},'Manuscript changed'
   for f in x['target_crops']:evidence(f['file'],f['sha256'])
   evidence(x['original_source']['file'],x['original_source']['sha256']);z=reg[f'kh1-ch{k[1]}-v{k[2]}'];assert z['hard_hold']is True and z['accepted_translation']is None and z['status']==x['prior_registry_status']and z['current_translation_review']==x['prior_current_translation_review']and z.get('latest_source_corroboration')==x['prior_latest_source_corroboration'],'Prior hold/review changed'
   assert z['latest_four_reference_comparison']=={'review_file':entry['review_file'],'review_sha256':entry['review_sha256'],'key':list(k),'hold_retained':True,'new_text_change':None,'meaning_certified':False,'base_scan_misreading_established':False},'Registry pointer or hold changed'
   if k==(1,21,45):assert z['active_original_source_reference']=={**x['original_source'],'continuation':x['active_source_coordinate_note']},'Active original52 reference stale'
 return len(seen)

if __name__=='__main__':print('Four-reference retained-hold comparisons validated:',validate(Path(__file__).resolve().parent))
