# Isolated qualified review reader

`/kn/mudgala-purana/review/` exposes the saved November 17 review checkpoint separately from the canonical edition. It is a draft, not expert verified. The tracked queue has 985 accepted-qualified and 548 pending records; this does not imply the remaining draft records are verified and excludes separate Khanda 9 chapters 25–41 qualifications.

`prepare-review.py` reads the immutable November 12 baseline, verifies November 17 delta hashes, replaces entries in their original positions by stable ID, and applies complete group/colophon replacements. Its 300 chapters and 16,734 records are generated under `.generated/review/`, never added to canonical book data, search, sitemap or download generation. Checkpoint sources are not modified.

The separate server-rendered static routes use existing source context groups: Kannada-script Sanskrit above a divider, then exactly corresponding numbered Kannada meanings. Each record retains its source and original Devanagari, numbering flags, current meaning status and historical qualifications in a disclosure. No modernization or inferred corrections are applied. Draft pages are noindex, follow and linked once from the canonical book index. Existing EPUB/PDF links still refer to the unchanged published canonical edition (Khanda 1 chapters 1–18).

`npm run build` includes `scripts/test-review.py`, checking all exported chapters, exact source strings, stable IDs and meaning mappings, internal links, actual noindex HTML and sitemap isolation. Baseline/delta integrity and status counts fail closed in prebuild.

Acceptance URLs:
- `/kn/mudgala-purana/review/khanda-5/2/#kh05-ch002-v016`: current accepted-qualified-draft, with earlier pending/uncertain prose retained as historical source qualifications.
- `/kn/mudgala-purana/review/khanda-5/41/#kh05-ch041-v035`: unresolved numbered placeholder, unchanged.
