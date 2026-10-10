# ಮುದ್ಗಲ ಪುರಾಣ

Kannada reading draft of all 20 pages of `1 TO 25(1).pdf`, all 30 pages of `26 TO 55(2).pdf`, and all 21 pages of `55 TO 76(1).pdf`, and all 22 pages of `77 TO 98(1).pdf`. and all 20 pages of `99 TO 118(1).pdf`. Also includes all 20 pages of `119 TO 138(1).pdf`. Plain HTML book, not an application. Approved cover and Tiro Kannada are retained.

Includes front matter, 371 contents entries, first-khanda divider and original illustrations. Chapters 1–53 are included: 2731 unique numbered entries. Unclear readings are documented outside the reading view. Devotional passages are transliterated without translation. Output page count differs from source page count. This is a translation of uploaded excerpts, not the complete Purana.

Open `book/index.html` beside its assets. Print on A4 with background graphics enabled. EPUB: `dist/mudgala_purana.epub`.

Build: install `requirements.txt`, then run `python3 build_book.py`, `python3 build_epub.py` and `python3 validate_book.py 133`. Source-confirmed ending chapters are in `translation/completed-chapters.json`; independent batch coverage boundaries are in `translation/coverage.json`.

Batch checklists: `translation/tasks.md` and `translation/pdf-03-tasks.md` and `translation/pdf-04-tasks.md`. Reusable image-to-Kannada/HTML instructions: `translation/system-prompt.md`. Supply the existing HTML/CSS, source-page mapping and preceding verse context with that prompt for continuity. A prompt alone does not guarantee linguistic accuracy or rendering.

See `translation/verification.md`. This is a review draft, not a scholarly certified translation. XML/ZIP/assets/text checks are automated; full EPUBCheck and reader testing remain recommended.

Cover remains 1055 × 1491 pixels, not a 300 ppi A4 press master. Tiro Kannada is supplied under the SIL Open Font License, which does not license book text or illustrations.
