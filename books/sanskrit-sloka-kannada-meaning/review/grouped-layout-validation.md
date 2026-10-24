# Three-sloka grouped reading layout

The user's reference photo from another book was visually inspected. It places several slokas above a divider and numbered Kannada meanings below. No reference-book scripture, prose or numbering was imported. The user approved three slokas per group, emphasizing correct meaning arrangement.

## Mapping and unchanged content

Canonical chapter XHTML retains its existing stable-ID verse/meaning associations. Neither the canonical chapter, frontmatter nor archived Devanagari text is edited in this layout change. An explicit manifest lists stable IDs for16 groups:1–3,4–6,...,43–45,46–47(partial). The builder resolves each ID to its original sloka and its original Kannada paragraph; it does not zip independent lists of texts by position. The invocation remains separate, and frontmatter retains its prior arrangement.

All47 numbered Sanskrit-language Kannada-script entries map to exactly47 numbered Kannada meanings. The first15 groups contain3 entries each; the last contains46 and only the visible opening of47. Verse21 occurs once, with both PDF14/15 references retained. Each sloka's displayed number and ending number are checked against its stable ID, and its meaning repeats the same displayed number.

Four outputs are checked against the canonical source for every one of the94 numbered-entry paragraphs: combined web, portable HTML, separate chapter web XHTML and separate chapter EPUB XHTML. Paragraph XML/text, including uncertainty markup, is unchanged. No sloka or meaning is omitted, duplicated, reordered or rewritten. The opening word47 stays `ಕುತ್ರ`; both its sloka and meaning rows carry the reader-facing status `ಅಪೂರ್ಣ` outside the original paragraph.

Sanskrit uncertainty clusters10/25/32/40/46 remain unchanged. Manifest meaning-gap flags38/40 are retained; the generated meaning row38 receives a minimal dagger outside its unchanged paragraph, while40 retains its existing dagger. Detailed source uncertainty reports remain separate from reading text.

## Structure and rendering

Each group contains a sloka block, a horizontal divider, and a meaning block, in that DOM/reading order. Each meaning row has an explicit `data-meaning-for` referring to its sloka's stable ID. Maroon verses and dark high-contrast meanings remain differentiated by type size and spacing as well as color. Layout follows a single responsive column rather than a fixed photographed page.

Web and EPUB use the same generated grouped chapter. Original source data stays paired for reliable maintenance. All8 textual scan wrappers remain hidden and retained, and the cover plus5 devotional artwork images remain visible. No new PDF pages are used, and no reference-book content is inserted.

## Validation

- 12 regression tests pass, including exact per-ID paragraph comparison across all4 outputs, complete ordering/coverage, matching verse numbers, reunited21, partial47 and rejecting swapped/duplicate/missing IDs or misnumbered verses.
- EPUBCheck5.4.0: zero errors or warnings.
- Chrome light/dark checks at320/375/768/1100px plus200% layout zoom at1100px: all47 sloka/meaning mappings and numbering match canonical source in every scenario;16 groups correctly stack slokas/divider/meanings; no horizontal overflow or clipped sloka text; Kannada font loads and text is selectable. Mobile and desktop screenshots visually inspected.
- Frontmatter remains13 sections/372 contents entries, with15 total source-page sections through PDF15. No original-book files are changed.

Project instructions and current content boundary are now documented separately in `../AGENTS.md` and `current-batch-status.md` with explicit user approval for their repository publication. These review/instruction files are not included in the reading web or EPUB outputs.
