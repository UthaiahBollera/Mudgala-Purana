# Deployment handoff

App ready locally; Vercel production deployment is **not completed**.

- Requested project URL: https://vercel.com/uthaiah-bbs-projects/mudgala_purana
- Existing GitHub repository: UthaiahBollera/Mudgala-Purana
- Source branch: book/sanskrit-kannada-blank-starter
- Root Directory: books/sanskrit-sloka-kannada-meaning/site
- Framework: Next.js; use pinned package-lock and Node22+.
- Build: npm run build. Requires Python3 and access to parent source files (`sourceFilesOutsideRootDirectory`), because prebuild reuses the existing book generator.
- Static export: out/. Generated content/assets are ignored, rebuilt from canonical sources. No environment secrets are needed by the reader.
- Canonical domain: https://mudgalapurana.com . Configure www as a permanent redirect to apex; app vercel.json contains that host redirect.

## Confirmed blocker

The connected Vercel team is readable, but project lookup returns404 and both filtered and unfiltered project lists return no projects. No existing authenticated local Vercel CLI session was found. Corrected domain DNS points to Vercel nameservers and HTTPS responds with a Vercel404. Thus DNS/TLS reach Vercel, but the requested project/domain association cannot be verified or changed with current access. No project, domain, DNS, nameserver or OAuth changes were made. Obtain the correct project ID/URL and make that project available to the existing connection before deployment; any new access grant requires action-time approval.

## Local verification

18chapters,985pairs,290groups (1–5verses); no new translation. Static generation succeeds;3site checks verify exact chapter bodies, metadata,20sitemapURLs,robots,Book/Chapter JSON-LD and EPUB equality.16book regressiontests and EPUBCheck pass. Real browser checks cover every chapter on mobile plus12home/frontmatter/reader width checks, fonts/selectability/hidden scans, no overflow. Chapter19 has no route. Original source and Pages files remain unchanged.

After access is resolved, connect the existing repository, select this source branch/root, deploy the tested revision, then verify live HTML/canonical/sitemap/robots/chapter navigation/EPUB and domain/TLS/www redirect. Search indexing is a later external process and has not been confirmed.
