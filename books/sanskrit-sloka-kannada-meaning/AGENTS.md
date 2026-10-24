# Mudgala Purana — Sanskrit sloka and Kannada meaning

These instructions apply to this new book directory. Preserve the existing original book and all unrelated files, branches, pending corrections and uncommitted changes.

## Source and fidelity

- Use the user-supplied PDF scans as the source of truth. Read the actual pages visually at adequate resolution. The existing user-supplied OCR may be a secondary cross-reference; do not generate new OCR without approval.
- Preserve doctrine, Sanskrit words, sequence, verse numbers, speaker changes and source-page references. Do not guess unclear characters, supply missing verse endings, or silently normalize unusual source readings.
- Mark unresolved readings honestly in the reading text when necessary, with details in a separate review report. Keep editorial and validation commentary outside the reading content. Accuracy takes priority over speed.
- A reference image from another book is a layout reference only. Do not copy its scripture, meanings, numbering or source assumptions.

## Current reader format

- Present Sanskrit-language slokas as selectable text transliterated into **Kannada script**. This changes script, not Sanskrit words or meaning. Preserve long/short vowels, aspiration, dental/retroflex distinctions, conjuncts, anusvara, visarga, avagraha, punctuation and verse numbering.
- Retain the original Devanagari text separately in review/source data for verification; do not display it as the reader's sloka text.
- For Chapter1, show **three slokas together**, a divider, then their **numbered Kannada meanings in exactly the same order**. The final group may contain fewer entries. Group by explicit stable verse IDs, and validate every sloka-to-meaning reference, number, text and order. Do not merge explanations or rewrite translations to create a group.
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
- The user has granted standing approval to commit, push and publish future requested changes to this new book at the same repository and preview path. Do not ask again for routine publication within that requested scope. This does not authorize unrequested content, unrelated repositories, deletion, destructive operations or bypassing a blocked action. Honor any later private/local-only restriction.
- Publish only scoped new-book changes on the feature branch and the existing additive `/sanskrit-kannada/` Pages path. Preserve the old book/root and unrelated paths. Do not force push, broadly merge unrelated work, or change deployment settings without authorization.
- Verify exact remote commit, CI/Pages success, live HTTP/rendered output and downloadable EPUB before claiming publication. Verify original-book preservation. Report actual blockers and saved work accurately.

## Superseded choices

- Devanagari reader-facing slokas were replaced by Kannada-script Sanskrit transliteration.
- One sloka immediately followed by its meaning was replaced, for Chapter1, by groups of three slokas followed by the matching numbered meanings.
- Development-preview disclaimers and visible text facsimiles were removed/hidden. Do not restore them during rebuilds.
- Earlier requests for a separate publication confirmation for every batch are superseded by standing publication approval for future requested new-book changes. Unrequested future pages remain out of scope.

Current coverage and unresolved readings belong in [review/current-batch-status.md](review/current-batch-status.md), rather than being inferred from contents entries or older plans.
