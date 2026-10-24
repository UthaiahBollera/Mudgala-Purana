# Pre-batch and release validation checklist

Use this checklist before and during each new batch. Coverage and unresolved readings come from `current-batch-status.md`, not the contents pages or historical reports.

- Read the scoped AGENTS.md and the current project requirements before translating or editing.
- Verify the supplied scan file, actual PDF page, printed page, chapter boundary and exact resume verse. Read the pixels; existing suppliedOCR is secondary. Keep original Sanskrit and source references, and mark unclear readings without guessing.
- Present Sanskrit in Kannada script with accurate individually numbered Kannada meanings. Keep stable verse IDs and verify every association, order, omission and duplicate, including page splits.
- Choose short context-based groups from complete thoughts, speaker changes and natural subtopics. Avoid long blocks that separate verses too far from their meanings. Do not use a fixed count. If a longer group is genuinely indivisible, record why outside the reader. Do not split a dependent sentence just to meet a range.
- Put the grouped verses above the divider and their numbered meanings below in exactly matching order. Keep all wording and uncertainty markers when changing layout.
- Inspect phone, tablet, desktop and zoomed rendering early in the batch: Kannada shaping, comfortable spacing, contrast, wrapping and no clipping or horizontal scrolling. Keep approved cover/devotional artwork visible and text scans hidden with assets retained.
- Verify the single-source web and EPUB builds, manifest/source provenance, mapping regression tests and reputable EPUB validation. Review the resulting reader pixels; a successful build alone does not establish readability or textual correctness.
- Preserve the original book and unrelated work. Keep unfinished or incompletely validated draft chapters out of the canonical release. Record exact coverage and remaining uncertainties without claiming whole-khanda completion.

## Current release check

The18-chapter/985-pair release was checked against these requirements:290 context groups, no group longer than5 in this edition, with1-verse complete framing units retained. This range describes the reviewed edition; it is not an inflexible rule for future text.39longer groups were split at documented natural subtopics; canonical scripture and individual meaning bytes were unchanged.16tests,cleanEPUBCheck and10responsive browser scenarios passed. The deployed HTML/EPUB matched the build and the original root remained byte-identical. Detailed rationale is in `readability-grouping-adjustment.json`.
