export const basePath=process.env.NEXT_PUBLIC_MUDGALA_BASE_PATH||'';
export const localPath=p=>p.startsWith('/')?basePath+p:p;
export const canonicalBookPath='/kn/mudgala-purana/';
export const bookPath=localPath(canonicalBookPath);
export const khandaPath=n=>localPath(`${canonicalBookPath}khanda-${n}/`);
export const chapterPath=c=>`${canonicalBookPath}khanda-${c.khanda}/${c.slug}/`;
export const chapterHref=c=>localPath(chapterPath(c));
export const assetSet=s=>s?.split(',').map(v=>localPath(v.trim())).join(', ');
