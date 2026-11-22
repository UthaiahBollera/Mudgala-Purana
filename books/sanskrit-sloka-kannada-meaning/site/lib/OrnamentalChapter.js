import {localPath} from './paths';

const ornament = name => localPath('/book/assets/ornamental/' + name);
const numeral = value => String(value).replace(/[0-9]/g, digit => '೦೧೨೩೪೫೬೭೮೯'[Number(digit)]);

export default function OrnamentalChapter({number, children, chapterTitle=false}) {
  const art = Object.fromEntries(
    ['corner.png', 'lotus.png', 'leaf.png', 'plaque.svg', 'seal.svg'].map(name => [
      '--k1-' + name.split('.')[0], `url("${ornament(name)}")`
    ])
  );
  const title = `ಅಧ್ಯಾಯ ${numeral(number)}`;
  return (
    <div className="ornamental-chapter" style={art}>
      <div className="ornamental-inside">
        <div className="ornamental-masthead" aria-hidden="true">
          <span>ಮುದ್ಗಲ ಪುರಾಣ</span>
          <img src={ornament('ganesha.png')} alt="" width="287" height="87"/>
          <span>ಖಂಡ ೧</span>
        </div>
        {chapterTitle
          ? <h1 className="ornamental-plaque" aria-label={`ಖಂಡ ೧ · ${title}`}><span>{title}</span></h1>
          : <div className="ornamental-plaque" aria-hidden="true"><span>{title}</span></div>}
        <div className="ornamental-rule" aria-hidden="true"/>
        {children}
        <div className="ornamental-end" aria-hidden="true"><img src={ornament('om.png')} alt="" width="178" height="54"/></div>
      </div>
    </div>
  );
}
