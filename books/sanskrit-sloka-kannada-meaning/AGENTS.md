# Mudgala Purana — Sanskrit sloka and Kannada meaning

These instructions apply to this new book directory. Preserve the existing original book and all unrelated files, branches, pending corrections and uncommitted changes.

## Before each batch

Read this AGENTS.md, the current coverage/uncertainty ledger and the [pre-batch validation checklist](review/pre-batch-validation-checklist.md) before starting a batch. Apply the reading requirements from the beginning of the work rather than postponing layout and mapping checks until the book is complete.

## Source and fidelity

- Use the user-supplied PDF scans as the source of truth. Read the actual pages visually at adequate resolution. The existing user-supplied OCR may be a secondary cross-reference; do not generate new OCR without approval.
- Preserve doctrine, Sanskrit words, sequence, verse numbers, speaker changes and source-page references. Do not guess unclear characters, supply missing verse endings, or silently normalize unusual source readings.
- Mark unresolved readings honestly in the reading text when necessary, with details in a separate review report. Keep editorial and validation commentary outside the reading content. Accuracy takes priority over speed.
- A reference image from another book is a layout reference only. Do not copy its scripture, meanings, numbering or source assumptions.

## Current reader format

- Present Sanskrit-language slokas as selectable text transliterated into **Kannada script**. This changes script, not Sanskrit words or meaning. Preserve long/short vowels, aspiration, dental/retroflex distinctions, conjuncts, anusvara, visarga, avagraha, punctuation and verse numbering.
- Retain the original Devanagari text separately in review/source data for verification; do not display it as the reader's sloka text.
- Group slokas by **related context and complete available thoughts**, not a fixed count of three, four or any other number. Review the actual Sanskrit and Kannada meanings, speaker changes, narrative lead-ins and connected explanations. Put each context group above a divider and its **numbered Kannada meanings in exactly the same order** below. Group by explicit stable verse IDs and validate every sloka-to-meaning reference, number, text and order. Record a concise boundary rationale in a separate review file, never in the reader view. Do not merge explanations or rewrite translations to create a group. A group ending at the current source limit may remain explicitly incomplete.
- Preserve the single reunited verse21 across its source-page split. Retain partial verses as partial; do not complete them from an unapproved next page.
- Use restrained deep-maroon slokas, readable dark meanings in the light theme, and accessible colors in dark themes. Use type scale and spacing as well as color. Keep the book clean, without development labels, placeholder commentary, extra navigation chrome or explanatory demo text.
- Keep the approved cover and devotional artwork visible. Hide textual page screenshots and Sanskrit text strips with `display:none`, while retaining their files and source references. Do not hide illustrations merely because they originated as scans.
- Ensure mobile, tablet, desktop and zoomed reading work without horizontal scrolling, clipped glyphs or broken Kannada shaping. Bundle appropriate fonts and support accessible language metadata and selectable text.

## Source structure and builds

- Maintain chapter files grouped by khanda, shared cover/assets/styles/fonts, and an explicit manifest for titles, order, metadata, source references and reading groups.
- Build web reading, portable HTML and EPUB from the same canonical sources. Keep separate XHTML chapters internally in the EPUB. Preserve canonical per-verse Sanskrit/meaning associations even when the reader groups multiple verses.
- Keep tooling minimal and maintainable. Do not start new content conversion, invent sample scripture, or introduce unnecessary frameworks.

## Validation and publication

- For every batch, verify source-page coverage, omissions/duplicates, verse order/numerals, exact Sanskrit/meaning mappings, transliteration fidelity, uncertainty markers, relative assets, fonts and rendered output. Run appropriate build/regression tests and EPUBCheck. Inspect desktop/mobile rendering and responsive layouts, including zoom.
- Follow the user's current request and active approval settings for repository publication.
- Publish only scoped new-book changes on the feature branch and the existing additive `/sanskrit-kannada/` Pages path. Preserve the old book/root and unrelated paths. Do not force push, broadly merge unrelated work, or change deployment settings without authorization.
- Verify exact remote commit, CI/Pages success, live HTTP/rendered output and downloadable EPUB before claiming publication. Verify original-book preservation. Report actual blockers and saved work accurately.

## Superseded choices

- Devanagari reader-facing slokas were replaced by Kannada-script Sanskrit transliteration.
- One-sloka/one-meaning display and the later fixed-three grouping are superseded by context-based groups with matching numbered meanings. Group size alone is never evidence of a meaningful boundary. Keep groups short enough to read comfortably, generally around2–5 where natural; split longer passages at complete subtopics. Any larger indivisible group needs a recorded rationale; never split a dependent sentence merely to meet a count.
- Development-preview disclaimers and visible text facsimiles were removed/hidden. Do not restore them during rebuilds.

Current coverage and unresolved readings belong in [review/current-batch-status.md](review/current-batch-status.md), rather than being inferred from contents entries or older plans.

## Next.js reader and custom domain

The `site/` app derives static, crawlable chapter pages from these same canonical sources. Keep scripture, numbered meaning associations, short context groups and uncertainty marks unchanged during site work. Rebuild shared EPUB from the existing generator; do not create a separate translation source. Preserve the original book and existing Pages deployment.

The requested custom-domain target is `mudgalapurana.com`; earlier `mudugalpurana.com` was a typo. Keep canonical metadata, sitemap, robots and structured data consistent with the corrected host. Use truthful edition coverage, no invented author attribution or ranking/indexing guarantees. Verify actual deployment, domain/TLS and redirects separately before claiming live success.
