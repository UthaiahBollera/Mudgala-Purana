export const progressKey='mudgala-reader-progress';
export const scaleKey='mudgala-reader-scale';
export const themeKey='mudgala-reader-theme';
// Runs before paint on every route; optional browser state never changes source text.
export const preferenceBootstrap=`try{var t=localStorage.getItem(${JSON.stringify(themeKey)});if(['system','light','dark'].includes(t))document.documentElement.dataset.theme=t;var s=Number(localStorage.getItem(${JSON.stringify(scaleKey)}));if(s>=.9&&s<=1.5)document.documentElement.style.setProperty('--reader-scale',s)}catch{}`;
