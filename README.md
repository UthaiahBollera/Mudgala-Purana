# ಮುದ್ಗಲ ಪುರಾಣ

Kannada reading draft spanning **two volumes, 55 represented chapters and 2,846 numbered entries**: Khanda 1, Vakratunda Charita, through 54:55 (2,796 entries), plus **Khanda 2 chapter 1 verses 1–50, partial**. Unresolved readings remain; this is not a scholarly certified translation. Narrative is translated into formal Kannada; devotional verses remain Sanskrit transliterated in Kannada script.

## Latest source-backed continuation

**Khanda 2 chapter 1 verses 26–50** were independently reviewed against original Sanskrit at [Google Books fZcHEQAAQBAJ, PT74–PT81](https://books.google.com/books?id=fZcHEQAAQBAJ&pg=PT74). The batch adds 25 entries (17 narrative translations and eight Kannada-script Sanskrit prayers), preserving all 2,821 earlier entries. Four source-reading questions were resolved by enlarged-pixel review and retained in the JSON register. No new open semantic question remains in this batch; the existing **2.1.9** notice and historical issues remain. Chapter 1 is still partial, now **verses 1–50**, and its body heading displays that range. No ending colophon is inferred. Cumulative Google Books coverage is 37 distinct page locations; the two PT74 crops retain separate batch evidence.

- [Verses 26–50 review](translation/google-books-khanda2-next-review.md)
- [Per-verse evidence and decisions](translation/google-books-khanda2-next-review.json)

### Previous continuation: Khanda 2 opening

**Khanda 2 chapter 1 verses 1–25** were checked against original Sanskrit at [Google Books fZcHEQAAQBAJ, PT66–PT74](https://books.google.com/books?id=fZcHEQAAQBAJ&pg=PT66). All 25 records received independent review. Verse **2.1.9 remains unresolved**, visibly marked in Kannada and indexed in the issue registry. This chapter remains partial; no thematic title or ending colophon is inferred. All 2,796 prior entries remain unchanged.

- [Khanda 2 opening review](translation/google-books-khanda2-opening-review.md)
- [Khanda 2 per-verse evidence and decisions](translation/google-books-khanda2-opening-review.json)

### Previous continuation: Khanda 1 ending

The ending, **53:39–49 and 54:1–55**, was checked directly against the original Sanskrit visible in [Google Books Khand 1](https://books.google.com/books?id=Lh0FEQAAQBAJ), locations **PT881–884 and PT886–902**. This batch adds 65 entries and completes the previously partial 53:39. Its 66 records received an independent second review. Readings at **53:41, 54:10 and 54:53 remain unresolved**, with visible Kannada notices and exact source locations in the issue registry.

The displayed contents now index only the translated body, using matching chapter titles, verse ranges and links. The inherited full-source contents file remains archival evidence and is not the reading edition's navigation.

New work uses Google Books Sanskrit only. Previously supplied PDFs are no longer active sources or fallback references; earlier translations and their dated provenance are retained. Modern English commentary and new artwork are not reproduced. This batch does not claim that the earlier 2,731 entries have all been checked against Google Books.

- [Unresolved passages and resolution history (JSON)](translation/unresolved-passages.json)
- [Google Books ending review](translation/google-books-khanda1-ending-review.md)
- [Per-verse source/review evidence (JSON)](translation/google-books-khanda1-ending-review.json)
- [Historical correction review](translation/source-review/README.md)

The Google Books cumulative count after chapter 53 also differs from the current entry count (2,744 versus 2,741); this remains an explicit comparison question, not a presumed missing-text diagnosis.

## Read and build

Open `book/index.html` beside its assets. EPUB: `dist/mudgala_purana.epub`. The public preview is [GitHub Pages](https://uthaiahbollera.github.io/Mudgala-Purana/). Print on A4 with background graphics enabled.

Install `requirements.txt`, then run:

```
python3 build_book.py
python3 build_epub.py
python3 validate_book.py google-books-khanda2-next
python3 validate_source_review.py
python3 tests/test_reading_contents.py
python3 tests/test_google_source_validation.py
```

HTML/EPUB structure, links, asset references, Kannada glyph coverage, exact verse order, historical text preservation and source/review consistency are checked. Full EPUBCheck and reader-device testing are not claimed. The approved cover and Tiro Kannada font remain; the font's SIL Open Font License does not license book text or illustrations.

## Historical correction review

The dated review corrected 1,676 verse texts and 10 chapter headings among the original 2,731 entries and recorded 152 unresolved verse records. Its original evidence remains unchanged. The current issue registry records subsequent resolutions separately, including the completed 53:39. Unknown Google Books page IDs remain null rather than guessed.
