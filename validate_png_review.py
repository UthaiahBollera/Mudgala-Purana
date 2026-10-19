"""Validate archive-PNG gap recoveries without changing frozen candidate evidence."""
from collections import Counter
from pathlib import Path
import hashlib,json,re

def candidate_entries(candidate):
    """Normalize source-coordinate schemas in memory; evidence files stay verbatim."""
    if 'entries' in candidate:return candidate['entries']
    if 'records' in candidate:
        units=[]
        for x in candidate['records']+candidate['nonverse_material']:
            refs=x.get('source_refs',x.get('source_spans',x.get('source_provenance')));regions=[]
            for p in refs:
                image=p.get('source_image',p.get('page_image'));image=f'page_{image:04}.png' if isinstance(image,int) else Path(image).name
                regions.append({'image':image,'bbox_xyxy':p.get('bbox_px',p.get('bbox_xyxy',p.get('coordinates_xyxy')))})
            units.append(dict(x,source_regions=regions))
        return units
    return [dict(x, source_regions=[{'image':f"page_{p['image_id']:04}.png",'bbox_xyxy':b} for p in x['source_portions'] for b in p['rectangles_xyxy']]) for x in candidate['front_matter']+candidate['verses']]

def null_acceptance(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if k in ('accepted_sanskrit','accepted_kannada'):assert v is None,'Worker acceptance fields changed'
            null_acceptance(v)
    elif isinstance(value,list):
        for v in value:null_acceptance(v)

def validate_png_batch(root,batch,rows,review,registry):
    assert batch['source_kind']==review['source_kind']=='original_png_archive','Wrong PNG source kind'
    archive=batch['source_archive'];assert archive==review['source_archive'],'PNG archive identity mismatch'
    assert Path(archive['filename']).name==archive['filename'] and archive['filename'].endswith('.zip'),'Invalid PNG archive name'
    assert re.fullmatch('[0-9a-f]{64}',archive['sha256']) and archive['bytes']>0,'Invalid PNG archive digest/size'
    def evidence(path,digest):
        p=(root/path).resolve();assert p.is_relative_to((root/'translation').resolve()) and p.is_file(),'Missing PNG review evidence'
        assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,'PNG review evidence checksum mismatch'
        return p
    candidate=json.loads(evidence(review['candidate_file'],review['candidate_sha256']).read_text())
    frozen=json.loads(evidence(review['frozen_candidate_file'],review['frozen_candidate_sha256']).read_text())
    evidence(review['independent_review_file'],review['independent_review_sha256'])
    if 'revision' in candidate:assert candidate['revision']['original_frozen_sha256']==review['frozen_candidate_sha256'],'Wrong frozen candidate'
    else:
        assert candidate['schema']=='khanda2.long_gap.candidate_bundle.v1' and review['candidate_sha256']==review['frozen_candidate_sha256'],'Wrong frozen reviewed bundle'
        independent=json.loads(evidence(review['independent_review_json_file'],review['independent_review_json_sha256']).read_text())
        assert candidate['independent_review']['report_sha256']==review['independent_review_json_sha256'] and not independent['unchecked_candidate_ranges'],'Incomplete long-gap review'
        for f in review['evidence_files']:evidence(f['file'],f['sha256'])
        null_acceptance(independent)
    for d in [candidate,frozen]:null_acceptance(d)
    units=candidate_entries(candidate);entries={x['id']:x for x in units};assert len(entries)==len(units),'Duplicate candidate entry'
    assert batch['source_pages']==review['source_pages'],'PNG page manifest differs'
    allowed=set()
    for p in batch['source_pages']:
        assert type(p['image_index']) is int and p['image_index']>0,'Invalid image index'
        assert p['id']==f"png:{archive['sha256']}:p{p['image_index']}",'Wrong PNG page ID'
        assert p['member']==f"Page Images/page_{p['image_index']:04}.png",'Wrong PNG member'
        assert p['id'] not in allowed and p['dimensions']==[3840,2508] and p['pixels_Mac_checked'] is True,'Invalid/unverified PNG page'
        images=[x for x in candidate.get('source_images',candidate.get('provenance',{}).get('sources',[]))if x.get('image',x.get('source_image',f"page_{x.get('image_id',0):04}.png"))==Path(p['member']).name]
        assert len(images)==1 and images[0].get('sha256',images[0].get('source_sha256'))==p['image_sha256'],'PNG image digest differs from candidate'
        allowed.add(p['id'])
    assert allowed,'Missing PNG pages'
    records=review['verses'];assert len(records)==len(rows) and {tuple(x['key'])for x in records}==set(rows),'PNG review keys differ'
    indexed={x['id']:x for x in registry['records']};unresolved=set();consumed=Counter()
    compact=lambda s:re.sub(r'\s+','',s)
    for x in records:
        key=tuple(x['key']);row=rows[key]
        assert all(x[f]==row[f]for f in ['source_pages','type','text']),'PNG accepted row differs from review'
        assert x['independent_review']['status']=='accepted','Independent PNG review missing'
        assert x['candidate_entry_ids'] and all(i in entries for i in x['candidate_entry_ids']),'Unknown/noninsertable input'
        consumed.update(x['candidate_entry_ids'])
        assert compact(x['source_sanskrit'])==compact(' '.join(p['text']for p in x['source_parts'])),'PNG Sanskrit join mismatch'
        assert list(dict.fromkeys(p['source_page']for p in x['source_parts']))==x['source_pages'].split(','),'PNG join source map mismatch'
        for p in x['source_parts']:
            if p.get('candidate_entry_id'):
                e=entries[p['candidate_entry_id']];assert p['source_page']in allowed and all(r in e['source_regions'] for r in p['source_regions']),'Gap-owned source changed'
                assert all(r['image']==f"page_{int(p['source_page'].rsplit('p',1)[1]):04}.png"for r in p['source_regions']),'Source coordinates assigned to wrong PNG'
                for region in p['source_regions']:
                    a,b,c,d=region['bbox_xyxy'];assert 0<=a<c<=3840 and 0<=b<d<=2508,'Source bbox outside image'
            else:
                path=(root/p['historical_review_file']).resolve();assert path.is_relative_to((root/'translation').resolve()),'Historical review outside source tree'
                old=[r for r in json.loads(path.read_text())['verses']if tuple(r['key'])==key]
                assert len(old)==1 and old[0]['source_pages']==p['source_page'] and compact(old[0]['source_sanskrit'])==compact(p['text']),'Historical fragment changed or duplicated'
        for cid in x['candidate_entry_ids']:
            parts=[p for p in x['source_parts'] if p.get('candidate_entry_id')==cid]
            assert compact(' '.join(p['text'] for p in parts))==compact(entries[cid]['candidate_sanskrit']),'Gap-owned source changed or duplicated'
            actual=[r for p in parts for r in p['source_regions']]
            assert actual==entries[cid]['source_regions'],'Source coordinates omitted or duplicated'
        open_issues=[i for i in x.get('issues',[])if i.get('status')=='open']
        if x['review_status']=='accepted_with_unresolved_reading':
            assert open_issues and row['type']=='translation-review' and 'ಪರಿಶೀಲನೆ' in row['text'],'Unresolved PNG reading not visible'
            rid=f'kh{key[0]}-ch{key[1]}-v{key[2]}';old=indexed[rid];current=old.get('current_recovery_review',old)
            assert current['source_sanskrit']==x['source_sanskrit'] and current['source_pages']==x['source_pages'] and current['issues']==x['issues'],'PNG hold registry differs'
            assert all(i.get('reading') is None for i in open_issues),'Unresolved PNG reading promoted to accepted'
            unresolved.add(key)
        else:assert x['review_status']=='accepted' and not open_issues and row['type']=='translation','Unreviewed PNG row'
    for n in review['nonverse_adjudications']:
        assert n['candidate_entry_id']in entries and n['review_status']=='accepted' and n['source_pages']in allowed,'Unreviewed PNG nonverse'
        e=entries[n['candidate_entry_id']]
        assert n['source_sanskrit']==e['candidate_sanskrit'] and n['text']==e['candidate_kannada'],'Nonverse differs from corrected candidate'
        if n['kind']!='speaker':consumed[n['candidate_entry_id']]+=1
        else:assert consumed[n['candidate_entry_id']]==1 and n['attached_once_to_key'],'Speaker not attached exactly once'
    assert set(consumed)==set(entries) and all(n==1 for n in consumed.values()),'Omitted or repeated gap-owned unit'
    if 'records' in candidate:
        expected_holds={tuple(map(int,id.split('.'))) for h in independent['retained_holds']for id in h['verse'].split(';')}
        assert unresolved==expected_holds,'Independent long-gap holds omitted or promoted'
    gap=indexed[review['recovered_gap_id']];assert gap['status']=='resolved_by_additional_original_scan' and gap['resolution']['source_archive_sha256']==archive['sha256'],'PNG physical gap not accounted for'
    return allowed,unresolved
