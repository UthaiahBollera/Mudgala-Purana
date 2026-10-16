# Kannada Mudgala Purana: source review, 15 October 2026

## Result and scope
All 2731 included numbered entries were read against the corresponding first-khanda Sanskrit: chapters 1–52 complete, chapter 53 through its existing partial verse 39. 1676 verse texts and 10 chapter headings were corrected after a separate comparison pass. Correct narrative Kannada was preserved; prayers remain Sanskrit transliteration in Kannada script. Source-page mappings and chapter/verse order are unchanged. No new chapter or continuation has been added.

This is a source-reviewed reading draft, not an error-free or critically established edition. 152 numbered-verse records still have an unresolved reading, possible edition variant, or philological question. Some records contain a supported partial correction while another phrase remains unresolved. Plausible variant readings were retained rather than silently replaced.

## Sources and limits
- Main reference: [Sanskrit Documents, Mudgala Purana Khanda 1](https://sanskritdocuments.org/doc_purana/mudgalapurANam1.html), proofread by Yash Khasbage. Chapter totals 1–52 align with the draft. Two duplicate verse labels in the reference were documented: 11:33 is labelled 32, and 50:63 is labelled 33. Sequential context preserves the book numbering.
- Google Books checked: [Shri Mudgala Purana—Khand 1](https://books.google.com/books?id=Lh0FEQAAQBAJ), Shree Mudgal Puran Trust, 2024, 648 pages; translators Saraswati Raman, Rupal Satish Kulkarni, Yogindra Vijay Deodhar and Ganesh Vinayak Joshi. Inspected preview images PT61–63 identify the volume and first chapter but do not contain verse text. Google Books did not independently corroborate the corrected verse readings in this review.
- The suggested [Khand 2 Google Books volume](https://books.google.co.in/books?id=fZcHEQAAQBAJ&printsec=frontcover) concerns a different khanda and was not used to substitute first-khanda verses.
- Original uploaded scan bytes were not present in the repository. Archive/Google Books verse-scan retrieval could not be completed. Consequently, this comparison does not establish that every variant belongs to the same printed edition.

## What remains
See unresolved.json for every remaining chapter/verse issue. The chapter 24 heading also remains edition-dependent: the online reference says a meeting, while the earlier scan review recorded a departure; its existing heading is retained. The source-limited ending 53:39 is still partial; no online continuation was inserted. Front-matter place-name readings on source pages 11–12 (Dhemwad/ಢೇಂವಾಡ್) and previously noted contents names (Anasakta, Shaila, Karmangada) remain unverified. The 371 source contents entries and illustrations were preserved, not comprehensively recollated in this chapter review.

## Audit files
- corrections.json: exact original/corrected Kannada, Sanskrit evidence, khanda 1 chapter/verse, source URL, rationale and review status for every applied verse correction.
- title-corrections.json: heading changes and evidence.
- checklist.json: all 53 chapter coverage records.
- sources.json: reference identity, checksum, Google Books details, scope and reference numbering errata.
- unresolved.json: remaining numbered-verse issues, with partial-correction versus unchanged status.
- supplementary-unresolved.json: the held chapter heading, front-matter place names and contents-name questions.

## Verification
The rebuilt outputs are checked for 2731 unique ordered verse IDs, unchanged source-page mapping through 133, one partial tail, complete chapter counts, Kannada font glyph coverage, no cross-script Indic contamination, HTML text equality, EPUB ZIP/XML/manifest/spine/assets/text identity, internal references and correction provenance against the original commit. Sanskrit evidence for applied verse corrections is matched to the pinned local reference, including the two documented numbering errata.

Full EPUBCheck and ebook-reader testing have not been performed. Browser/print visual QA could not run because the available Chromium process was blocked by the execution environment. Prior print-proof claims do not validate this changed text.

The correction branch is local; no push, pull request, deployment, or replacement of the existing published site was performed.
