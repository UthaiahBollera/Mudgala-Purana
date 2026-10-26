"""Derive per-khanda EPUB and print sources from the canonical generated reader."""
from pathlib import Path
import json,hashlib,html,zipfile,xml.etree.ElementTree as E,os,shutil
site=Path(__file__).resolve().parents[1];data=json.loads((site/'.generated/book.json').read_text());target=site/'public/book';downloads=site/'downloads';downloads.mkdir(exist_ok=True)
fingerprint=hashlib.sha256((site/'.generated/book.json').read_bytes()+(site.parent/'styles/book.css').read_bytes()+(site.parent/'styles/print.css').read_bytes()+(site/'scripts/print.mjs').read_bytes()).hexdigest()
base=target/'mudgala-purana.epub';source=zipfile.ZipFile(base);ns={'o':'http://www.idpf.org/2007/opf'}
editions=[]
available=sorted({c['khanda'] for c in data['chapters']})
for key,k,label in [('available',None,'ಲಭ್ಯ ಭಾಗಗಳ ಸಂಯುಕ್ತ ಆವೃತ್ತಿ')]+[(f'khanda-{k}',k,f'ಖಂಡ {k} · ಲಭ್ಯ ಭಾಗಗಳು') for k in available]:
 chapters=[c for c in data['chapters'] if k is None or c['khanda']==k];included={c['id'] for c in chapters};slug='mudgala-purana-'+key+'-partial';title=data['title']+' · '+label;desc='Partial edition: '+('; '.join(f"Khanda {n} chapters "+', '.join(str(c['number']) for c in chapters if c['khanda']==n) for n in sorted({c['khanda'] for c in chapters})))+'. '+('Reading draft; source caveats retained; meaning 7.37 pending; not expert-reviewed. ' if any(c['khanda']==2 for c in chapters) else '')+str(sum(c['count'] for c in chapters))+' numbered verse/meaning pairs. Not a complete book.'
 # Full EPUB compatibility URL stays available; subsets retain separate chapter XHTML.
 root=E.fromstring(source.read('EPUB/package.opf'));manifest=root.find('o:manifest',ns);spine=root.find('o:spine',ns);remove=set()
 for item in list(manifest):
  if item.get('href','').startswith('chapters/') and item.get('id') not in included or k==2 and item.get('href','').startswith('frontmatter/'):
   remove.add('EPUB/'+item.get('href'));manifest.remove(item)
 valid={i.get('id') for i in manifest}
 for item in list(spine):
  if item.get('idref') not in valid:spine.remove(item)
 root.find('o:metadata/{http://purl.org/dc/elements/1.1/}title',ns).text=title
 E.SubElement(root.find('o:metadata',ns),'{http://purl.org/dc/elements/1.1/}description').text=desc
 root.find('o:metadata/{http://purl.org/dc/elements/1.1/}identifier',ns).text='urn:mudgala-purana:'+key+':'+fingerprint[:16]
 E.register_namespace('',ns['o']);E.register_namespace('dc','http://purl.org/dc/elements/1.1/')
 with zipfile.ZipFile(target/(slug+'.epub'),'w',compression=zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','application/epub+zip',compress_type=zipfile.ZIP_STORED)
  for name in source.namelist():
   if name=='mimetype' or name in remove:continue
   value=source.read(name)
   if name=='EPUB/package.opf':value=E.tostring(root,encoding='utf-8',xml_declaration=True)
   if name=='EPUB/nav.xhtml':
    nav=E.fromstring(value);n={'h':'http://www.w3.org/1999/xhtml'}
    for ol in nav.findall('.//h:ol',n):
     for li in list(ol):
      a=li.find('h:a',n)
      if a is not None and 'EPUB/'+a.get('href','') in remove:ol.remove(li)
    E.register_namespace('','http://www.w3.org/1999/xhtml');value=E.tostring(nav,encoding='utf-8',xml_declaration=True)
   z.writestr(name,value)
 # Print uses the same per-chapter HTML, preserving exact verse/meaning associations.
 toc='<nav aria-label="ಪರಿವಿಡಿ"><h2>ಪರಿವಿಡಿ</h2><ol>'+''.join(f'<li><a href="#{c["id"]}">ಖಂಡ {c["khanda"]} · {html.escape(c["title"])}</a></li>' for c in chapters)+'</ol></nav>'
 content=''.join(c['html'] for c in chapters)
 if k!=2:content=''.join(f['html'] for f in data['frontmatter'])+content
 content=content.replace('/book/',target.as_uri()+'/')
 css=(target/'styles/book.css').as_uri();cover=(target/data['cover'].removeprefix('/book/')).as_uri()
 printcss=(site.parent/'styles/print.css').read_text()
 doc=f'<!doctype html><html lang="kn"><meta charset="utf-8"><title>{html.escape(title)}</title><link rel="stylesheet" href="{css}"><style>{printcss}</style><body><header class="print-cover"><img src="{cover}" alt="ಅನುಮೋದಿತ ಮುಖಪುಟ"><h1 class="print-title">{html.escape(title)}</h1><p>ಲಭ್ಯ ಭಾಗಗಳು ಮಾತ್ರ · ಪೂರ್ಣ ಪುಸ್ತಕವಲ್ಲ</p><p lang="en">{html.escape(desc)}</p></header><section class="print-toc">{toc}</section><main>{content}</main></body></html>'
 (site/'.generated'/('print-'+key+'.html')).write_text(doc)
 editions.append({'key':key,'khanda':k,'title':title,'coverage':desc,'slug':slug,'chapters':[c['id'] for c in chapters]})
(site/'.generated/editions.json').write_text(json.dumps({'fingerprint':fingerprint,'editions':editions},ensure_ascii=False,indent=2))
record=downloads/'manifest.json'
if os.environ.get('MUDGALA_REBUILD_PDF')!='1':
 if not record.exists():raise SystemExit('Run npm run downloads to create source-matched PDF editions before building.')
 manifest=json.loads(record.read_text());assert manifest['fingerprint']==fingerprint,'PDF content is stale: run npm run downloads before building'
 for e in editions:
  p=downloads/(e['slug']+'.pdf');assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest['files'][p.name];shutil.copy2(p,target/p.name)
