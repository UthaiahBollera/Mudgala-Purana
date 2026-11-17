import fs from 'node:fs';
import path from 'node:path';
import {notFound} from 'next/navigation';
import {localPath} from '../../../../../lib/paths';
import index from '../../../../../.generated/review/index.json';
import './review.css';
const root='/kn/mudgala-purana/review/';
export const dynamicParams=false;
export function generateStaticParams(){return [{parts:[]},...index.chapters.map(c=>({parts:c.slug.split('/')}))];}
function resolve(parts=[]){return parts.length?index.chapters.find(c=>c.slug===parts.join('/')):null;}
export async function generateMetadata({params}){
 const {parts=[]}=await params,c=resolve(parts),url=root+(c?c.slug+'/':'');
 const title=c?`Review draft · Khanda ${c.khanda} Chapter ${c.chapter}`:'ಖಂಡ 3–9 · ಪರಿಶೀಲನಾ ಕರಡು';
 return {title,description:'November 17 qualified review draft. Not expert verified. Separate from the canonical reader and downloads.',robots:{index:false,follow:true},alternates:{canonical:url},openGraph:{title,url}};
}
export default async function Review({params}){
 const {parts=[]}=await params,c=resolve(parts);
 if(parts.length&&!c)notFound();
 const chapter=c?JSON.parse(fs.readFileSync(path.join(process.cwd(),'.generated/review',`${c.khanda}-${c.chapter}.json`),'utf8')):null;
 const position=c?index.chapters.findIndex(x=>x.slug===c.slug):-1;
 return <main id="reading" tabIndex={-1} className="library review-reader">
  <nav aria-label="Review navigation"><a href={localPath('/kn/mudgala-purana/')}>ಪ್ರಕಟಿತ ಮೂಲ ಓದು</a> · <a href={localPath(root)}>ಖಂಡ 3–9 · ಕರಡು ಸೂಚಿ</a></nav>
  <h1>{c?`ಖಂಡ ${c.khanda} · ಅಧ್ಯಾಯ ${c.chapter}`:'ಮುದ್ಗಲ ಪುರಾಣ · ಖಂಡ 3–9'}</h1>
  <aside className="review-warning"><h2>ಪರಿಶೀಲನಾ ಕರಡು · ಪೂರ್ಣ ಪರಿಶೀಲಿತ ಆವೃತ್ತಿಯಲ್ಲ</h2><p lang="en">November 17, 2026 checkpoint. Not expert verified. 300 chapters / 16,734 numbered records. In the tracked review queue, 985 meanings are accepted with qualifications; 548 remain unresolved (547 text-bearing records and one placeholder). This queue excludes separate qualifications in Khanda 9 chapters 25–41. Other draft text and all retained qualifications still require review.</p><p lang="en">Historical notes may describe an earlier state; each record’s meaning status is current. Printed numbering anomalies and the placeholder kh05-ch041-v035 are preserved. This review does not replace the published canonical reader, search, EPUB or PDF downloads.</p></aside>
  {c?<><p>{c.count} numbered records · <span lang="en">Saved source text, without modernization.</span></p><article className="review-text" dangerouslySetInnerHTML={{__html:chapter.html}}/><nav aria-label="Adjacent review chapters">{index.chapters[position-1]&&<a href={localPath(root+index.chapters[position-1].slug+'/')}>ಹಿಂದಿನ ಅಧ್ಯಾಯ</a>} · <a href={localPath(root)}>ಸೂಚಿ</a> · {index.chapters[position+1]&&<a href={localPath(root+index.chapters[position+1].slug+'/')}>ಮುಂದಿನ ಅಧ್ಯಾಯ</a>}</nav></>:Array.from({length:7},(_,i)=>i+3).map(k=><section key={k}><h2>ಖಂಡ {k}</h2><ol className="chapter-list">{index.chapters.filter(c=>c.khanda===k).map(c=><li key={c.slug}><a href={localPath(root+c.slug+'/')}>ಅಧ್ಯಾಯ {c.chapter}<span lang="en">{c.count} numbered records · review draft</span></a></li>)}</ol></section>)}
 </main>;
}
