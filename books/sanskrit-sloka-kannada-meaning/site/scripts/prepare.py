"""Derive Next.js pages from the same reviewed sources as web and EPUB."""
from pathlib import Path
from ornamental import canonical_chapter
import importlib.util,json,shutil,xml.etree.ElementTree as E
site=Path(__file__).resolve().parents[1];book=site.parent
spec=importlib.util.spec_from_file_location('book_build',book/'build.py');build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build);build.build()
m=json.loads((book/'book.json').read_text());data={'title':m['title'],'modified':m['modified'],'cover':'/book/'+m['cover'],'chapters':[],'frontmatter':[]};ns={'h':'http://www.w3.org/1999/xhtml'}
def body(c):
 root=E.fromstring(build.reader_document(c));main=root.find('h:body/h:main',ns);assert main is not None
 for e in main.iter():
  if e.tag.endswith('}img'):e.set('loading','lazy')
  for attr in ('src','href'):
   v=e.get(attr)
   if v and not v.startswith(('#','http:','https:','data:')):
    target=(book/c['file']).parent.joinpath(v).resolve();e.set(attr,'/book/'+target.relative_to(book).as_posix())

 for e in list(main.iter()):
  if e.get('class')=='unit sloka-entry':
   e.set('tabindex','-1');num=e.find('h:div[@class="num"]',ns)
   if num is not None:
    label=num.text;num.text=None;a=E.SubElement(num,'{'+ns['h']+'}a',{'href':'#'+e.get('id'),'aria-label':'ಶ್ಲೋಕ '+label+' ನೇರ ಕೊಂಡಿ'});a.text=label
 main.tag='{'+ns['h']+'}article'
 E.register_namespace('',ns['h']);return E.tostring(main,encoding='unicode').replace(' xmlns="http://www.w3.org/1999/xhtml"','')
for c in m['chapters']:
 if c.get('include',True):data['chapters'].append({'chapterComplete':c['coverage'].get('chapter_complete',True),'id':c['id'],'khanda':c['khanda'],'number':c['number'],'title':c['title'],'slug':str(c['number']),'count':c['coverage']['last_verse'],'groups':len(c['reading_groups']),'html':body(c)})
for c in m['frontmatter']:data['frontmatter'].append({'title':c['title'],'html':body(c)})
baseline=[c for c in data['chapters'] if c['khanda']==1]
assert len(baseline)==18 and sum(c['count'] for c in baseline)==985
assert len({c['id'] for c in data['chapters']})==len(data['chapters'])
(site/'.generated').mkdir(exist_ok=True);(site/'.generated/book.json').write_text(json.dumps(data,ensure_ascii=False))
target=site/'public/book'
if target.exists():shutil.rmtree(target)
target.mkdir(parents=True,exist_ok=True)
for folder in ['assets','styles']:shutil.copytree(book/folder,target/folder,dirs_exist_ok=True)
shutil.copytree(site/'ornamental-assets',target/'assets/ornamental')
shutil.copy2(book/'dist/mudgala-preview.epub',target/'mudgala-purana.epub');print(f"Prepared {len(data['chapters'])} chapters/{sum(c['count'] for c in data['chapters'])} pairs; Khanda1 baseline preserved.")

search=[]
for c in data['chapters']:
 root=E.fromstring(c['html'])
 for u in root.findall('.//div[@class="unit sloka-entry"]'):
  id=u.get('id');meaning=root.find('.//div[@data-meaning-for="'+id+'"]')
  search.append({'id':id,'khanda':c['khanda'],'chapter':c['number'],'verse':int(id.rsplit('-v',1)[1]),'url':f"/kn/mudgala-purana/khanda-{c['khanda']}/{c['slug']}/#{id}",'sanskrit':' '.join(''.join(u.find('.//p').itertext()).split()),'meaning':' '.join(''.join(meaning.find('.//div[@class="entry-text"]').itertext()).split())})
(target/'search-index.json').write_text(json.dumps(search,ensure_ascii=False))

import runpy
runpy.run_path(str(site/'scripts/editions.py'))

# The canonical PDF/EPUB fingerprint and search index are derived above from
# the original source presentation. Only the website gets paired styling.
paired={c['id']:canonical_chapter(c['html']) for c in data['chapters'] if c['khanda']==1}
(site/'.generated/book-ornamental.json').write_text(json.dumps(paired,ensure_ascii=False))

runpy.run_path(str(site/'scripts/prepare-review.py'), run_name='__main__')

# Keep this full Khanda 1 reading copy separate from source-matched canonical downloads.
import hashlib
khanda1_print = site/'downloads'/'mudgala-purana-khanda-1-kannada.pdf'
khanda1_print_sha256 = '41a710e1679535ac3a1aa5807752ddc056313d34d944ede0b148b6d63749c748'
if hashlib.sha256(khanda1_print.read_bytes()).hexdigest() != khanda1_print_sha256:
 raise SystemExit('Khanda 1 ornamental print copy does not match the validated release.')
shutil.copy2(khanda1_print, target/khanda1_print.name)
