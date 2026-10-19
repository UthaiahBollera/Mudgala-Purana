import copy
import json
import unittest
from pathlib import Path
from lxml import html
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reference_only import validate, render, digest, display_text, validate_rendered

DATA = json.loads((Path(__file__).parent/'fixtures/reference-only-reviewed-corpus.json').read_text())

class ReferenceOnlyTests(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(DATA)
    def changed(self, record):
        record['draft_canonical_sha256'] = digest(record['draft_original'])
        record['manifest_canonical_sha256'] = digest(record['draft_original']['original_manifest'])
    def test_full_delivered_corpus(self):
        self.assertEqual(validate(self.data), {'reference_only_chapters':17,'editorial_locators':264,'verified_verse_total':None})
    def test_literal_page_hash_rejects_change(self):
        self.data['chapters'][0]['literal_pages'][0]['text'] += 'x'
        with self.assertRaises(AssertionError): validate(self.data)
    def test_draft_digest_rejects_change(self):
        self.data['chapters'][0]['draft_original']['segments'][0]['kannada_translation'] += 'x'
        with self.assertRaises(AssertionError): validate(self.data)
    def test_false_literal_span_rejected(self):
        r=self.data['chapters'][0];r['draft_original']['segments'][0]['source_spans'][0]['raw_source'] += 'x';self.changed(r)
        with self.assertRaises(AssertionError): validate(self.data)
    def test_body_gap_rejected_even_with_valid_literal_text(self):
        r=self.data['chapters'][0];s=r['draft_original']['segments'][0]['source_spans'][0];s['char_start']+=1;s['raw_source']=s['raw_source'][1:];self.changed(r)
        with self.assertRaises(AssertionError): validate(self.data)
    def test_body_overlap_rejected(self):
        r=self.data['chapters'][0];sp=r['draft_original']['segments'][0]['source_spans'];sp.append(copy.deepcopy(sp[0]));self.changed(r)
        with self.assertRaises(AssertionError): validate(self.data)
    def test_verified_verse_id_rejected(self):
        r=self.data['chapters'][0];r['draft_original']['segments'][0]['segment_key']='kh9-ch25-v1';self.changed(r)
        with self.assertRaises(AssertionError): validate(self.data)
    def test_translation_acceptance_must_remain_null(self):
        r=self.data['chapters'][0];r['draft_original']['segments'][0]['accepted_translation']='accepted';self.changed(r)
        with self.assertRaises(AssertionError): validate(self.data)
    def test_partial_argon_evidence_cannot_disappear(self):
        r=self.data['chapters'][0];r['draft_original']['original_manifest']['partial_saved_Argon_supplement']=None;self.changed(r)
        with self.assertRaises(AssertionError): validate(self.data)
    def test_no_verified_source_keys_can_be_invented(self):
        r=self.data['chapters'][0];r['draft_original']['original_manifest']['stable_verse_keys']=[[9,25,1]];self.changed(r)
        with self.assertRaises(AssertionError): validate(self.data)
    def test_scan_availability_cannot_be_upgraded(self):
        r=self.data['chapters'][0];r['draft_original']['original_manifest']['source_parts'][0]['scan_available']=True;self.changed(r)
        with self.assertRaises(AssertionError): validate(self.data)
    def test_display_transliteration_cannot_emend_letters(self):
        r=next(x for x in self.data['chapters']if x['draft_original']['chapter']==32);r['display_transliterations']['kh09-ch032-loc005'][0]['kannada']='ಹೆಸರು'
        with self.assertRaises(AssertionError): validate(self.data)
    def test_chapter35_does_not_swallow_chapter36(self):
        r=next(x for x in self.data['chapters']if x['draft_original']['chapter']==35);s=r['draft_original']['colophon']['source_spans'][0];p=next(x for x in r['literal_pages']if x['reference_page']==s['reference_page']);s['char_end_exclusive']=1500;s['raw_source']=p['text'][s['char_start']:1500];self.changed(r)
        with self.assertRaises(AssertionError): validate(self.data)
    def test_render_preserves_locator_ids_and_escapes_text(self):
        r=self.data['chapters'][0];r['draft_original']['segments'][0]['kannada_translation'] += '<script>alert(1)</script>';self.changed(r)
        doc=html.fromstring('<main>'+''.join(render(self.data))+'</main>')
        self.assertFalse(doc.xpath('//script|//button|//form'))
        self.assertEqual(len(doc.xpath('//p[@class="reference-translation"]')),264)
        self.assertEqual(len(doc.xpath('//tr[@data-reference-chapter]')),17)
        self.assertFalse(doc.xpath('//tr[@data-chapter]'))
        self.assertFalse(doc.xpath('//p[starts-with(@id,"kh9-ch25-v")]'))
        self.assertIn('<script>',doc.get_element_by_id('kh09-ch025-loc001').text_content())
        self.assertIn('ದೃಢಪಡಿಸಿದ ಶ್ಲೋಕಸಂಖ್ಯೆಗಳಲ್ಲ',doc.text_content())
        self.assertTrue(doc.get_element_by_id('kh09-ch041-terminal-closure').text_content())
    def test_all_reference_links_resolve(self):
        doc=html.fromstring('<main>'+''.join(render(self.data))+'</main>');ids=doc.xpath('//@id');self.assertEqual(len(ids),len(set(ids)))
        for a in doc.xpath('//a'):
            self.assertIn(a.get('href')[1:],ids)
    def test_literal_script_change_leaves_original_draft_unchanged(self):
        r=next(x for x in self.data['chapters']if x['draft_original']['chapter']==32);b=r['draft_original']['segments'][4]
        self.assertIn('पलटी',b['kannada_translation']);self.assertIn('ಪಲಟೀ',display_text(r,b));self.assertEqual(r['draft_canonical_sha256'],digest(r['draft_original']))

    def test_rendered_text_is_verified(self):
        doc=html.fromstring('<main>'+''.join(render(self.data))+'</main>')
        self.assertEqual(validate_rendered(self.data,doc)['editorial_locators'],264)
        doc.get_element_by_id('kh09-ch025-loc001').text='ಬದಲಾವಣೆ'
        with self.assertRaises(AssertionError):validate_rendered(self.data,doc)
    def test_source_only_notice_cannot_disappear(self):
        doc=html.fromstring('<main>'+''.join(render(self.data))+'</main>')
        node=doc.get_element_by_id('reference-chapter-kh9-25-1')
        node.remove(node.xpath('./p[@class="caption"]')[0])
        with self.assertRaises(AssertionError):validate_rendered(self.data,doc)
    def test_rendered_source_pointer_cannot_change(self):
        doc=html.fromstring('<main>'+''.join(render(self.data))+'</main>')
        doc.get_element_by_id('kh09-ch025-loc001').set('data-source-spans','gb:invented:PT1')
        with self.assertRaises(AssertionError):validate_rendered(self.data,doc)
    def test_fabricated_mantra_is_rejected(self):
        from lxml import etree
        doc=html.fromstring('<main>'+''.join(render(self.data))+'</main>')
        etree.SubElement(doc.get_element_by_id('reference-chapter-kh9-25-1'),'p',{'class':'mantra'}).text='ಊಹೆ'
        with self.assertRaises(AssertionError):validate_rendered(self.data,doc)

if __name__=='__main__':unittest.main()
