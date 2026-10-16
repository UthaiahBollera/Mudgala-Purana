# Integration validation — 16 October 2026

Khanda 2 chapter 1 now includes verses 1–50 and remains partial. This batch adds exactly 25 reviewed entries, yielding 2,846 numbered entries across 55 represented chapters.

- Compared all 2,821 earlier TSV rows against source baseline `d5e53b91a9e7d9c3102ddc9b183c43fca01e8aa8`: text, type, keys and source mappings unchanged.
- Materialized both Library ZIP inputs through the supported Library transfer helper on the consuming Mac. Opened all eight original Sanskrit PNGs PT74–PT81; their SHA-256 values and the source ZIP hash match the reviewed JSON.
- Preserved all prior issue records exactly; appended four resolved source questions at 2.1.28, 34, 46 and 49. Existing open 2.1.9 remains visibly qualified. Cumulative source locations form a union of 37 identifiers; PT74 keeps distinct evidence per batch.
- HTML and EPUB builds passed, as did `validate_book.py google-books-khanda2-next`, `validate_source_review.py`, `tests/test_reading_contents.py`, and all 36 `tests/test_google_source_validation.py` cases. The historical Sanskrit quotation comparison was not rerun because its local reference cache is absent; no alternate source was downloaded.
- Headless Chrome rendered the prepared Pages edition at desktop 1280×900 and mobile 390×900 and 320×900. Verified all 2,846 numbered paragraphs, loaded Kannada font and all images, no visible-element or document horizontal overflow, and absence of a top banner. Inspected screenshots of the partial heading, narrative continuation, hymn and ending at verse 50. Existing `mobile-reading-layout` CSS retained byte for byte.
- The visible first-section heading derives its partial range from included rows. Existing section and verse IDs remain stable; no Khanda 2 closing colophon was generated.

Full EPUBCheck and physical reader-device testing are not claimed. Linguistic review and its limits remain documented in the accompanying review JSON/Markdown. `translation/system-prompt.md` and historical assets are unchanged. No PDF, modern English translation or new artwork was used.
