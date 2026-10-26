// Interface labels are separate from scripture and translation sources.
export const ui={kn:{languages:'ಭಾಷೆಗಳು',books:'ಕನ್ನಡ ಪುಸ್ತಕಗಳು',chooseKhanda:'ಖಂಡವನ್ನು ಆಯ್ಕೆಮಾಡಿ',available:'ಲಭ್ಯ ಭಾಗಗಳು',notAvailable:'Not yet available',search:'ಶ್ಲೋಕ ಹುಡುಕಾಟ'}};
export const khandaNames={1:'ಪ್ರಥಮ ಖಂಡ',2:'ದ್ವಿತೀಯ ಖಂಡ'};
export const label=(locale,key)=>ui[locale]?.[key]??ui.kn[key];
