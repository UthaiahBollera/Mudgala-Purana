import {chapterPath,localPath} from './paths';
export {chapterPath} from './paths';
import fs from 'node:fs';import path from 'node:path';
export const book=JSON.parse(fs.readFileSync(path.join(process.cwd(),'.generated/book.json'),'utf8'));
export const origin='https://mudgalapurana.com';
export const description='ಮುದ್ಗಲ ಪುರಾಣ: ಕನ್ನಡ ಲಿಪಿಯಲ್ಲಿ ಸಂಸ್ಕೃತ ಶ್ಲೋಕಗಳು ಮತ್ತು ಕನ್ನಡ ಅರ್ಥ. Read Mudgala (Mudugal) Purana in Kannada script with Kannada meanings; Khanda 1 chapters 1–26 and Khanda 2 chapters 1–74. Partial reading draft; source caveats and pending meanings retained.';
export function structured(c){return c?{'@context':'https://schema.org','@type':'Chapter','@id':origin+chapterPath(c),name:`${c.title} — Khanda ${c.khanda} Chapter ${c.number}`,position:c.number,inLanguage:['kn','sa-Knda'],url:origin+chapterPath(c),isPartOf:{'@type':'Book','@id':origin+'/kn/mudgala-purana/#book',name:book.title}}:{'@context':'https://schema.org','@type':'Book','@id':origin+'/kn/mudgala-purana/#book',name:book.title,alternateName:['Mudgala Purana','Mudugal Purana'],inLanguage:['kn','sa-Knda'],url:origin+'/kn/mudgala-purana/',description,dateModified:book.modified,image:origin+book.cover,hasPart:book.chapters.map(c=>({'@type':'Chapter','@id':origin+chapterPath(c),name:`${c.title} — Khanda ${c.khanda} Chapter ${c.number}`,position:c.number,url:origin+chapterPath(c)}))};}
export const jsonLd=d=>JSON.stringify(d).replace(/</g,'\\u003c');

export const readerHTML=c=>c.html.replaceAll('\"/book/','\"'+localPath('/book/'));
