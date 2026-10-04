# ಮುದ್ಗಲ ಪುರಾಣ

Kannada book sample with a flat illustrated cover and six interior sections. This is a book, not a web application. No toolbar, navigation controls, scripts, or application notices are included in the reading view.

## Read and print

Open `book/index.html` in a browser. Keep its `assets` directory beside it. Use the browser's print command for the A4 layout and enable background graphics to retain the page colours.

## EPUB

The generated ebook is `dist/mudgala_purana.epub`. It includes UTF-8 XHTML, Kannada language metadata (`kn`), an EPUB navigation document, the corrected cover, and embedded Tiro Kannada Regular. Text reflows for the reader's screen, so screen page counts vary.

Regenerate with Python 3.10 or newer:

```sh
python3 -m pip install -r requirements.txt
python3 build_epub.py
```

The build checks XML parsing, ZIP integrity, manifest files, reading order count, and unchanged book content. Full EPUBCheck and visual testing on target ebook readers are still recommended before publication.

## Content and assets

Interior wording is sample text, not a verified translation of the Purana. The cover artwork is 1055 × 1491 pixels, a design proof rather than a 300 ppi A4 print master. Tiro Kannada is included under the SIL Open Font License in `book/assets/TiroKannada-OFL.txt`. No licence for the book text or artwork is granted by the font licence.
