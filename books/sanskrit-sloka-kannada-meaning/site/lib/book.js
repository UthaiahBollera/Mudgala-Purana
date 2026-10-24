import fs from 'node:fs';import path from 'node:path';
export const book=JSON.parse(fs.readFileSync(path.join(process.cwd(),'.generated/book.json'),'utf8'));
export const origin='https://mudgalapurana.com';
export const chapterPath=c=>`/khanda-1/${c.slug}/`;
export const description='ಮುದ್ಗಲ ಪುರಾಣ: ಕನ್ನಡ ಲಿಪಿಯಲ್ಲಿ ಸಂಸ್ಕೃತ ಶ್ಲೋಕಗಳು ಮತ್ತು ಕನ್ನಡ ಅರ್ಥ. Read Mudgala (Mudugal) Purana in Kannada script with Kannada meanings; available Khanda 1 chapters 1–18.';
export function structured(c){return c?{'@context':'https://schema.org','@type':'Chapter',name:`${c.title} — Khanda 1 Chapter ${c.number}`,position:c.number,inLanguage:['kn','sa-Knda'],url:origin+chapterPath(c),isPartOf:{'@type':'Book','@id':origin+'/#book',name:book.title}}:{'@context':'https://schema.org','@type':'Book','@id':origin+'/#book',name:book.title,alternateName:['Mudgala Purana','Mudugal Purana'],inLanguage:['kn','sa-Knda'],url:origin+'/',description,dateModified:book.modified,image:origin+book.cover,hasPart:book.chapters.map(c=>({'@type':'Chapter',name:`${c.title} — Khanda 1 Chapter ${c.number}`,position:c.number,url:origin+chapterPath(c)}))};}
export const jsonLd=d=>JSON.stringify(d).replace(/</g,'\\u003c');
