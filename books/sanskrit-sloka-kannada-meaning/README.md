# Mudgala Purana: Sanskrit sloka + Kannada meaning

This separate book contains the cover and empty chapter content. The existing approved Kannada v5 cover is reused unchanged.

## Build

Requires Python 3.10+; no third-party packages or framework.

```sh
python3 books/sanskrit-sloka-kannada-meaning/build.py
```

Outputs (ignored by Git):

- `dist/web/index.html`: web reader; deploy the entire `web/` folder together when authorized.
- `dist/mudgala-preview.html`: standalone preview with embedded cover, font and styles; open directly in a browser.
- `dist/mudgala-preview.epub`: EPUB 3 with separate XHTML chapter files internally.

No build or deployment changes are made to the original book.

## Editing

`book.json` is the explicit reading order and metadata source. Each chapter records its stable ID, khanda number, chapter number, navigation title, source path and status. Keep the array in khanda/chapter order. Update `modified` in UTC when changing the edition. The identifier stays stable for this book.

Edit only canonical XHTML under `chapters/khanda-NN/chapter-NNN.xhtml`. Add future chapters there and register them in the manifest. The current chapter is an empty structural scaffold, not a supplied chapter title or translation. The web reader and standalone HTML display only the cover and chapter content. Manifest titles are used for internal EPUB navigation, which is hidden from book pages. No devotional opening or sample verse is included.

Keep UTF-8 and XHTML namespaces. Kannada meaning uses `lang="kn"`; future Sanskrit text should use the chosen appropriate language/script tag once approved. Keep the stable chapter main ID. For an approved populated chapter change `status` from `blank` to `draft`; the build rejects any text in a chapter still marked blank. Shared styling lives in `styles/book.css`, the approved cover in `assets/`, and the Tiro Kannada font and OFL license in `assets/fonts/`. A future Devanagari font can be added only if that script is selected.

Do not edit generated `dist/` files. The web reader and standalone HTML are generated from the same manifest and chapter sources as the EPUB. Canonical chapter files resolve shared assets directly, so they are independently viewable as well.

## Validation

The build checks unique IDs/paths, numeric chapter order, XML parsing, local chapter references and blank scaffolds. Run the regression checks with `python3 -m unittest discover -s books/sanskrit-sloka-kannada-meaning -p test_build.py`. Before sharing an edition, run W3C EPUBCheck against the EPUB, inspect the web and standalone output in desktop/mobile browsers, and verify navigation and font loading. EPUBCheck is an external development tool, not a runtime dependency:

```sh
java -jar /path/to/epubcheck.jar books/sanskrit-sloka-kannada-meaning/dist/mudgala-preview.epub
```

Preview status does not constitute a claim of complete EPUB accessibility conformance. No scripture text has yet been selected for typography or reading-order review.

First scaffold verification: W3C EPUBCheck 5.4.0 passed with 0 errors and 0 warnings. Desktop (1100px) and mobile (390px) browser checks verified the embedded font and cover, no horizontal overflow, empty content, chapter anchor, web chapter navigation and return to contents. Sanskrit glyph rendering remains pending the script selection and actual text.
