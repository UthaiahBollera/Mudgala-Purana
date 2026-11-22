import fs from 'node:fs';
import path from 'node:path';
import {notFound} from 'next/navigation';
import {localPath} from '../../../../../lib/paths';
import Khanda1PrintDownload from '../../../../../lib/Khanda1PrintDownload';
import OrnamentalChapter from '../../../../../lib/OrnamentalChapter';
import index from '../../../../../.generated/review/index.json';
import './review.css';
const root='/kn/mudgala-purana/review/';
export const dynamicParams=false;
export function generateStaticParams(){return [{parts:[]},...index.chapters.map(c=>({parts:c.slug.split('/')}))];}
function resolve(parts=[]){return parts.length?index.chapters.find(c=>c.slug===parts.join('/')):null;}
export async function generateMetadata({params}){
 const {parts=[]}=await params,c=resolve(parts),url=root+(c?c.slug+'/':'');
 const title=c?`Review draft · Khanda ${c.khanda} Chapter ${c.chapter}`:'ಖಂಡ 1–9 · ಪರಿಶೀಲನಾ ಕರಡು';
 return {title,description:'November 22 Sanskrit–Kannada review draft. Not expert verified. Reading draft distinct from the canonical editions.',robots:{index:false,follow:true},alternates:{canonical:url},openGraph:{title,url}};
}
export default async function Review({params}){
 const {parts=[]}=await params,c=resolve(parts);
 if(parts.length&&!c)notFound();
 const chapter=c?JSON.parse(fs.readFileSync(path.join(process.cwd(),'.generated/review',`${c.khanda}-${c.chapter}.json`),'utf8')):null;
 const reading=chapter?<article className="review-text" dangerouslySetInnerHTML={{__html:chapter.html}}/>:null;
 const position=c?index.chapters.findIndex(x=>x.slug===c.slug):-1;
 return <main id="reading" tabIndex={-1} className="library review-reader">
  <nav aria-label="Review navigation"><a href={localPath('/kn/mudgala-purana/')}>ಪ್ರಕಟಿತ ಮೂಲ ಓದು</a> · <a href={localPath(root)}>ಖಂಡ 1–9 · ಕರಡು ಸೂಚಿ</a></nav>
  {c?.khanda!==1&&<h1>{c?`ಖಂಡ ${c.khanda} · ಅಧ್ಯಾಯ ${c.chapter}`:'ಮುದ್ಗಲ ಪುರಾಣ · ಖಂಡ 1–9'}</h1>}
  <aside className="review-warning"><h2>ಪರಿಶೀಲನಾ ಕರಡು · ಪೂರ್ಣ ಪರಿಶೀಲಿತ ಆವೃತ್ತಿಯಲ್ಲ</h2><p lang="en">November 22, 2026 reading drafts. Not expert verified. {index.stats.chapters} chapters across all nine khandas. In the latest tracked review of Khandas 3–9, {index.stats.working_resolved} of {index.stats.reviewed_queue} flagged passages were resolved for the working Kannada draft and {index.stats.still_marked} remain marked. Another {index.stats.provisional} readings are provisional first-pass drafts.</p><p lang="en">These figures do not include other retained qualifications, such as Khanda 9 chapters 25–41. Missing or uncertain source text is preserved, including Khanda 5 chapter 41 verse 35. Existing canonical EPUB and PDF editions remain available separately.</p></aside>
  {(!c||c.khanda===1)&&<Khanda1PrintDownload/>}
  {c?<><p>{c.count} numbered records · <span lang="en">Saved source text, without modernization.</span></p>{c.khanda===1?<OrnamentalChapter number={c.chapter} chapterTitle>{reading}</OrnamentalChapter>:reading}<nav aria-label="Adjacent review chapters">{index.chapters[position-1]&&<a href={localPath(root+index.chapters[position-1].slug+'/')}>ಹಿಂದಿನ ಅಧ್ಯಾಯ</a>} · <a href={localPath(root)}>ಸೂಚಿ</a> · {index.chapters[position+1]&&<a href={localPath(root+index.chapters[position+1].slug+'/')}>ಮುಂದಿನ ಅಧ್ಯಾಯ</a>}</nav></>:Array.from({length:9},(_,i)=>i+1).map(k=><section key={k}><h2>ಖಂಡ {k}</h2><ol className="chapter-list">{index.chapters.filter(c=>c.khanda===k).map(c=><li key={c.slug}><a href={localPath(root+c.slug+'/')}>ಅಧ್ಯಾಯ {c.chapter}<span lang="en">{c.count} numbered records · review draft</span></a></li>)}</ol></section>)}
 </main>;
}
