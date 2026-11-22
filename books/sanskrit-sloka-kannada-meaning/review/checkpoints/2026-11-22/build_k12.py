#!/usr/bin/env python3
"""Prepare a deterministic no-asset review snapshot from pinned, public XHTML.

Run with input/ populated by git archive of the exact branch commit recorded in
validation. Only numbered text, saved grouping, invocation and closing text are
included. The separately served original edition and facsimile assets are untouched.
"""
import gzip
import hashlib
import html
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

X = "{http://www.w3.org/1999/xhtml}"
ESC = html.escape
HERE = Path(__file__).resolve().parent
BOOK = HERE / "input/books/sanskrit-sloka-kannada-meaning"
rows = []
stats = {}
sources = {}
all_ids = set()

def body(e):
    """Emit escaped text and explicitly allow the saved uncertainty annotation."""
    acc = ESC(e.text or "")
    for c in e:
        assert c.tag == X + "abbr" and c.get("class") == "reading-uncertain" and not len(c)
        acc += ('<abbr class="reading-uncertain" title="'
                + ESC(c.get("title", "")) + '">' + ESC(c.text or "") + '</abbr>' + ESC(c.tail or ""))
    return acc

def para(e, default):
    lang = e.get("lang", default)
    assert lang in ("sa-Knda", "kn")
    attrs = ""
    if e.get("data-reading-uncertain") == "true":
        attrs += ' data-reading-uncertain="true"'
    if "title" in e.attrib:
        attrs += ' title="' + ESC(e.get("title")) + '"'
    return f'<p lang="{lang}" style="white-space:pre-wrap"{attrs}>{body(e)}</p>'

for k, expected in [(1, 54), (2, 74)]:
    stats[k] = Counter()
    for ch in range(1, expected + 1):
        prefix = f"kh{k:02d}-ch{ch:03d}"
        path = BOOK / f"chapters/khanda-{k:02d}/chapter-{ch:03d}.xhtml"
        raw = path.read_bytes()
        sources[str(path.relative_to(BOOK))] = hashlib.sha256(raw).hexdigest()
        doc = ET.fromstring(raw)
        m = doc.find(f".//{X}main")
        assert m is not None and m.get("id") == prefix
        indexed = {}
        for u in m.iter(X + "div"):
            if u.get("class") != "unit":
                continue
            ident, number, pair = u.get("id"), u[0], u[1]
            if ident == prefix + "-invocation":
                continue
            assert ident not in all_ids and re.fullmatch(prefix + r"-v[0-9]{3}", ident)
            assert number.get("class") == "num" and pair.get("class") == "verse-pair"
            first, second = tuple(pair)
            assert first.tag == second.tag == X + "p"
            assert first.get("lang") == "sa-Knda" and second.get("lang") == "kn"
            assert number.text and number.text.isdecimal()
            assert int(number.text) == int(ident.rsplit("v", 1)[-1]) == int(u.get("data-unit"))
            indexed[ident] = (number.text, first, second)
            all_ids.add(ident)
            stats[k]["pairs"] += 1
            stats[k]["source_marked"] += first.get("data-reading-uncertain") == "true"
            stats[k]["literal_script_gap"] += "⟦…⟧" in "".join(first.itertext())
        if k == 1:
            grouping = BOOK / ("review/context-grouping.json" if ch == 1 else f"review/context-grouping-chapter-{ch:03d}.json")
            data = grouping.read_bytes()
            sources[str(grouping.relative_to(BOOK))] = hashlib.sha256(data).hexdigest()
            groups = [(g["id"], g["verses"]) for g in json.loads(data)["groups"]]
        else:
            # The pinned K2 XHTML has paired units, not reviewed grouping boundaries.
            groups = [(prefix + f"-pair-{i:03d}", [ident]) for i, ident in enumerate(indexed, 1)]
        assert [ident for _, ids in groups for ident in ids] == list(indexed)
        assert len({ident for ident, _ in groups}) == len(groups)
        for g, _ in groups:
            assert re.fullmatch(prefix + r"-(?:group|pair)-[0-9]+", g)
        parts = []
        invocations = [e for e in m.iter(X + "div") if e.get("id") == prefix + "-invocation"]
        for inv in invocations:
            parts.append(f'<section class="review-entry" id="{prefix}-invocation">' + "".join(para(e, "kn") for e in inv[1]) + "</section>")
        for group_id, verse_ids in groups:
            parts.append(f'<section id="{group_id}" class="review-group">')
            for ident in verse_ids:
                number, first, _ = indexed[ident]
                parts.append(f'<section class="review-sloka" id="{ident}" tabindex="-1"><h2><a href="#{ident}">{ESC(number)}</a></h2>{para(first, "sa-Knda")}</section>')
            parts.append("<hr/>")
            for ident in verse_ids:
                number, _, second = indexed[ident]
                parts.append(f'<section class="review-meaning"><h3>{ESC(number)}</h3><div data-meaning-for="{ident}">{para(second, "kn")}</div></section>')
            parts.append("</section>")
        closing = [e for e in m.iter() if e.get("id") == prefix + "-colophon"]
        assert len(closing) == 1
        end = closing[0]
        closing_html = para(end, "kn") if end.tag == X + "p" else "".join(para(e, "kn") for e in end)
        parts.append(f'<section class="review-entry" id="{prefix}-colophon"><h2>ಅಧ್ಯಾಯ ಸಮಾಪ್ತಿ</h2>{closing_html}</section>')
        html_out = "".join(parts)
        for pattern in (r'<section class="review-sloka" id="([^"]+)"', r'data-meaning-for="([^"]+)"'):
            assert re.findall(pattern, html_out) == list(indexed)
        assert len(set(re.findall(r'\bid="([^"]+)"', html_out))) == len(re.findall(r'\bid="([^"]+)"', html_out))
        rows.append({"khanda": k, "chapter": ch, "slug": f"khanda-{k}/{ch}", "count": len(indexed), "html": html_out})
        stats[k].update({"chapters": 1, "groups": len(groups), "invocations": len(invocations)})
encoded = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode()
out = gzip.compress(encoded, compresslevel=9, mtime=0)
(HERE / "k12-review.json.gz").write_bytes(out)
report = {"source_commit": "0122c9d402896821784cd4503ab01d47d31da78f", "stats": stats, "sources": sources, "sha256": hashlib.sha256(out).hexdigest(), "json_sha256": hashlib.sha256(encoded).hexdigest()}
(HERE / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k:v for k,v in report.items() if k != "sources"}, indent=2))
