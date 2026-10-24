# Deployment handoff

Production reader is live at https://mudgalapurana.com .

- Requested project URL: https://vercel.com/uthaiah-bbs-projects/mudgala_purana
- Existing GitHub repository: UthaiahBollera/Mudgala-Purana
- Source branch: book/sanskrit-kannada-blank-starter
- Root Directory: books/sanskrit-sloka-kannada-meaning/site
- Framework: Next.js; use pinned package-lock and Node22+.
- Build: npm run build. Requires Python3 and access to parent source files (`sourceFilesOutsideRootDirectory`), because prebuild reuses the existing book generator.
- Static export: out/. Generated content/assets are ignored, rebuilt from canonical sources. No environment secrets are needed by the reader.
- Canonical domain: https://mudgalapurana.com . Configure www as a permanent redirect to apex; app vercel.json contains that host redirect.

## Production status

Production is live at https://mudgalapurana.com on project `prj_NfTnmIS5BbCbiRpkp6RSbbFNK6ib`. Exact-ID connector calls without a team parameter work; team-scoped lookup returns404. Production metadata verifies the repository, branch and source commit. Build settings were updated to Next.js, Node24, this root directory, npm ci and npm run build, with parent-source access enabled. Persistent automatic future-push Git linkage is not exposed sufficiently by this connector; the release explicitly targets the exact GitHub repository and commit.

Apex HTTPS works; HTTP redirects to HTTPS. The separate www hostname currently has a TLS mismatch. Adding its redirect was rejected by automatic approval review as requiring specific authorization; no alias or DNS change was made. The app host redirect does not itself attach that hostname to Vercel.

## Local verification

18chapters,985pairs,290groups (1–5verses); no new translation. Static generation succeeds;3site checks verify exact chapter bodies, metadata,20sitemapURLs,robots,Book/Chapter JSON-LD and EPUB equality.16book regressiontests and EPUBCheck pass. Real browser checks cover every chapter on mobile plus12home/frontmatter/reader width checks, fonts/selectability/hidden scans, no overflow. Chapter19 has no route. Original source and Pages files remain unchanged.

Live checks confirmed18chapters/985pairs/290groups,20sitemapURLs,robots and responsive fonts/hidden scans. EPUB font MIME types are explicitly registered for consistent Linux/macOS builds. Search indexing has not been confirmed.
