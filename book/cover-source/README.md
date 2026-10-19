# Kannada cover v5

The title-free artwork was supplied as Library
`libfile_d355f332d17881918c1b0b6197d13e99` and retained unchanged here.
The final cover adds only these two centered Unicode lines:

ಮುದ್ಗಲ
ಪುರಾಣ

`tools/render_cover.cjs` uses the bundled Tiro Kannada Regular font and browser
text shaping, including the ದ್ಗ conjunct. It draws the artwork at its native
1024×1536 resolution without scaling, then warm-gold type inside
x180–845/y90–335. `typography-v5.json` records the Unicode, font and image hashes,
bounds and a pixel comparison confirming zero changes outside that title area.
The artwork and finished PNG are not a claim of 300-dpi print quality.

To reproduce with Node and Playwright available:

```sh
node tools/render_cover.cjs book/cover-source/title-free-artwork-v5.png book/assets/TiroKannada-Regular.ttf /tmp/mudgala-cover-v5.png
```

Set `PLAYWRIGHT_MODULE` and `CHROME_PATH` if using a separately installed runtime.
Normal HTML and EPUB builds use the finished asset and do not require Node.
The previous v4 asset remains in repository history and the checkout for traceability;
the reading edition and EPUB designate only v5 as the active cover.
