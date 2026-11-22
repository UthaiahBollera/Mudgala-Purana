"""Web-only paired presentation for Khanda 1; preserve source text and anchors."""
from xml.etree import ElementTree as ET


def wrap_pairs(group, slokas, meanings, meaning_id):
    """Move original nodes rather than cloning scripture or duplicating anchors."""
    verse_ids = [verse.attrib['id'] for verse in slokas]
    by_id = {meaning_id(row): row for row in meanings}
    assert len(verse_ids) == len(by_id) == len(meanings)
    assert verse_ids == list(by_id), (group.attrib['id'], verse_ids, list(by_id))
    for child in list(group):
        group.remove(child)
    for verse in slokas:
        row = by_id[verse.attrib['id']]
        pair = ET.SubElement(group, 'div', {'class': 'ornamental-pair'})
        pair.append(verse)
        row.insert(0, ET.Element('span', {'class': 'ornamental-pill'}))
        row[0].text = 'ಭಾವಾರ್ಥ'
        pair.append(row)


def fidelity(chapter):
    # Preserve every source paragraph, markup/qualification and link association
    # verbatim. Compare as collections because the verse/meaning flow changes.
    return (
        sorted(ET.tostring(el, encoding='unicode') for el in chapter.iter('p')),
        sorted(el.attrib['id'] for el in chapter.iter() if 'id' in el.attrib),
        sorted(el.attrib['href'] for el in chapter.iter('a')),
        sorted(el.attrib['data-meaning-for'] for el in chapter.iter()
               if 'data-meaning-for' in el.attrib),
    )


def canonical_chapter(markup):
    main = ET.fromstring(markup)
    before = fidelity(main)
    for group in main.findall('.//section[@class="verse-group"]'):
        slokas, _, meanings = group
        assert slokas.get('class') == 'group-slokas' and meanings.get('class') == 'group-meanings'
        wrap_pairs(group, list(slokas), list(meanings), lambda row: row.attrib['data-meaning-for'])
    assert fidelity(main) == before
    return ET.tostring(main, encoding='unicode')


def draft_chapter(markup):
    chapter = ET.fromstring('<root>' + markup + '</root>')
    before = fidelity(chapter)
    for group in chapter.findall('./section[@class="review-group"]'):
        slokas = group.findall('./section[@class="review-sloka"]')
        meanings = group.findall('./section[@class="review-meaning"]')
        assert len(group) == len(slokas) + len(meanings) + 1
        assert group[len(slokas)].tag == 'hr'
        wrap_pairs(group, slokas, meanings, lambda row: row.find('div').attrib['data-meaning-for'])
        for pair in group:
            heading = pair[0].find('h2')
            assert heading is not None
            heading.tag = 'div'
            heading.set('class', 'num')
            heading.find('a').set('aria-label', 'ಶ್ಲೋಕ ' + heading.find('a').text + ' ನೇರ ಕೊಂಡಿ')
            number = pair[1].find('h3')
            assert number is not None
            number.tag = 'span'
            number.set('class', 'ornamental-repeated-number')
            number.set('aria-hidden', 'true')
    assert fidelity(chapter) == before
    return ''.join(ET.tostring(el, encoding='unicode') for el in chapter)
