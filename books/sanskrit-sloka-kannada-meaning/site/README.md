# Static Next.js book reader

Run `npm ci`, `npm run build`, then `npm test`.

The prebuild runs the parent Python book generator and derives route data from its exact grouped XHTML, copying shared assets and the EPUB. Next.js exports crawlable chapter HTML into `out/`. Generated data/assets/output are ignored; canonical scripture remains in the parent book. Scope:18chapters/985pairs and290short semantic groups. Original contents entries do not create nonexistent chapter routes.

Canonical production host: https://mudgalapurana.com . Kannada/English metadata, Book/Chapter JSON-LD, sitemap and robots use this host. No invented author or full-khanda/ranking/indexing claim. Configure Vercel Root Directory as `books/sanskrit-sloka-kannada-meaning/site`, Next.js framework. Domain/DNS association is separate; use exact provider records and preserve unrelated DNS. Python3 is required during build.
