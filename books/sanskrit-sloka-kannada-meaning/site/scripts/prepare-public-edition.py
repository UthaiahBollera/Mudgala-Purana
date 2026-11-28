"""Build the public nine-khanda reader from the pinned proofread edition."""
from pathlib import Path
import gzip, hashlib, re

site = Path(__file__).resolve().parents[1]
input_dir = site / "reader-edition"
output_dir = site / "public" / "sanskrit-kannada"
output_dir.mkdir(parents=True, exist_ok=True)
INPUT_BLOBS = ["1922f0a7ff754a88dcf5c28488ca7b495cb7075b","9ad7f0f3738737ade2cf826a868bbf72d3318191","583190f09dbb680f61f716b709cb49815e839715","455fa19f71d58eb0a2b41c28b26639cdec876d47","be65526df5e34b41fe6ff3b7b01955054b555d8f","a5203dcf81ed677f895da6b7c31e2cd349504bd2","52d80827c16b4f2f341b28fcc5b93ef4f79209b8","d5bf665c3af25a089b3e8bd44799e8488d24e34a","91de517ff7e00854c6e1c6c7d2f465d14e77824e"]
expected = (54, 74, 51, 52, 45, 45, 16, 50, 41)
digits = "೦೧೨೩೪೫೬೭೮೯"
banners = (
    "ಓದುವ ಕರಡು · ಅಂತಿಮ ಪ್ರಕಟಣೆ ಅಲ್ಲ.",
    "ಓದುವ ಕರಡು. ಮೂಲಪಾಠ ಅಥವಾ ಅರ್ಥ ಇನ್ನೂ ಖಚಿತವಾಗದ ಕಡೆ ಗುರುತುಗಳನ್ನು ಉಳಿಸಲಾಗಿದೆ.",
    "ಖಾಸಗಿ ಓದುಗರ ಕರಡು. ಅಂತಿಮ ಪರಿಶೀಲನೆ ಅಥವಾ ಪ್ರಕಟಣೆ ಆಗಿಲ್ಲ.",
)
workflow = re.compile(r'<details><summary>ಪರಿಶೀಲನಾ ಟಿಪ್ಪಣಿ</summary>.*?</details>', re.S)
chapter_pattern = re.compile(r'<section id="ch(\d+)"')
verse_pattern = re.compile(r'<p\b[^>]*lang="sa-Knda"[^>]*>.*?</p>', re.S)
meaning_pattern = re.compile(r'<p\b[^>]*(?:class="meaning"|lang="kn")[^>]*>.*?</p>', re.S)
style = """
<style>
:root{color-scheme:light}body{color:#312822}nav{line-height:2.1}
.review-group{border-bottom:0!important}.review-group hr{display:none}
a:focus-visible{outline:2px solid #700d28;outline-offset:3px}
.public-nav{font-size:.92em}.editorial{font-size:.88em}
</style>"""
origin = "https://mudgalapurana.com/sanskrit-kannada"
for k, chapters in enumerate(expected, 1):
    data = (input_dir / f"khanda-{k}.html.gz").read_bytes()
    expected_sha = INPUT_BLOBS[k-1]
    gitsha = hashlib.sha1(("blob %d\0" % len(data)).encode() + data).hexdigest()
    if gitsha != expected_sha:
        raise ValueError(f"Khanda {k} source does not match the verified edition")
    original = gzip.decompress(data).decode("utf-8")
    public = original
    for banner in banners:
        markup = f"<p>{banner}</p>"
        if public.count(markup) > 1:
            raise ValueError(f"Khanda {k}: repeated draft label")
        public = public.replace(markup, "")
    public = workflow.sub("", public)
    if "<details" in public or re.search(r"<script\b|\bon[a-z]+=", public, re.I):
        raise ValueError(f"Khanda {k} contains unapproved markup")
    if any(x in public for x in (*banners, "private appendix", "ಖಾಸಗಿ ಅನುಬಂಧ", "saved for review")):
        raise ValueError(f"Khanda {k} contains private editorial text")
    if chapter_pattern.findall(public) != [str(x) for x in range(1, chapters + 1)]:
        raise ValueError(f"Khanda {k}: chapter inventory differs")
    if verse_pattern.findall(original) != verse_pattern.findall(public) or meaning_pattern.findall(original) != meaning_pattern.findall(public):
        raise ValueError(f"Khanda {k}: verse or meaning text changed")
    if k == 5 and ('id="kh05-ch041-v035"' not in public or "ಕ್ರಮವು ೩೪ರಿಂದ ನೇರವಾಗಿ ೩೬ಕ್ಕೆ ಸಾಗುತ್ತದೆ" not in public):
        raise ValueError("The source numbering note must be retained")
    public = public.replace("</head>", f'<link rel="canonical" href="{origin}/khanda-{k}/">{style}</head>', 1)
    public = public.replace("<body>", '<body><p class="public-nav"><a href="../">ಎಲ್ಲ ಖಂಡಗಳು</a> · <a href="/">ಮುಖಪುಟ</a></p>', 1)
    chapter_dir = output_dir / f"khanda-{k}"
    chapter_dir.mkdir(exist_ok=True)
    (chapter_dir / "index.html").write_text(public, encoding="utf-8")
    print(f"Public Khanda {k}: {chapters} chapters; source Sanskrit and Kannada verified")
