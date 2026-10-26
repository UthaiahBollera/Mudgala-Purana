import {book} from './book';
import {bookPath,localPath} from './paths';
export {bookPath,khandaPath} from './paths';
export const languages=[
{code:'kn',native:'ಕನ್ನಡ',name:'Kannada',available:true},
{code:'en',native:'English',name:'English'},
{code:'hi',native:'हिन्दी',name:'Hindi'},
{code:'es',native:'Español',name:'Spanish'},
{code:'zh',native:'中文',name:'Chinese'},
{code:'ar',native:'العربية',name:'Arabic',dir:'rtl'},
{code:'fr',native:'Français',name:'French'},
{code:'pt',native:'Português',name:'Portuguese'},
{code:'bn',native:'বাংলা',name:'Bengali'},
{code:'ru',native:'Русский',name:'Russian'},
{code:'ja',native:'日本語',name:'Japanese'},
{code:'de',native:'Deutsch',name:'German'},
{code:'ta',native:'தமிழ்',name:'Tamil'},
{code:'te',native:'తెలుగు',name:'Telugu'}];
export const edition={kn:{cover:book.cover,alt:'ಮುದ್ಗಲ ಪುರಾಣದ ಅನುಮೋದಿತ ಮುಖಪುಟ',status:'partial'}};
export function Breadcrumbs({items}){return <nav className="breadcrumbs" aria-label="ನೀವು ಇರುವ ಸ್ಥಳ"><ol>{items.map(([label,href],i)=><li key={i}>{href?<a href={href}>{label}</a>:<span aria-current="page">{label}</span>}</li>)}</ol></nav>}
export const baseCrumbs=[['ಭಾಷೆಗಳು',localPath('/')],['ಕನ್ನಡ',localPath('/kn/')],['ಮುದ್ಗಲ ಪುರಾಣ',bookPath]];

export const languageArt={src:'/book/assets/library/language-manuscript-v1-768.webp',srcSet:'/book/assets/library/language-manuscript-v1-384.webp 384w, /book/assets/library/language-manuscript-v1-768.webp 768w',width:768,height:512,kind:'landscape',alt:''};
