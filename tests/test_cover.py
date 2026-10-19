"""Kannada cover text, native geometry and EPUB cover designation regressions."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,struct,shutil,subprocess,sys,tempfile,unittest
from lxml import etree,html
ROOT=Path(__file__).resolve().parents[1]
ASSET='assets/mudgala-front-cover-kannada-v5.png'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

class Cover(unittest.TestCase):
 def test_native_cover_title_and_conjunct_proof(self):
  proof=json.loads((ROOT/'book/cover-source/typography-v5.json').read_text())
  self.assertEqual(proof['title'],'ಮುದ್ಗಲ ಪುರಾಣ')
  self.assertEqual(proof['lines'][0]['codepoints'],['cae','cc1','ca6','ccd','c97','cb2'])
  self.assertEqual([x['text']for x in proof['lines']],['ಮುದ್ಗಲ','ಪುರಾಣ'])
  self.assertEqual(struct.unpack('>II',(ROOT/'book'/ASSET).read_bytes()[16:24]),(1024,1536))
  self.assertEqual(sha(ROOT/proof['font_file']),proof['font_sha256'])
  self.assertEqual(sha(ROOT/proof['artwork_file']),proof['artwork_sha256'])
  self.assertEqual(sha(ROOT/proof['final_file']),proof['final_sha256'])
  self.assertTrue(proof['font_loaded']);self.assertEqual(proof['pixels_changed_outside_title_area'],0)
 def test_epub_designates_and_embeds_the_html_cover(self):
  doc=html.fromstring((ROOT/'book/index.html').read_bytes());img=doc.xpath('//*[@id="cover"]//img')[0]
  self.assertEqual(img.get('src'),ASSET);self.assertEqual((img.get('width'),img.get('height')),('1024','1536'))
  self.assertEqual(doc.xpath('//*[@id="cover"]//h1/text()'),['ಮುದ್ಗಲ ಪುರಾಣ'])
  with ZipFile(ROOT/'dist/mudgala_purana.epub')as z:
   p=etree.fromstring(z.read('content.opf'));covers=p.xpath('//*[local-name()="item" and @properties="cover-image"]')
   self.assertEqual([e.get('href')for e in covers],[ASSET]);self.assertEqual(z.read(ASSET),(ROOT/'book'/ASSET).read_bytes())
   x=etree.fromstring(z.read('cover.xhtml'));self.assertEqual(x.xpath('//*[local-name()="img"]/@src'),[ASSET])
   self.assertNotIn('assets/mudgala-front-cover-final-v4.png',z.namelist())
 def fixture(self,extra=''):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);base=Path(tmp.name);(base/'book/assets').mkdir(parents=True)
  for n in ['build_epub.py','reference_only.py']:shutil.copyfile(ROOT/n,base/n)
  for n in ['TiroKannada-Regular.ttf','TiroKannada-OFL.txt']:shutil.copyfile(ROOT/'book/assets'/n,base/'book/assets'/n)
  shutil.copyfile(ROOT/'book'/ASSET,base/'book/assets/renamed-cover.png')
  (base/'book/index.html').write_text('<main><section id="cover" class="cover"><h1>ಮುದ್ಗಲ ಪುರಾಣ</h1><img src="assets/renamed-cover.png"/>'+extra+'</section></main>')
  return base
 def test_cover_designation_follows_renamed_html_asset(self):
  base=self.fixture();subprocess.run([sys.executable,str(base/'build_epub.py')],check=True,stdout=subprocess.DEVNULL)
  with ZipFile(base/'dist/mudgala_purana.epub')as z:
   q=etree.fromstring(z.read('content.opf'));self.assertEqual(q.xpath('//*[local-name()="item" and @properties="cover-image"]/@href'),['assets/renamed-cover.png'])
 def test_ambiguous_multiple_cover_images_rejected(self):
  base=self.fixture('<img src="assets/renamed-cover.png"/>');r=subprocess.run([sys.executable,str(base/'build_epub.py')],capture_output=True,text=True);self.assertNotEqual(r.returncode,0);self.assertIn('Cover must contain exactly one image',r.stderr)

if __name__=='__main__':unittest.main()
