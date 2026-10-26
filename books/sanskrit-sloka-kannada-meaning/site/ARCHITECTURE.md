# Shared library, reader and release workflow

## Current public boundary

Only Khanda1 Chapters1–18,985 numbered pairs and290 short contextual groups are public candidates. Existing uncertainty flags remain. Khanda2 Chapter1 verses1–6 and all corresponding source/review records are preserved privately outside the checkout; no draft text, scans, route, search entries or downloads enter this release. Private Khanda1Chapter19 is also excluded. This is a partial edition, not expert-certified or complete.

## Shared architecture

`/` → `/kn/` → `/kn/mudgala-purana/` → `/khanda-1/` → chapter.14native-label language cards use shared components; only Kannada has reading routes. Unavailable languages are non-links, excluded from the sitemap, and never represented as translated editions. No flags or cultural stereotypes. Existing `/khanda-1/1/` through18 and `/prarambha/` retain readable content and stable anchors, with canonicals pointing to the new hierarchy.23real canonical pages are indexed; search results are noindex.

- `../book.json` and `../chapters/khanda-XX/chapter-XXX.xhtml`: canonical manifest, source pairs, ordering and group boundaries. Keep verse IDs khanda-aware (`kh01-ch001-v001`).
- `../review/verse-source-records.json`: retained original Devanagari, Kannada transliteration/meanings, provenance and uncertainty. Do not silently change doctrine or claim expert review.
- `../styles/book.css`: shared fonts and theme tokens, used by HTML, EPUB and print sources. `../styles/print.css`: shared A4 print overrides. Original fonts and OFL licenses remain; compressed WOFF2 is a format-only derivative for web performance.
- `app/globals.css`: one responsive library/navigation/control layer for all locales and khandas.
- `lib/library.js`, `lib/labels.js`, `lib/paths.js`: language availability, native UI labels, cover metadata and canonical routes.
- `lib/Card.js`, `Reader.js`, `Downloads.js`, `Coverage.js`: shared presentation. Cover comes from the manifest; no copied chapter templates.
- `lib/ReaderTools.js`: accessible font/theme controls, device-local reading progress and copy-only correction reports with exact verse reference. No account, server-side personal state, automatic message or invented recipient.
- `lib/book.js`: truthful shared Book/Chapter JSON-LD and metadata. Full verses and meanings are in initial HTML; no ranking/indexing promises.

## Assets and icons

Approved sacred cover and5devotional artworks remain unchanged. Language cards share one generated unlettered manuscript decoration, served as384×256/768×512 WebP under `../assets/library/`; labels and availability remain real text. See `../review/library-artwork.json`. Web-only library images are excluded from EPUB resources. Text scans remain hidden and retained; drafts stay outside public asset directories.

`app/icon.svg`, `icon.png`32px, `favicon.ico`16/32/48px and `apple-icon.png`180px use a simple code-native open-book motif and shared Next metadata. All fonts, images, search data and downloads are same-origin. No separate CDN, native app or PWA installation flow.

## Exports and correction workflow

HTML, search and EPUB derive from canonical sources. `npm run downloads` regenerates partial combined/per-khanda PDFs from exactly those reader bodies using installed Chrome (`CHROME_EXECUTABLE` on Linux), waits for fonts and records source/file hashes. `npm run build` refuses stale/missing PDFs. Approved binaries plus their fingerprint manifest must travel with a correction. Downloaded copies do not live-update. A4 PDFs have embedded fonts, margins, contents and page numbers; no commercial-press certification without printer specifications. EPUB retains separate chapter XHTML and original-script review data stays outside the EPUB.

Reader progress and preferences are local to the browser. Correction reports are prepared/copied only; no email, GitHub issue or third-party service is contacted. Search uses displayed text and exact stable IDs; it does not invent mantra names or generate translations for other locales.

## Repeatable checks and CI before deployment

`npm run validate` builds production output; npm postbuild runs `test:seo` and reader regression tests. `vercel.json` explicitly sets `buildCommand` to `npm run build`, so normal Vercel builds cannot bypass the audit by racing a separate CI job. Tests cover initial HTML, unique title/description/canonical, robots, sitemap, semantic links/targets, language/alt metadata, JSON-LD, exact source/anchor mapping, unavailable-locale/private-draft exclusions, download signatures/fingerprints and payload budgets.

`npm run test:browser` checks touch/reflow, font/theme controls, local continue reading and copy-only verse reports with installed Chromium. Analytics is intercepted during this local test. `npm run test:gate` safely damages a copied output title and proves audit failure prevents a hypothetical artifact-staging marker; no deploy command is run. `npm run audit:lighthouse -- URL` is a supplementary free pinned13.5.0 audit of a running preview. Scores are environment-dependent, not a guarantee.

`.github/workflows/new-book-quality.yml` runs build gates, negative gate proof, canonical book tests and browser checks on source pushes/PRs. A manual publish request or explicit `[publish-website]` release commit stages only the validated compatibility reader after quality succeeds; the publish job additionally requires `needs.quality.result == success`. It replaces only `/sanskrit-kannada/` on gh-pages and verifies original root bytes. The marker is an execution trigger, not a substitute for current user approval. No force push or broad merge.

Remote Pages settings could not be read with current access (public API404; no authenticated gh CLI). Any pre-existing direct gh-pages branch-push deployment remains a possible bypass outside this workflow. Fully restricting that path requires separately authorized branch/deployment settings; none were changed. Vercel production publication should wait for the GitHub quality job, even though its own build gate runs the static audits again.

## Analytics and budget

Official `@vercel/analytics`2.0.1 mounts once via `@vercel/analytics/next` in the shared root server layout. A small client wrapper permits page views only and removes query/hash/credentials and extra custom data. No search-term tracking, identifiers, custom events or replay. Dashboard enablement is not exposed by available project controls and remains unverified. Live events are not claimed before deployment and observation. Standard setup: https://vercel.com/docs/analytics/quickstart . No plan/security/access change or paid add-on. Current resource is free and non-commercial; Hobby only, no checkout, promotions, paid services or purchases.
