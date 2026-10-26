import {localPath} from '../../../lib/paths';
import Reader from '../../../lib/Reader';
import {notFound} from 'next/navigation';import {book,chapterPath,structured,jsonLd} from '../../../lib/book';
export const dynamicParams=false;
export function generateStaticParams(){return book.chapters.filter(c=>c.khanda===1).map(c=>({chapter:c.slug}));}
export async function generateMetadata({params}){const {chapter}=await params,c=book.chapters.find(c=>c.khanda===1&&c.slug===chapter);if(!c)return {};const title=`${c.title} · Khanda 1 Chapter ${c.number}`,description=`ಮುದ್ಗಲ ಪುರಾಣ, ಪ್ರಥಮ ಖಂಡ, ${c.title}. Sanskrit ślokas 1–${c.count} in Kannada script, with numbered Kannada meanings and short context groups.`;return {title,description,alternates:{canonical:chapterPath(c)},openGraph:{title,description,url:chapterPath(c),images:[{url:book.cover,alt:book.title}]}};}
export default async function Chapter({params}){const {chapter}=await params,c=book.chapters.find(c=>c.khanda===1&&c.slug===chapter);if(!c)notFound();return <><header className="reader-nav"><a href={localPath('/kn/mudgala-purana/khanda-1/')}>ಪರಿವಿಡಿ</a><span lang="en">Khanda 1 · Chapter {c.number}</span></header><main id="reading" tabIndex={-1}><Reader chapter={c}/></main><script type="application/ld+json" dangerouslySetInnerHTML={{__html:jsonLd(structured(c))}}/></>}
