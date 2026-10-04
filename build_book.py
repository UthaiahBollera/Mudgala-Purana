"""Generate the Kannada reading edition from source-mapped translation data."""
from pathlib import Path
import csv
import base64
import re
import json
from html import escape

BASE = Path(__file__).resolve().parent
BOOK = BASE / 'book'
ASSETS = BOOK / 'assets'
DATA = BASE / 'translation'
DIST = BASE / 'dist'
def rows(name):
    with (DATA / (name + '.tsv')).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))
toc, front, narrative = rows('contents'), rows('frontmatter'), rows('narrative')
verse_map={(int(r['chapter']),int(r['verse'])):r for r in narrative}
for batch in sorted(DATA.glob('batch-*.tsv')):
    with batch.open(encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f,delimiter='\t'):
            verse_map[(int(r['chapter']),int(r['verse']))]=r
narrative=[verse_map[k] for k in sorted(verse_map)]
assert len(toc) == 371
for chapter in sorted({int(r['chapter']) for r in narrative}):
    verses=[int(r['verse']) for r in narrative if int(r['chapter'])==chapter]
    assert verses==list(range(1,max(verses)+1)), (chapter,verses)
KN = str.maketrans('0123456789', '೦೧೨೩೪೫೬೭೮೯')
def kn(s): return str(s).translate(KN)
def e(s): return escape(str(s), quote=True)
def section(id, title, body, source='', kind='', hidden_title=False):
    heading = f'<h2'+(' class="sr-only"' if hidden_title else '')+f'>{e(title)}</h2>'
    return f'<section class="page {kind}" id="{id}" data-source-pages="{e(source)}" data-title="{e(title)}">{heading}{body}<div class="page-number" aria-hidden="true"></div></section>'
pages = []
cover_alt='ಮುದ್ಗಲ ಪುರಾಣ: ಮರೂನ್ ಮತ್ತು ಬಂಗಾರದ ಮುಖಪುಟದಲ್ಲಿ ಗಣೇಶನ ಚಿತ್ರ'
pages.append(f'<section class="page cover" id="cover" data-title="ಮುಖಪುಟ"><h1 class="sr-only">ಮುದ್ಗಲ ಪುರಾಣ</h1><div class="cover-art"><img src="assets/mudgala-front-cover-final-v4.png" width="1055" height="1491" alt="{cover_alt}" /></div></section>')
def front_page(n):
    body=''
    for r in front:
        if int(r['source_page'])!=n: continue
        text=re.sub(r'\s*\[[^\]]*\]', '', r['text'])
        if r['type']=='image':
            body+=f'<figure><img src="assets/{e(text)}" alt="ಮೂಲಗ್ರಂಥದಲ್ಲಿನ ಗಣೇಶನ ಚಿತ್ರ" /></figure>'
        elif r['type']=='mantra':
            body+=f'<p class="mantra" lang="sa-Knda" data-treatment="transliteration">{e(text)}</p>'
        else:
            body+=f'<p class="caption">{e(text)}</p>'
    titles={1:'ಶ್ರೀ ಮುದ್ಗಲ ಪುರಾಣ',2:'ಮಂಗಳವಚನಗಳು',9:'ಪ್ರಥಮ ಖಂಡ',10:'ಶ್ರೀಮಯೂರೇಶ್ವರ',11:'ಶ್ರೀಮಯೂರೇಶ್ವರ',12:'ಶ್ರೀವಕ್ರತುಂಡ ಮಯೂರೇಶ್ವರ',13:'ಶ್ರೀಅಷ್ಟವಿನಾಯಕ'}
    return section(f'source-{n:02}',titles[n],body,str(n),'illustrated' if n in [1,10,11,12,13] else 'frontmatter',True)
pages.extend([front_page(1),front_page(2)])
for src in range(3,9):
    entries=[r for r in toc if int(r['source_page'])==src]
    # Small physical groups, with automatic print continuation if a title wraps.
    for part,start in enumerate(range(0,len(entries),16),1):
        chunk=entries[start:start+16]
        body='<table class="contents"><thead><tr><th>ಅಧ್ಯಾಯ</th><th>ವಿಷಯ</th><th>ಮೂಲಪುಟ</th></tr></thead><tbody>'
        last=None
        for r in chunk:
            khanda=r['khanda']
            if khanda!=last:
                if khanda!='ಪೂರ್ವ ಖಂಡ':
                    body+=f'<tr class="khanda"><th colspan="3">{e("ಖಂಡ "+kn(khanda))}</th></tr>'
                last=khanda
            body+=f'<tr data-source-page="{src}" data-source-chapter="{r["chapter"]}" data-khanda="{e(khanda)}"><td>{kn(r["chapter"])}</td><td>{e(r["title"])}</td><td>{e(kn(r["original_pages"]))}</td></tr>'
        body+='</tbody></table>'
        if src==8 and start+16>=len(entries):
            for r in front:
                if r['source_page']=='8':body+=f'<p class="mantra" lang="sa-Knda" data-treatment="transliteration">{e(r["text"])}</p>'
        pages.append(section(f'contents-{src:02}-{part}','ವಿಷಯ ಸೂಚಿ',body,str(src),'contents-page'))
pages.extend(front_page(n) for n in range(9,14))
chapter_names={1:'ಶೌನಕ ಮತ್ತು ಸೂತನ ಸಂವಾದ',2:'ದಕ್ಷ ಮತ್ತು ನಂದಿಯ ವಿವಾದ',3:'ಪಾರ್ವತಿಯ ದೇಹತ್ಯಾಗ',4:'ದಕ್ಷನ ಚರಿತ್ರೆ',5:'ಪಾರ್ವತಿ ಮತ್ತು ಶಿವರ ವಿಚಾರ',6:'ಪ್ರಕೃತಿ ಮತ್ತು ಪುರುಷರಿಗೆ ವರಪ್ರದಾನ',7:'ತತ್ತ್ವಗಳು ಮಾಡಿದ ಸ್ತುತಿಯ ವರ್ಣನೆ',8:'ಗುಣೇಶನಿಗೆ ವರಪ್ರದಾನ',9:'ಪ್ರಕೃತಿಯ ವರ್ಣನೆ',10:'ನಾನಾ ಬ್ರಹ್ಮಾಂಡಗಳ ವರ್ಣನೆ',11:'ಪಂಚದೇವತೆಗಳಿಗೆ ವರಪ್ರದಾನ',12:'ಮಹಾವಿಷ್ಣುವಿನ ವಿವಾದ',13:'ಪಂಚದೇವತೆಗಳ ವಿವಾದ',14:'ಗಣೇಶನ ಉದ್ಭವ',15:'ಗಣೇಶನ ಪ್ರಸನ್ನಭಾವ'}
chapter_ord={1:'ಪ್ರಥಮ',2:'ದ್ವಿತೀಯ',3:'ತೃತೀಯ',4:'ಚತುರ್ಥ',5:'ಪಂಚಮ',6:'ಷಷ್ಠ',7:'ಸಪ್ತಮ',8:'ಅಷ್ಟಮ',9:'ನವಮ',10:'ದಶಮ',11:'ಏಕಾದಶ',12:'ದ್ವಾದಶ',13:'ತ್ರಯೋದಶ',14:'ಚತುರ್ದಶ',15:'ಪಂಚದಶ'}
chapter_names.update({16:'ಗಾಣೇಶಗೀತೆಯ ಸಾರಕಥನ',17:'ಶಿವ ಮತ್ತು ಶಕ್ತಿಯ ಸಂವಾದದ ಸಮಾಪ್ತಿ',18:'ಮುದ್ಗಲ ಮತ್ತು ದೇವದೂತನ ಸಂವಾದ',19:'ಅಂಗಿರಸ ಮತ್ತು ಮುದ್ಗಲನ ಸಂವಾದ'})
chapter_ord.update({16:'ಷೋಡಶ',17:'ಸಪ್ತದಶ',18:'ಅಷ್ಟಾದಶ',19:'ಏಕೋನವಿಂಶ',20:'ವಿಂಶ',21:'ಏಕವಿಂಶ',22:'ದ್ವಾವಿಂಶ',23:'ತ್ರಯೋವಿಂಶ',24:'ಚತುರ್ವಿಂಶ',25:'ಪಂಚವಿಂಶ',26:'ಷಡ್ವಿಂಶ',27:'ಸಪ್ತವಿಂಶ',28:'ಅಷ್ಟಾವಿಂಶ',29:'ಏಕೋನತ್ರಿಂಶ',30:'ತ್ರಿಂಶ'})
chapter_names.update({20:'ಗಣೇಶ ಮತ್ತು ಮುದ್ಗಲನ ಸಮಾಗಮ',21:'ಗಣೇಶಸ್ತೋತ್ರದ ಸಮರ್ಪಣೆ',22:'ಮುದ್ಗಲನಿಗೆ ವರಪ್ರದಾನ',23:'ಮತ್ಸರಾಸುರನ ತಪಸ್ಸಿನ ವರ್ಣನೆ'})
chapter_names.update({24:'ಮತ್ಸರಾಸುರನ ಗಮನ'})
chapter_names.update({25:'ಮತ್ಸರಾಸುರನ ಸೇನೆಯ ವರ್ಣನೆ',26:'ಪಾತಾಳವಿಜಯ',27:'ಮತ್ಸರಾಸುರನ ವಿಜಯ ಮತ್ತು ಇಂದ್ರನ ಬಂಧನ',28:'ಮತ್ಸರಾಸುರನ ಚೇಷ್ಟೆಗಳ ಕಥನ',29:'ಶಿವ ಮತ್ತು ಮತ್ಸರಾಸುರನ ಸಮಾಗಮ'})
chapter_names.update({30:'ಶಿವನ ಪರಾಜಯ',31:'ದತ್ತಾತ್ರೇಯನ ಸಮಾಗಮ',32:'ವಕ್ರತುಂಡನ ಉದ್ಭವ',33:'ಮತ್ಸರಾಸುರನ ಚಿಂತನೆ',34:'ದೇವಾಸುರರ ಯುದ್ಧಾರಂಭ',35:'ಶಿವನ ವಿಜಯ'})
chapter_ord.update({31:'ಏಕತ್ರಿಂಶ',32:'ದ್ವಾತ್ರಿಂಶ',33:'ತ್ರಯಸ್ತ್ರಿಂಶ',34:'ಚತುಸ್ತ್ರಿಂಶ',35:'ಪಂಚತ್ರಿಂಶ',36:'ಷಟ್ತ್ರಿಂಶ',37:'ಸಪ್ತತ್ರಿಂಶ',38:'ಅಷ್ಟಾತ್ರಿಂಶ',39:'ಏಕೋನಚತ್ವಾರಿಂಶ',40:'ಚತ್ವಾರಿಂಶ'})
completed_chapters=set(json.loads((DATA/'completed-chapters.json').read_text(encoding='utf-8')))
chapters=sorted({int(r['chapter']) for r in narrative})
for chapter in chapters:
    entries=[r for r in narrative if int(r['chapter'])==chapter]
    groups=[]; group=[]; length=0
    for r in entries:
        size=len(r['text'])
        if group and (length+size>1950 or len(group)>=6):
            groups.append(group);group=[];length=0
        group.append(r);length+=size
    if group: groups.append(group)
    for part,chunk in enumerate(groups,1):
        body=''
        if part==1:
            if chapter in chapter_names:body+=f'<h3>{e(chapter_names[chapter])}</h3>'
            if chapter==1:
                body+='<p class="mantra" lang="sa-Knda" data-treatment="transliteration">॥ ಓಂ ನಮಃ ಶ್ರೀಸ್ವಾನಂದೇಶಗಣೇಶಾಯ ಪೂರ್ಣಯೋಗಾತ್ಮನೇ ॥</p>'
                body+='<p class="caption">ಶ್ರೀಮುದ್ಗಲಪುರಾಣದ ಆರಂಭ</p>'
            body+='<p class="mantra" lang="sa-Knda" data-treatment="transliteration">॥ ಶ್ರೀಗಣೇಶಾಯ ನಮಃ ॥</p>'
        for r in chunk:
            mantra=r['type']=='mantra'
            reading_text=re.sub(r'\s*\[[^\]]*\]', '', r['text'])
            body+=f'<p id="ch{chapter}-v{r["verse"]}" class="'+('mantra' if mantra else 'narrative')+f'" lang="'+('sa-Knda' if mantra else 'kn')+f'" data-source-pages="{r["source_pages"]}" data-treatment="{r["type"]}">{e(reading_text)}</p>'
        # A colophon is generated only where the supplied scans show one.
        if part==len(groups) and chapter in completed_chapters:
            body+=f'<p class="colophon">ಓಂ. ಶ್ರೀಮುದ್ಗಲ ಮಹಾಪುರಾಣವೆಂಬ ಪುರಾಣೋಪನಿಷತ್ತಿನ ಪ್ರಥಮ ಖಂಡವಾದ ವಕ್ರತುಂಡಚರಿತ್ರೆಯಲ್ಲಿ “{e(chapter_names[chapter])}” ಎಂಬ {chapter_ord[chapter]} ಅಧ್ಯಾಯವು ಮುಗಿಯಿತು.</p>'
        source_pages=sorted(set(p for r in chunk for p in r['source_pages'].split(',')),key=int)
        pages.append(section(f'chapter-{chapter}-{part}',chapter_ord[chapter]+' ಅಧ್ಯಾಯ',body,','.join(source_pages),'chapter',part>1))
css='''@font-face{font-family:"Tiro Kannada";src:url("assets/TiroKannada-Regular.ttf") format("truetype");font-weight:400;font-style:normal;font-display:swap}
:root{--paper:#f4ead6;--ink:#3d3027;--red:#8c302b}*{box-sizing:border-box}body{margin:0;background:#30201e;color:var(--ink);font-family:"Tiro Kannada",serif;font-synthesis:none}
.book{counter-reset:leaf;display:grid;gap:32px;padding:28px 18px 50px}.page{counter-increment:leaf;position:relative;width:min(740px,100%);min-height:1046px;margin:auto;background:var(--paper);padding:92px 64px 90px;box-shadow:0 16px 40px #140b0b88}.page::before{content:"ಶ್ರೀ ಮುದ್ಗಲ ಪುರಾಣ";position:absolute;left:64px;right:64px;top:32px;text-align:center;border-bottom:1px solid #9c704475;padding-bottom:12px;font-size:12px;color:#624939}.page-number{position:absolute;bottom:32px;left:0;right:0;text-align:center;color:var(--red);font-size:14px}.page-number::after{content:counter(leaf,kannada)}
.cover{counter-increment:none;width:min(620px,100%);min-height:0;padding:0;aspect-ratio:210/297;background:#4c1420;box-shadow:none}.cover::before{display:none}.cover-art{position:absolute;inset:0}.cover-art img{display:block;width:100%;height:100%;object-fit:contain}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}h2,h3{font-weight:400;text-align:center;color:var(--red);line-height:1.6}h2{font-size:29px;margin:0 0 22px}h3{font-size:21px;margin:0 0 26px}p{font-size:18px;line-height:1.85;text-align:justify;margin:0 0 18px;hyphens:none;overflow-wrap:break-word;orphans:3;widows:3}.mantra{text-align:center;color:#6f342b;line-height:2;break-inside:avoid}.caption{text-align:center;color:var(--red)}.colophon{font-size:14px;text-align:center;margin-top:24px;border-top:1px solid #b6936b;padding-top:16px}figure{margin:24px 0}figure img{display:block;width:100%;height:auto;max-height:650px;object-fit:contain}.frontmatter{display:flex;flex-direction:column;justify-content:center}.frontmatter p{margin:22px 0}
.contents{width:100%;border-collapse:collapse;font-size:14px;line-height:1.8}.contents th{font-weight:400;color:var(--red);text-align:left}.contents td,.contents th{padding:7px 5px;border-bottom:1px solid #b6936b55;vertical-align:top}.contents td:first-child{width:42px}.contents td:last-child{width:85px;white-space:nowrap;text-align:right}.contents th:last-child{text-align:right}.contents .khanda th{text-align:center;padding:13px 0 8px;background:#e9dac133}.contents tr{break-inside:avoid}
@media(max-width:600px){.book{padding:16px 9px 32px;gap:22px}.page{min-height:850px;padding:75px 26px 70px}.page::before{left:26px;right:26px;top:25px}.cover{min-height:0;padding:0}p{font-size:16px}h2{font-size:25px}h3{font-size:19px}.contents{font-size:12px}.contents td:last-child{width:60px}.contents td:first-child{width:30px}}
@page{size:A4 portrait;margin:20mm 20mm 22mm;background:#f4ead6;@top-center{content:"ಶ್ರೀ ಮುದ್ಗಲ ಪುರಾಣ";font-family:"Tiro Kannada";font-size:9pt;color:#624939}@bottom-center{content:counter(page,kannada);font-family:"Tiro Kannada";font-size:10pt;color:#8c302b}}
@page cover{size:A4 portrait;margin:0;counter-reset:page 0;@top-center{content:none}@bottom-center{content:none}}
@media print{html,body{margin:0;background:var(--paper)}.book{display:block;padding:0}.page{width:auto;min-height:0;height:auto;margin:0;padding:0;background:var(--paper);box-shadow:none;break-after:page;-webkit-print-color-adjust:exact;print-color-adjust:exact}.page:last-child{break-after:auto}.page::before,.page-number{display:none}p{font-size:12.5pt;line-height:1.8;margin-bottom:4mm}h2{font-size:21pt;margin-bottom:6mm}h3{font-size:15pt;margin-bottom:6mm}.colophon{font-size:10pt}.contents{font-size:10.5pt;line-height:1.65}.contents td,.contents th{padding:2.2mm 1.5mm}.cover{page:cover;width:210mm;height:297mm;padding:0;aspect-ratio:auto;overflow:hidden;background:#4c1420}.cover-art{inset:0;width:210mm;height:297mm}.cover-art img{width:100%;height:100%;object-fit:contain}.frontmatter{display:flex;min-height:240mm;flex-direction:column;justify-content:center}.illustrated figure img{max-height:190mm}.illustrated .mantra,.illustrated .caption{font-size:12pt}figure{margin:5mm 0}}
'''
html='<!doctype html>\n<html lang="kn"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" /><title>ಮುದ್ಗಲ ಪುರಾಣ</title><meta name="description" content="ಮೂಲಪುಟಗಳ ಕನ್ನಡ ಓದುವ ಆವೃತ್ತಿ. ಕಥಾಭಾಗಗಳ ಅನುವಾದ, ಮಂತ್ರಗಳ ಕನ್ನಡ ಲಿಪ್ಯಂತರ ಮತ್ತು ಮೂಲಚಿತ್ರಗಳು." /><style>'+css+'</style></head><body><main class="book">'+''.join(pages)+'</main></body></html>\n'
BOOK.mkdir(exist_ok=True);DIST.mkdir(exist_ok=True)
(BOOK/'index.html').write_text(html,encoding='utf-8')
# A downloadable edition with no external assets or application controls.
standalone=html
for path in sorted(ASSETS.iterdir()):
    if path.name=='TiroKannada-OFL.txt': continue
    token='assets/'+path.name
    if token not in standalone:continue
    mime={'.ttf':'font/ttf','.png':'image/png','.jpg':'image/jpeg'}[path.suffix]
    standalone=standalone.replace(token,'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode('ascii'))
licence=(ASSETS/'TiroKannada-OFL.txt').read_text().replace('--','- -')
standalone=standalone.replace('</head>','<!-- Embedded font licence: '+licence+' -->\n</head>')
(DIST/'mudgala_purana_kannada.html').write_text(standalone,encoding='utf-8')
print(f'Built {len(pages)} book sections; 371 contents entries; {len(narrative)} unique numbered entries; {len(chapters)} chapters represented.')
