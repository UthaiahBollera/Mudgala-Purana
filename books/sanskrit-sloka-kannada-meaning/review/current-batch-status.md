# Edition coverage and publication boundary

## Published snapshot

This edition contains validated local Chapters1–18 (985 numbered pairs), prepared for the user-requested publication. Earlier reports describe historical snapshots and do not define current coverage.

## Validated local canonical continuation

- User scans remain authoritative; existing supplied OCR is secondary, no new OCR generated.
- Front matter remains unchanged. Chapter1 now covers1–59 and colophon; Chapter2 covers1–45 and colophon; Chapter3 covers1–63 and colophon; Chapter4 covers1–110 and colophon; Chapter5 covers1–47 and colophon; Chapter6 covers1–62 and colophon; Chapter7 covers1–52 and colophon; Chapter8 covers1–73 and colophon; Chapter9 covers1–46 and colophon; Chapter10 covers1–42 and colophon. Chapter11 covers1–78 and colophon; Chapter12 covers1–48 and colophon. Chapter13 covers1–51 and colophon; Chapter14 covers1–41 and colophon. Chapter15 covers1–22 and colophon; Chapter16 covers1–26 and colophon. Chapter17 covers1–56 and colophon; Chapter18 covers1–64 and colophon. Total985 numbered Sanskrit/meaning pairs plus separate invocation.
- Physical source: `1 TO 25.pdf` pages1–20, then `26 TO 55.pdf` pages1–30 (printed8–37), then `55 TO 76.pdf` pages1–7 (printed38–44). Chapter3 verse58 crosses this file boundary. Chapter1 verse47 is now completed from its actual scan continuation. The historical partial47 archive is retained.
- Reader Sanskrit is in Kannada script; current original Devanagari, Kannada text and provenance are in `verse-source-records.json`. Existing Chapter1 1–46 paragraphs are preserved exactly against `published-chapter1-prefix.xhtml`.
- Context groups: 290 across18 chapters, ranging1–5 verses after natural subtopic splits. Source and Kannada meaning bytes unchanged. No larger-group exception. Boundary rationale: `readability-grouping-adjustment.json` and individual chapter grouping records.
- Sanskrit uncertainties remain Chapter1 10/25/32/40/46; Chapter2 8/20/41; Chapter3 13 (instrument spelling); Chapter4 3/17/34/40/91/93/100; Chapter5 30/37; Chapter6 4/8/12/13/20/23/25/47; Chapter7 25/40/46; Chapter8 8/30/36/45/46/48/60; Chapter9 11/25/26/34/36; Chapter10 2/11/14/18 (reading or interpretation). Chapter11 flags12/13/15/32/35/36/43 and Chapter12 flags10/18/19/29/47 remain; Chapter13 flags34/51 and Chapter14 flags2/11/37/39/40 remain; Chapter15 flag11 and Chapter16 flags3/4/9/10/16/19/22 remain; Chapter17 flags6/10/11/12/14/18/21/27/29/30/36/39 and Chapter18 flags6/11/19/23/36/37/51/53/58 remain; Chapter1 Kannada meaning flags38/40 remain. Do not silently resolve them.
- All61 textual scan placements are retained and hidden; approved cover plus5 devotional artworks remain visible.
- Validation:16 regression tests; clean EPUBCheck;10 Chrome scenarios at320/375/768/1100px, light/dark and200%layout zoom. Exact985 mappings and order checked; fonts/selectability/contrast pass, no overflow or clipped slokas. See `integrated-browser-validation.json`.
- Next canonical continuation: Chapter19verse1, `55 TO 76.pdf` PDF7 / printed44, belowChapter18colophon. A private Chapter19 first draft exists but has not completed its second visual validation pass; it is excluded from this edition. Translation is paused by user request. Latest report: `chapters017-018-validation.md`.


## Essential whole-khanda blocker

After Chapter54 verse34 and the opening of35 on printed122 (`139 TO 163.pdf`, PDF2), the next supplied page is a completion divider. A bounded overlap check of adjacent supplied PDFs and original Downloads copy did not recover the ending body leaf. The rest of35 and ending/colophon require a scan; exact missing physical page count cannot be certified. See `missing-ending-scan-check.json`. Do not claim complete Khanda1. Further translation is paused pending the user's source update or new instructions.

Follow the user's current request and active approval settings for repository publication. The user explicitly requested publication of the validated available edition and then a pause. Preserve older reports as historical snapshots; they do not supersede this status.

## October26 website-first release boundary

Website changes only; no staging, commit, push or deployment. Published-content candidate remains Khanda1 Chapters1–18/985pairs. The new Khanda2 Chapter1 verses1–6 draft and its source/scan/review records are preserved outside the checkout in the private-review khanda02-starter bundle; verse2 remains unresolved. No Khanda2 text, route, search entry, sitemap URL, source scan, PDF or EPUB is included in this release. Continue translation only when separately requested. Private Khanda1Chapter19 remains excluded.


## October27 release candidate

Khanda2 Chapters1–26:1289 numbered records,399 contextual groups;1200 resolved drafts,88 qualified meanings,one pending7.37. Not expert-reviewed. Chapter27 is excluded because its integration checkpoint was cancelled;no checkpoint retry or Chapter28 translation is part of this release. Original book and Khanda1 source unchanged. Publication requires passing the release gates and actual deployment verification.


## October27 Chapter27 release candidate

Chapter27 checkpoint was explicitly approved and saved;release candidate now Khanda2 Chapters1–27,1322 records/408 groups,1231 resolved drafts/90 qualified/1pending7.37.Not expert-reviewed.Future chapters stay private and require separate publication approval.


## October 28 release candidate: all available Khanda 2 draft chapters

Khanda 2 Chapters 1–74, through 74.28 and the source-ending colophon on supplied original page 0282, printed page 156. The reading draft contains 3,614 numbered records in 1,060 contextual groups: 3,148 resolved drafts, 465 qualified records and one pending Kannada meaning (7.37). Source extent is complete; this is not a fully resolved or expert-verified translation. All prior uncertainty markers remain. Khanda 1 Chapters 1–18 and its private Chapter 19 exclusion are unchanged. This supersedes the historical 27-chapter release boundary above.

The user explicitly requested publication of the available Khanda 2 draft to the existing Pages preview. See `khanda02-release-074.json` for the review list and exact source references. Source and download consistency, tests, CI and live verification are required before claiming publication.


## Source photograph corrections — 2026-10-29

Printed pages 79 and 99 were compared with 48 existing verse records (three partially visible). Corrected 37.18, 47.6 and 47.20, and the Chapter 36 closing title. Three draft flags cleared: 462 qualified records and the pending meaning of 7.37 remain. Coverage remains Chapters 1–74, 3,614 records and 1,060 context groups. See `khanda02-photo-corrections-2026-10-29.json` for the exact before/after text and provenance. These corrections require fresh PDF/EPUB builds and release validation.


## Continuation resumed — 2026-10-30

Khanda 1 Chapter 19: 67 numbered verse/meaning records, 20 short context groups; seven qualified readings (15,28,29,45,50,52,53). Supplied PDF 55 TO 76.pdf pages 7–10 / printed 44–47 visually compared. The earlier provisional negative at verse 9 was corrected to the visible ब्रह्मन्नत्र वै. Splits at verses 33 and 57 were reunited. Previous 18 chapters and all Khanda 2 source files are unchanged. User requested ongoing supported-batch publication toward all nine khandas; this batch still needs release checks and live verification. Next: Chapter 20 verse 1, same PDF page 10 / printed 47, below the Chapter 19 colophon.


## Chapter 20 continuation — 2026-10-30

Complete 42-record reading draft in 13 context groups; eleven source/interpretation caveats. Supplied PDF pages 10–12 / printed 47–49 and original PNG0047–0049 visually compared. Source names the one-syllable mantra without printing its syllable here; none added. Splits 8 and 34 reunited. Next: Chapter 21 verse 1, PDF12 / printed49. All previous 93 chapter source hashes unchanged.


### Chapter 20 transcription correction pass

The enlarged original PNG comparison exposed mistakes in the initial transcription and associated meanings, including 20.1, 20.25, 20.30, 20.32 and 20.35. These are corrections to our draft, not claimed source variants. Full before/after history is in `chapter-020-transcription-corrections-2026-10-30.json`. Forty-two records and thirteen groups remain; current review qualifications: 17, 28, 32 and 39. The source explicitly says a thousand divine years in 32; no mantra syllable has been invented. Regenerated release verification pending.

Corrected artifacts passed local validation: 16 book tests, 11 reader tests, 5 SEO tests, negative audit gate, 45 browser scenarios, Pages checks and four EPUBCheck files with zero errors/warnings. Original 93 chapter sources and Khanda 2 print PDF remain unchanged. K1 PDF: 228 A4 pages with embedded fonts; corrected chapter first, middle and final pages visually inspected. Live release verification remains separate.

A final tight crop confirms `देहानां` in 20.5, distinct from `देहिनां` in 20.6. Both Sanskrit and Kannada meaning are corrected and the distinction has a regression assertion. Regenerated PDFs and four EPUBCheck files pass; the corrected PDF page 221 was visually inspected.


## Chapter 21 continuation — 2026-10-30

54 numbered source records and21 context groups, from supplied PDF12–15 / printed49–52 and native original PNG0049–0052. Sixteen records retain source or interpretation qualifications; several are partial readings with explicit markers, not completed reconstructed Sanskrit or expert-reviewed meanings. All54 positions and the closing colophon are present. Splits10,27,45 reunited; source soham and Ganesh names retained without added syllables. Previous94chapter source hashes unchanged. Local validation and release verification pending. Next: Chapter22verse1,PDF15/printed52 below the colophon.

Local Chapter21 release checks passed: 16 book tests,12 reader tests,5 SEO tests,48 browser scenarios,negative SEO gate,Pages checks and four EPUBCheck editions with zero errors/warnings. The240-page K1 PDF contains all54 exact source/meaning texts after whitespace normalization; first/middle/last chapter pages and phone/desktop reader visually inspected. Three provisional starter transcriptions (3,8,9) were corrected before release; concise before/after history retained separately. Live verification remains pending.


## Chapter22 continuation —2026-10-30

54 records,18 short context groups,three qualifications (27,40,54). Source originalPNG0052–0054 and suppliedPDF15–17/printed52–54 compared;9and34page splits reunited. The printed dehanivedana term and Ganeshoham retained in Kannada script. Ramachandra in43 and Jamadagni-son Rama in45 remain distinct. Printed bhavane in40 and fine closing reading54 are qualified rather than normalized. Previous95chapter files unchanged. Build/live validation pending. Next:23.1,PDF18/printed55;verify new page before translating.

Local Chapter22 checks passed:16book tests,13reader tests,5SEO tests,51responsive cases,negative audit gate,Pages checks and four EPUBCheck editions with zero errors/warnings. K1PDF250A4pages;all54exact source/meaning texts present; beginning,page-split,exemplar and ending pages visually inspected alongside phone/desktop reader. Previous95chapter hashes and Khanda2printPDF unchanged. Live release verification remains pending.


## Chapter 23 continuation — 2026-10-30

49 records, 16 short context groups and seven qualifications (1, 3, 8, 15, 16, 24, 44). User-supplied original PNG0055–0056 and split PDF pages 18–19 / printed pages 55–56 were compared; verse 26's split was reunited. The printed Madakara name and thousand-divine-year interval are retained. The five-syllable mantra is named, but its formula is not printed here; none was invented. Previous 96 chapter files are unchanged. Local and release checks are pending. Next: 24.1, PDF page 20 / printed page 57.

Local Chapter 23 checks passed: 16 book tests, 14 reader tests, 5 SEO tests, 54 responsive scenarios, negative release gate, Pages compatibility and four EPUBCheck editions with zero errors/warnings. The 259-page K1 PDF contains all 49 exact verse/meaning texts; opening, page-split, proper-name, mantra-duration and closing pages were visually inspected with phone/desktop reader renders. Previous 96 chapter sources and Khanda 2 print PDF are unchanged. Live verification remains pending.


## Chapter 24 continuation — 2026-10-30

48 source-position records, 16 short context groups, eight qualifications (4, 6, 12, 24, 30, 31, 35, 41). User original PNG0057–0058 and supplied PDF20–21 / printed57–58 visually compared. Hymn12–19 and the boon request are retained without an added formula. The daityas claims are attributed to their speakers, not silently reconciled or asserted as narrator doctrine. Printed te in24 and damaged second half of41 remain qualified. Prior97chapter sources unchanged. Local and live validation pending. Next25.1, PDF22 / printed59; verify next page before translating.

Local Chapter 24 checks passed: 16 book tests, 15 reader tests, 5 SEO tests, 57 responsive scenarios, negative audit gate, Pages compatibility and four EPUBCheck editions with zero errors/warnings. All 48 exact verse/meaning texts are present in the 268-page K1 PDF; opening, boon-request and closing pages were visually inspected. Previous 97 chapter source hashes and Khanda 2 print PDF are unchanged. Live release verification remains separate.


## Chapter 25 continuation — 2026-10-30

44 numbered source positions, 13 context groups and 11 qualified records (5, 12, 19, 22, 24, 27, 30, 31, 37, 41, 44). Original PNG0059–0060 and supplied 55 TO 76 PDF22 plus overlapping 77 TO 98 PDF1–2 / printed59–60 were visually compared. Verse26's split was reunited. The unclear phrase in27 is explicitly gapped and its exact meaning withheld. The private starter transcription in14 was corrected to सर्वकर्ताऽभूत्तेषां against a native tight crop; it is not a claimed source variant. Previous98 chapter sources remain unchanged. Next:26.1, 77 TO 98 PDF2 / printed60 below the colophon.

Local checks passed:16 book tests,16 reader tests,5 SEO tests,60 responsive scenarios,negative audit gate,Pages compatibility and four EPUBCheck editions with zero errors/warnings. All44 exact source/meaning text units occur in the277-page K1 PDF after normalization. Opening,middle,explicit-gap and ending PDF pages plus phone/desktop reader renders were inspected. Source-qualified coverage is not a fully resolved or expert-reviewed translation. Live verification remains separate.


## Chapter 26 private candidate — 2026-10-31

43 numbered source positions, 13 context groups and five qualifications (17, 26, 29, 31, 38). Original PNG0060–0062 and supplied 77 TO 98 PDF2–4 / printed60–62 were visually compared; splits3 and29 were reunited. Verse31 has an explicit word-group gap and its exact meaning is withheld. Shukras vidya and the Garuda weapon are named without invented mantra formulas. Previous99 chapter sources are unchanged. Next:27.1, 77 TO 98 PDF4 / printed62 below the colophon.

Local checks passed:16 book tests,17 reader tests,5 SEO tests,63 responsive scenarios,negative audit gate,Pages compatibility and four EPUBCheck editions with zero errors/warnings. All43 exact source/meaning text units occur in the285-page K1 PDF after normalization. Actual phone/desktop reader renders and PDF278,282,283,285 were inspected. A self-contained private chapter HTML and an8-page PDF excerpt are available for review; the excerpt retains the full edition page numbers278–285.

Chapter26 is included in this scoped reading-draft release. Khanda1 coverage is Chapters1–26 with1386 numbered records and420 context groups; Khanda2 coverage remains Chapters1–74. Later private continuation is excluded. The five Chapter26 qualifications and explicit verse31 phrase gap remain. This is a qualified draft,not expert-reviewed final scripture. Deployment status must be checked against the actual release marker and CI result.
