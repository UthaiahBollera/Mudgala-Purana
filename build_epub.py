"""Package the current Kannada HTML edition as an EPUB 3 publication."""
from pathlib import Path
from lxml import etree, html
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from datetime import datetime, timezone
from uuid import uuid5, NAMESPACE_URL
import mimetypes
import json
import re

BASE=Path(__file__).resolve().parent
SOURCE=BASE/'book'
doc=html.fromstring((SOURCE/'index.html').read_bytes())
sections=doc.xpath('//main/section')
assert sections and 'cover' in sections[0].get('class','')
X='http://www.w3.org/1999/xhtml';E='http://www.idpf.org/2007/ops';P='http://www.idpf.org/2007/opf'
files={};items=[]
def document(title,children):
    root=etree.Element('{%s}html'%X,nsmap={None:X,'epub':E},lang='kn')
    root.set('{http://www.w3.org/XML/1998/namespace}lang','kn')
    head=etree.SubElement(root,'{%s}head'%X)
    etree.SubElement(head,'{%s}title'%X).text=title
    etree.SubElement(head,'{%s}meta'%X,charset='utf-8')
    etree.SubElement(head,'{%s}link'%X,rel='stylesheet',href='styles.css',type='text/css')
    body=etree.SubElement(root,'{%s}body'%X)
    for child in children:
        for el in child.iter():
            if isinstance(el.tag,str) and not el.tag.startswith('{'):el.tag='{%s}%s'%(X,el.tag)
        body.append(child)
    return etree.tostring(root,encoding='utf-8',xml_declaration=True,doctype='<!DOCTYPE html>')
nav=etree.Element('{%s}nav'%X);nav.set('{%s}type'%E,'toc')
etree.SubElement(nav,'{%s}h1'%X).text='ವಿಷಯ ಸೂಚಿ'
ol=etree.SubElement(nav,'{%s}ol'%X)
# HTML fragment links must cross EPUB spine documents after splitting.
id_documents = {el.get('id'): section.get('id')+'.xhtml'
                for section in sections for el in section.iter() if el.get('id')}
for section in sections:
    for anchor in section.xpath('.//a[starts-with(@href, "#")]'):
        target = anchor.get('href')[1:]
        assert target in id_documents, ('Unknown internal link', target)
        anchor.set('href', id_documents[target]+'#'+target)
for i,section in enumerate(sections):
    id=section.get('id');name=id+'.xhtml';title=section.get('data-title') or 'ಮುದ್ಗಲ ಪುರಾಣ'
    files[name]=document(title,[section]);items.append((f's{i}',name,'application/xhtml+xml',''))
    if not id.startswith(('chapter-','contents-','reference-chapter-')) or id.endswith('-1'):
        li=etree.SubElement(ol,'{%s}li'%X)
        label=section.get('data-toc-label') or title
        etree.SubElement(li,'{%s}a'%X,href=name).text=label
files['nav.xhtml']=document('ವಿಷಯ ಸೂಚಿ',[nav]);items.append(('nav','nav.xhtml','application/xhtml+xml','nav'))
files['styles.css']='''@font-face{font-family:"Tiro Kannada";src:url("assets/TiroKannada-Regular.ttf") format("truetype");font-weight:400;font-style:normal}
body{font-family:"Tiro Kannada",serif;font-synthesis:none;margin:1em;line-height:1.85;color:#3d3027;background:#f4ead6}.cover{text-align:center;background:#4c1420}.cover-art img{width:100%;height:auto;max-height:95vh;object-fit:contain}h2,h3{font-weight:400;text-align:center;color:#8c302b;line-height:1.6}h2{font-size:1.7em}h3{font-size:1.25em}
p{text-align:justify;hyphens:none;overflow-wrap:break-word}.mantra{text-align:center;color:#6f342b;line-height:2;break-inside:avoid}.caption,.colophon{text-align:center}.caption{color:#8c302b}.colophon{font-size:.85em;border-top:1px solid #b6936b;margin-top:1.5em;padding-top:1em}figure{margin:1.5em 0}figure img{max-width:100%;height:auto}.page-number{display:none}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}table{width:100%;border-collapse:collapse;font-size:.85em;line-height:1.8}th{font-weight:400;color:#8c302b;text-align:left}td,th{padding:.5em .3em;vertical-align:top;border-bottom:1px solid #b6936b55}td:first-child{width:2em}td:last-child{white-space:nowrap;text-align:right}.khanda th{text-align:center}
'''.encode('utf-8');items.append(('css','styles.css','text/css',''))
needed={'assets/TiroKannada-Regular.ttf','assets/TiroKannada-OFL.txt'}
needed.update(el.get('src') for s in sections for el in s.iter() if el.tag=='{%s}img'%X)
for n,name in enumerate(sorted(needed)):
    files[name]=(SOURCE/name).read_bytes();mime=mimetypes.guess_type(name)[0] or 'application/octet-stream'
    if name.endswith('.ttf'):mime='font/ttf'
    prop='cover-image' if name.endswith('mudgala-front-cover-final-v4.png') else ''
    items.append((f'a{n}',name,mime,prop))
root=etree.Element('{%s}package'%P,nsmap={None:P},version='3.0')
root.set('unique-identifier','book-id');root.set('{http://www.w3.org/XML/1998/namespace}lang','kn')
metadata=etree.SubElement(root,'{%s}metadata'%P,nsmap={'dc':'http://purl.org/dc/elements/1.1/'})
def dc(tag,text,id=None):
    node=etree.SubElement(metadata,'{http://purl.org/dc/elements/1.1/}'+tag);node.text=text
    if id:node.set('id',id)
dc('identifier','urn:uuid:'+str(uuid5(NAMESPACE_URL,'https://github.com/UthaiahBollera/Mudgala-Purana')),'book-id')
source_description = '1 TO 25(1).pdf; all 20 pages. 26 TO 55(2).pdf; all 30 pages. 55 TO 76(1).pdf; all 21 pages. 77 TO 98(1).pdf; all 22 pages. 99 TO 118(1).pdf; all 20 pages. 119 TO 138(1).pdf; all 20 pages.'
manifest_path = BASE/'translation/batch-manifest.json'
if manifest_path.exists():
    manifest_data = json.loads(manifest_path.read_text(encoding='utf-8'))
    for batch in manifest_data['batches']:
        if batch.get('source_kind') == 'google_books':
            source_description += (f' Google Books {batch["book_id"]}; '
                                   f'page IDs {", ".join(page["id"] for page in batch["source_pages"])}.')
        elif batch.get('source_kind') == 'local_pdf':
            source_description += f' Primary scanned PDF {batch["source_pdf"]}; SHA-256 {batch["source_sha256"]}; PDF pages '+', '.join(str(p['pdf_page']) for p in batch['source_pages'])+'. Google Books is a cross-reference; OCR is a transcription aid.'
        elif batch.get('source_kind') == 'reviewed_base_correction':
            source_description += ' Reviewed token-only base-edition correction; historical source mapping and edition variants retained. Evidence: '+batch['review_file']+'.'
        elif batch.get('source_kind') == 'original_png_archive':
            source_description += ' Additional original PNG archive '+batch['source_archive']['filename']+'; SHA-256 '+batch['source_archive']['sha256']+'; members '+', '.join(p['member'] for p in batch['source_pages'])+'. Frozen candidates and independent review retained; lexical holds remain explicit.'
        else:
            start, end = batch['pdf_page_range']
            source_description += f' {batch["source_pdf"]}; PDF pages {start}–{end}.'
from reference_only import load as load_reference_only
if load_reference_only(BASE)['chapters']:
    source_description += ' Additional chapters are provisional Kannada based only on uploaded Sanskrit OCR; editorial locators are not verified verse numbers. Partial chapter25 Argon evidence is retained separately; no continuation scans or Argon are claimed.'
dc('title','ಮುದ್ಗಲ ಪುರಾಣ');dc('language','kn');dc('source',source_description)
dc('description','Kannada reading draft. Narrative is translated; devotional passages are transliterated without translation. Editorial uncertainties and batch boundaries are recorded outside the reading text.')
for prop,value in [('dcterms:modified',datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')),('rendition:layout','reflowable')]:etree.SubElement(metadata,'{%s}meta'%P,property=prop).text=value
manifest=etree.SubElement(root,'{%s}manifest'%P)
for id,href,mime,prop in items:
    item=etree.SubElement(manifest,'{%s}item'%P,id=id,href=href);item.set('media-type',mime)
    if prop:item.set('properties',prop)
spine=etree.SubElement(root,'{%s}spine'%P);spine.set('page-progression-direction','ltr')
for i in range(len(sections)):etree.SubElement(spine,'{%s}itemref'%P,idref=f's{i}')
files['content.opf']=etree.tostring(root,encoding='utf-8',xml_declaration=True)
files['META-INF/container.xml']=b'<?xml version="1.0" encoding="utf-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'
out=BASE/'dist'/'mudgala_purana.epub';out.parent.mkdir(exist_ok=True)
with ZipFile(out,'w') as z:
    z.writestr('mimetype',b'application/epub+zip',compress_type=ZIP_STORED)
    for name,data in files.items():z.writestr(name,data,compress_type=ZIP_DEFLATED)
with ZipFile(out) as z:
    assert z.infolist()[0].filename=='mimetype' and z.infolist()[0].compress_type==ZIP_STORED
    assert z.read('mimetype')==b'application/epub+zip' and z.testzip() is None
    for name in z.namelist():
        if name.endswith(('.xhtml','.opf','.xml')):etree.fromstring(z.read(name))
    for _,href,_,_ in items:assert href in z.namelist()
    for section in sections:
        parsed=etree.fromstring(z.read(section.get('id')+'.xhtml'))
        assert ''.join(section.itertext())==''.join(parsed.find('{%s}body'%X)[0].itertext())
        for img in parsed.findall('.//{%s}img'%X):assert img.get('src') in z.namelist()
print(f'EPUB checks passed: {len(sections)} spine documents, embedded assets, XML, ZIP, and unchanged Kannada text.')
