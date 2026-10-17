"""Validate scan-backed continuation provenance; never infer source text from OCR."""
import hashlib,json,re
from pathlib import Path

def validate_declared_fragment_completion(root, old_row, key, item, prior_batches, coverage):
    """Allow an explicit reviewed fragment without rewriting its historical TSV type."""
    matches = [b for b in prior_batches if b['review_file'] == item.get('old_fragment_review_file')]
    assert len(matches) == 1, 'Fragment completion lacks an earlier accepted review'
    batch = matches[0]
    assert list(key) in coverage[batch['coverage_boundary']].get('fragment_only_keys', []), 'Old key was not declared fragment-only'
    review = json.loads((root/batch['review_file']).read_text(encoding='utf-8'))
    records = [r for r in review['verses'] if tuple(r['key']) == key]
    assert len(records) == 1 and records[0].get('fragment') in {'a_only', 'b_only'}, 'Old review lacks explicit fragment evidence'
    assert all(records[0][f] == old_row[f] for f in ('source_pages', 'type', 'text')), 'Fragment evidence differs from historical row'

def validate_pdf_batch(root,batch,rows,review,registry):
    assert batch['source_kind']==review['source_kind']=='local_pdf', 'Wrong PDF review kind'
    identity=batch['source_pdf'];digest=batch['source_sha256']
    assert Path(identity).name==identity and identity.endswith('.pdf'), 'PDF identity must be a basename'
    assert re.fullmatch('[0-9a-f]{64}',digest), 'Invalid PDF hash'
    assert review['primary_source']['filename']==identity and review['primary_source']['sha256']==digest, 'Primary PDF identity mismatch'
    assert review['source_priority']=='scanned_pdf_primary_ocr_aid_google_books_reference', 'Wrong source priority'
    # Cross-file verses retain both page tokens, each tied to a declared PDF.
    sources=batch.get('additional_source_pdfs',[])
    assert sources==review.get('additional_source_pdfs',[]), 'Additional PDF identities mismatch'
    digests={digest}
    identities={identity}
    for source in sources:
        name=source['filename'];other=source['sha256']
        assert Path(name).name==name and name.endswith('.pdf'), 'PDF identity must be a basename'
        assert re.fullmatch('[0-9a-f]{64}',other), 'Invalid additional PDF hash'
        assert name not in identities and other not in digests, 'Duplicate PDF identity'
        identities.add(name);digests.add(other)
    pages=batch['source_pages'];allowed=set()
    for p in pages:
        assert type(p['pdf_page']) is int and p['pdf_page']>0, 'Invalid PDF page'
        page_digest=p.get('source_sha256',digest)
        assert page_digest in digests, 'Undeclared PDF source'
        assert p['id']==f'pdf:{page_digest}:p{p["pdf_page"]}', 'Mismatched PDF page token'
        assert p['id'] not in allowed, 'Duplicate PDF page'
        assert re.fullmatch('[0-9a-f]{64}',p['image_sha256']), 'Missing source image hash'
        assert type(p['printed_page']) is int and p['printed_page']>0 and p['printed_page_verified'] is True, 'Unverified printed page'
        allowed.add(p['id'])
    assert allowed, 'Missing PDF pages'
    records=review['verses'];keys=[tuple(x['key']) for x in records]
    assert len(keys)==len(set(keys)) and set(keys)==set(rows), 'Missing/duplicate PDF reviews'
    unresolved=set()
    for key,x in zip(keys,records):
        row=rows[key]
        assert x['text']==row['text'] and x['source_pages']==row['source_pages'] and x['type']==row['type'], 'PDF review differs from row'
        assert set(x['source_pages'].split(','))<=allowed, 'PDF verse outside source pages'
        assert re.search('[\u0900-\u097f]',x['source_sanskrit']), 'Missing Sanskrit evidence'
        assert x['classification']['required_treatment']==('Kannada-script Sanskrit transliteration' if row['type']=='mantra' else 'formal Kannada translation'), 'Treatment/classification mismatch'
        assert x['independent_review']['status']=='accepted' and x['independent_review']['scope']=='language_and_context_only_source_pixels_checked_by_integrator', 'Independent review missing or overstated'
        open_issues=[i for i in x.get('issues',[]) if i.get('status')=='open']
        if x['review_status']=='accepted_with_unresolved_reading':
            assert row['type']=='translation-review' and open_issues, 'Unresolved PDF verse not marked'
            text=re.sub(r'\s*\[[^\]]*\]','',row['text'])
            assert any('ಪರಿಶೀಲನೆ' in s or 'ಅನಿಶ್ಚಿತ' in s for s in re.findall(r'\([^()]+\)',text)), 'Visible Kannada notice missing'
            matches=[i for i in registry['records'] if i['id']==f'kh{key[0]}-ch{key[1]}-v{key[2]}']
            assert len(matches)==1, 'PDF issue register missing/duplicate'
            issue=matches[0]
            assert issue['status']=='open_pdf_reading_question' and issue['issues']==x['issues'] and issue['source_sanskrit']==x['source_sanskrit'], 'PDF issue evidence mismatch'
            assert issue['primary_source']==review['primary_source'] and issue['source_pages']==x['source_pages'], 'PDF issue source mismatch'
            unresolved.add(key)
        else:
            assert x['review_status']=='accepted' and not open_issues and row['type']!='translation-review', 'Unresolved PDF verse falsely accepted'
    return allowed,unresolved
