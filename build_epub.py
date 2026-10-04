from pathlib import Path
from lxml import etree, html
from zipfile import ZipFile, ZIP_STORED, ZIP_DEFLATED
from datetime import datetime, timezone
from uuid import uuid4
from html import escape

base = Path(__file__).resolve().parent
source = base / 'book'
doc = html.fromstring((source / 'index.html').read_bytes())
sections = doc.xpath('//main/section')
assert len(sections) == 7
X = 'http://www.w3.org/1999/xhtml'
E = 'http://www.idpf.org/2007/ops'
files = {}
def xhtml(title, children):
    root = etree.Element('{%s}html' % X, nsmap={None:X, 'epub':E}, lang='kn')
    root.set('{http://www.w3.org/XML/1998/namespace}lang', 'kn')
    head = etree.SubElement(root, '{%s}head' % X)
    etree.SubElement(head, '{%s}title' % X).text = title
    etree.SubElement(head, '{%s}meta' % X, charset='utf-8')
    etree.SubElement(head, '{%s}link' % X, rel='stylesheet', href='styles.css', type='text/css')
    body = etree.SubElement(root, '{%s}body' % X)
    for child in children:
        for el in child.iter():
            if isinstance(el.tag, str) and not el.tag.startswith('{'):
                el.tag = '{%s}%s' % (X, el.tag)
            el.attrib.pop('fetchpriority', None)
        body.append(child)
    return etree.tostring(root, encoding='utf-8', xml_declaration=True, doctype='<!DOCTYPE html>')

titles = []
for i, section in enumerate(sections):
    title = 'ಮುಖಪುಟ' if i == 0 else section.xpath('.//h2')[0].text_content()
    titles.append(title)
    name = 'cover.xhtml' if i == 0 else f'page-{i}.xhtml'
    files[name] = xhtml(title, [section])
nav = etree.Element('{%s}nav' % X)
nav.set('{%s}type' % E, 'toc')
etree.SubElement(nav, '{%s}h1' % X).text = 'ವಿಷಯ ಸೂಚಿ'
ol = etree.SubElement(nav, '{%s}ol' % X)
for i, title in enumerate(titles):
    li = etree.SubElement(ol, '{%s}li' % X)
    etree.SubElement(li, '{%s}a' % X, href='cover.xhtml' if i == 0 else f'page-{i}.xhtml').text = title
files['nav.xhtml'] = xhtml('ವಿಷಯ ಸೂಚಿ', [nav])
files['styles.css'] = '''@font-face{font-family:"Tiro Kannada";src:url("assets/TiroKannada-Regular.ttf");font-style:normal;font-weight:400}
body{font-family:"Tiro Kannada",serif;line-height:1.9;margin:1em;color:#3d3027;background:#f4ead6;font-synthesis:none}
.page{break-before:page}.cover{margin:0;padding:0;background:#4c1420;text-align:center}.cover-art img{max-width:100%;height:auto;max-height:95vh;object-fit:contain}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
h2,h3{font-weight:400;color:#8c302b;text-align:center;line-height:1.6}h2{font-size:1.7em}h3{font-size:1.2em}
p{text-align:justify;hyphens:none;overflow-wrap:break-word}.kicker,.ornament,.quote,.colophon,.page-number{text-align:center}.kicker,.ornament,.page-number{color:#8c302b}.quote{margin:1.5em 0;color:#6f342b}.toc div{margin:.6em 0;border-bottom:1px dotted #aa8461}.toc span{margin-right:.7em}.note{border-top:1px solid #b6936b;font-size:.85em}.colophon{margin-top:2em}.colophon strong{font-weight:400}
'''.encode('utf-8')
for name in ['mudgala-front-cover-final-v4.png','TiroKannada-Regular.ttf','TiroKannada-OFL.txt']:
    files['assets/'+name] = (source/'assets'/name).read_bytes()
items = [('nav','nav.xhtml','application/xhtml+xml','nav'),('css','styles.css','text/css',''),('image','assets/mudgala-front-cover-final-v4.png','image/png','cover-image'),('font','assets/TiroKannada-Regular.ttf','font/ttf',''),('licence','assets/TiroKannada-OFL.txt','text/plain','')]
items += [('cover' if i==0 else f'p{i}', 'cover.xhtml' if i==0 else f'page-{i}.xhtml','application/xhtml+xml','') for i in range(7)]
manifest=''.join(f'<item id="{id}" href="{href}" media-type="{mime}"'+(f' properties="{prop}"' if prop else '')+'/>' for id,href,mime,prop in items)
spine=''.join(f'<itemref idref="{id}"/>' for id in ['cover']+[f'p{i}' for i in range(1,7)])
modified=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
files['content.opf']=f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="kn"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="book-id">urn:uuid:{uuid4()}</dc:identifier><dc:title>ಮುದ್ಗಲ ಪುರಾಣ</dc:title><dc:language>kn</dc:language><dc:description>ಕನ್ನಡ ಪುಸ್ತಕ ಮಾದರಿ. Sample text, not a verified Purana translation.</dc:description><meta property="dcterms:modified">{modified}</meta><meta property="rendition:layout">reflowable</meta></metadata><manifest>{manifest}</manifest><spine page-progression-direction="ltr">{spine}</spine></package>'''.encode('utf-8')
files['META-INF/container.xml']=b'''<?xml version="1.0" encoding="utf-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'''
out=base/'dist'/'mudgala_purana.epub'
out.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(out,'w') as z:
    z.writestr('mimetype',b'application/epub+zip',compress_type=ZIP_STORED)
    for name,data in files.items():
        z.writestr(name,data,compress_type=ZIP_DEFLATED)
with ZipFile(out) as z:
    assert z.infolist()[0].filename=='mimetype' and z.infolist()[0].compress_type==ZIP_STORED
    assert z.read('mimetype')==b'application/epub+zip'
    assert z.testzip() is None
    for name in z.namelist():
        if name.endswith(('.xhtml','.xml','.opf')):
            etree.fromstring(z.read(name))
    for _,href,_,_ in items:
        assert href in z.namelist()
    for i,section in enumerate(sections):
        name='cover.xhtml' if i==0 else f'page-{i}.xhtml'
        actual=etree.fromstring(z.read(name))
        assert ''.join(section.itertext()) == ''.join(actual.find('{%s}body'%X)[0].itertext())
print(f'{out}: XML, ZIP, manifest, seven reading sections and content preservation checks passed.')
