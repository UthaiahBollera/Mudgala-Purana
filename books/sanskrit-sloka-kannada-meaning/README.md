# Mudgala Purana — Sanskrit slokas in Kannada script and Kannada meanings

This independent book preserves the approved cover and translated front matter, followed by Khanda1 Chapters1–18:985 numbered Sanskrit/meaning pairs, with colophons. Sanskrit language is transliterated into selectable Kannada script. Related verses are grouped by context above a divider, with their individually numbered Kannada meanings in the same order below. The old book is separate and unchanged.

The edition is incomplete. It does not contain Chapters19 onward. Explicit source-reading and interpretation flags remain; see `review/current-batch-status.md`. Textual source scans remain available as hidden assets; the approved cover and devotional artworks remain visible. Review notes never enter the reader or EPUB.

## Sources and editing

User-supplied scans are authoritative; existing supplied OCR is only a cross-reference. No newOCR is generated. Per-verse original Devanagari, Kannada-script Sanskrit, meaning and source-file/PDF/printed-page provenance are retained in `review/verse-source-records.json`. Do not infer chapter coverage from front-matter contents entries. Do not silently resolve uncertain readings.

Edit canonical XHTML chapter files under `chapters/khanda-01/`, with shared assets/styles/fonts. `book.json` defines explicit source documents, chapter order, metadata and stable verse-ID reading groups. Group rationales live in `review/context-grouping*.json`. Keep UTF-8, existing IDs, language tags and Sanskrit-to-meaning associations. Follow AGENTS.md.

## Build and validate

Python3.10+ standard library; no framework or runtime dependency:

```sh
python3 books/sanskrit-sloka-kannada-meaning/build.py
python3 -m unittest discover -s books/sanskrit-sloka-kannada-meaning -p test_build.py
```

Ignored outputs: `dist/web/` complete web reader, `dist/mudgala-preview.html` standalone portable reader, and `dist/mudgala-preview.epub` EPUB3 retaining separate XHTML chapters. Do not hand-edit generated output. Deploy only the web directory to the additive `/sanskrit-kannada/` path when authorized. No original-book deployment files need modification.

Run reputable EPUBCheck on the generated EPUB and inspect real mobile/desktop rendering. Current edition passed16 regression tests, EPUBCheck5.4.0 with0 errors/warnings, and10 browser width/theme/zoom scenarios checking every985 text mapping, fonts, contrast and overflow. This is not a claim that every provisional source reading is resolved or that the whole khanda is complete.
