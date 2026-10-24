# Sanskrit text verification — supplied PDF pages 1–15

Primary: user-supplied `1 TO 25.pdf`, SHA256 00dc9890c76c3845d228055b1695908f8b3f12415244bda829885cf6c6896391. Direct visual comparison of 320dpi renderings of PDF14–15 (printed1–2); existing user-supplied OCR was secondary, never newly generated. OCR discrepancies were not substituted for the scans.

## Coverage and order
PDF1: invocation and dhyana now selectable Devanagari, each above its Kannada meaning. PDF2: existing five devotional Sanskrit/Kannada pairs retained. PDF3–13: existing contents and illustrations retained; no new chapter content inferred from contents. PDF14: opening, verses1–20 and first half21. PDF15: second half21, verses22–46 and only opening word47. Verse21 reunited into one pair with both source-page references. Every numbered Sanskrit entry is immediately followed by its Kannada paragraph, with stable IDs v001–v047. No PDF16+ used.

## Unresolved printed readings
Visible `⟦…⟧` marks only unreadable clusters; no guessed completion:
- PDF14 verse10: consonant cluster in final word after तदर्थमभव.
- PDF15 verse25: cluster between भृगु and मुद्गलोयोगी; existing Kannada interpretation remains provisional.
- PDF15 verse32: final cluster after साक्षात्संशय.
- PDF15 verse40: cluster between युग and तिक्रमणं; Kannada remains incomplete and marked.
- PDF15 verse46: noun after प्राणोऽ, before मित्युक्तं. Kannada no longer guesses अग्नि/भूत.

## Comparison findings
Retained source spellings including ध्याये, लोमहर्षण in11 versus रोमहर्षण elsewhere, तेयं in28, स्वयेच्छया in29, and nonstandard devotional spellings on PDF2. Verse24 visually reads मुनिदत्ते शुभासने (not the prior mistaken interpretation). Verse38 zoom reads दातृत्वात्पुण्यदानि च; Kannada now reflects giving the four aims and merit, instead of an unresolved conjectural praise phrase. Corrected directly mismatching Kannada in24,29,31,36,38,41,43,46. Other existing Kannada uncertainty daggers remain; this is not a claim of guru-approved critical Sanskrit or a fully complete chapter.

## Retention
All8 textual scan wrappers remain inline display:none and retained in assets. Cover and5 devotional images remain visible. No validation commentary is inserted into reading content. Devanagari Tiro Sanskrit font bundled under OFL. Contents-name uncertainty from prior batch remains unchanged.

## Build and rendering validation
Eight unit/regression checks pass. EPUBCheck5.4.0: zero errors/warnings. Chrome desktop1100px and mobile390px:48 ordered Sanskrit/Kannada pairs, selectable Sanskrit, bundled Tiro Devanagari Sanskrit loaded, no horizontal overflow, eight textual scan wrappers hidden and six artwork images visible. Verse21 occurs once and verse47 contains only कुत्र. Rendered screenshots visually inspected.
