// Next and shared URL helpers generate the complete subpath website natively.
import fs from 'node:fs';import path from 'node:path';
const target=path.resolve('../../../pages-candidate');fs.rmSync(target,{recursive:true,force:true});fs.cpSync('out',target,{recursive:true});
for(const folder of ['chapters','frontmatter','assets','styles'])fs.cpSync(path.join('../dist/web',folder),path.join(target,folder),{recursive:true});fs.copyFileSync('../dist/web/mudgala-preview.epub',path.join(target,'mudgala-preview.epub'));
fs.writeFileSync(path.join(target,'release.json'),JSON.stringify({sourceCommit:process.env.GITHUB_SHA||null,quality:'passed',run:process.env.GITHUB_RUN_ID?`https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}`:null,coverage:'Khanda 1 chapters 1–22, 1202 pairs; Khanda 2 chapters 1–74, 3614 records; 462 qualified and 7.37 pending, reading draft; future Chapter 75 excluded'},null,2));
console.log('Prepared native Pages subpath website and legacy compatibility files.');
