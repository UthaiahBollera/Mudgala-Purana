"""Isolated schema-2 provenance regression tests; never modify the working data."""
import ast
import copy
import re
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CODE = (ROOT/'validate_source_review.py').read_text().split("raw = (ROOT/'book/index.html').read_text()", 1)[0]
BOOK_ID = 'Lh0FEQAAQBAJ'
PAGE = f'gb:{BOOK_ID}:PT897'
BOOK_ID_2 = 'fZcHEQAAQBAJ'
PAGE_2 = f'gb:{BOOK_ID_2}:PT15'

class GoogleSourceValidation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT/'translation', self.root/'translation')
        (self.root/'.git').symlink_to(ROOT/'.git', target_is_directory=True)
        (self.root/'build_book.py').symlink_to(ROOT/'build_book.py')
        reviewed = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', 'dcd504671e5ed48c84344c20174bb7c6b28c37f8', 'translation'], cwd=ROOT).decode().splitlines()
        for file in (self.root/'translation').glob('batch-*.tsv'):
            if str(file.relative_to(self.root)) not in reviewed:
                file.unlink()
        self.row = {'khanda':'1', 'chapter':'53', 'verse':'40', 'source_pages':PAGE, 'type':'translation', 'text':'ಪರೀಕ್ಷೆ'}
        self.review = {'source_kind':'google_books', 'book_id':BOOK_ID, 'verses':[{'key':[1,53,40], 'source_pages':PAGE, 'text':'ಪರೀಕ್ಷೆ', 'source_sanskrit':'गणेश', 'review_status':'accepted'}]}
        self.batch = {'file':'batch-google-test.tsv', 'sha256':'', 'source_kind':'google_books', 'book_id':BOOK_ID, 'source_pages':[{'id':PAGE, 'page_id':'PT897', 'url':f'https://books.google.com/books?id={BOOK_ID}&pg=PT897'}], 'coverage_boundary':'google-books-test', 'review_status':'accepted', 'review_file':'translation/google-test-review.json', 'review_sha256':'', 'added_keys':[[1,53,40]], 'boundary_completions':[]}
        self.manifest = {'schema_version':2, 'reviewed_commit':'dcd504671e5ed48c84344c20174bb7c6b28c37f8', 'batches':[self.batch]}
        self.registry = None
        self.extra_batches = []
        self.coverage = {'chapter_counts_by_khanda':{}, 'partial_keys':[], 'non_narrative_source_pages':[], 'source_pages':[PAGE]}

    def tearDown(self):
        self.tmp.cleanup()

    def run_case(self, accepted=False):
        coverage = json.loads((self.root/'translation/coverage.json').read_text())
        for row, review, batch, boundary in [(self.row, self.review, self.batch, self.coverage), *self.extra_batches]:
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=list(row), delimiter='\t', lineterminator='\n')
            writer.writeheader(); writer.writerow(row)
            data = out.getvalue().encode()
            (self.root/'translation'/batch['file']).write_bytes(data)
            batch['sha256'] = hashlib.sha256(data).hexdigest()
            review_data = json.dumps(review).encode()
            (self.root/batch['review_file']).write_bytes(review_data)
            batch['review_sha256'] = hashlib.sha256(review_data).hexdigest()
            coverage[batch['coverage_boundary']] = boundary
        (self.root/'translation/batch-manifest.json').write_text(json.dumps(self.manifest))
        (self.root/'translation/coverage.json').write_text(json.dumps(coverage))
        if self.registry is not None:
            (self.root/'translation/unresolved-passages.json').write_text(json.dumps(self.registry))
        result = subprocess.run(['python3', '-c', f'__file__={str(self.root/"validate_source_review.py")!r}\n'+CODE], capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, accepted, result.stderr)

    def test_valid_review(self):
        self.run_case(True)

    def configure_unresolved(self):
        text = 'ಪರೀಕ್ಷೆ (ಈ ಅರ್ಥಕ್ಕೆ ಹೆಚ್ಚಿನ ಪರಿಶೀಲನೆ ಅಗತ್ಯ.)'
        issues = [{'status':'open', 'description':'Synthetic unresolved test reading'}]
        self.row.update(type='translation-review', text=text)
        self.review['verses'][0].update(text=text, issues=issues, review_status='accepted_with_unresolved_reading')
        self.coverage['review_required_keys'] = [[1,53,40]]
        self.registry = {'records':[{'id':'kh1-ch53-v40', 'book_id':BOOK_ID, 'chapter':53,
            'verse_start':40, 'verse_end':40, 'status':'open_google_books_reading_question',
            'issues':issues, 'source_sanskrit':'गणेश', 'google_books_pages':['PT897'],
            'google_books_page_url':f'https://books.google.com/books?id={BOOK_ID}&pg=PT897'}]}

    def test_valid_unresolved(self):
        self.configure_unresolved()
        self.run_case(True)

    def test_unresolved_missing_notice(self):
        self.configure_unresolved()
        self.row['text'] = self.review['verses'][0]['text'] = 'ಪರೀಕ್ಷೆ'
        self.run_case()

    def test_unresolved_hidden_notice(self):
        self.configure_unresolved()
        self.row['text'] = self.review['verses'][0]['text'] = 'ಪರೀಕ್ಷೆ [(ಪರಿಶೀಲನೆ ಅಗತ್ಯ)]'
        self.run_case()

    def test_unresolved_missing_registry(self):
        self.configure_unresolved()
        self.registry['records'] = []
        self.run_case()

    def test_unresolved_wrong_registry_url(self):
        self.configure_unresolved()
        self.registry['records'][0]['google_books_page_url'] += '0'
        self.run_case()

    def test_unresolved_missing_coverage(self):
        self.configure_unresolved()
        self.coverage['review_required_keys'] = []
        self.run_case()

    def test_unresolved_falsely_accepted(self):
        self.configure_unresolved()
        self.review['verses'][0]['review_status'] = 'accepted'
        self.run_case()

    def configure_completion(self):
        old = None
        for path in [self.root/'translation/narrative.tsv', *sorted((self.root/'translation').glob('batch-*.tsv'))]:
            with path.open() as stream:
                for row in csv.DictReader(stream, delimiter='\t'):
                    if (int(row.get('khanda') or 1), int(row['chapter']), int(row['verse'])) == (1,53,39):
                        old = {field:row[field] for field in ('source_pages','type','text')}
        assert old and old['type'] == 'translation-partial'
        self.row.update(verse='39', source_pages='133,'+PAGE)
        self.review['verses'][0].update(key=[1,53,39], source_pages=self.row['source_pages'])
        self.batch['added_keys'] = []
        self.batch['boundary_completions'] = [{'key':[1,53,39], 'old_row':old,
            'new_row':{field:self.row[field] for field in old}, 'rationale':'Synthetic test completion',
            'source_evidence':'Synthetic evidence, not publication content', 'review_status':'accepted'}]

    def test_valid_boundary_completion(self):
        self.configure_completion()
        self.run_case(True)

    def test_boundary_drops_historical_source(self):
        self.configure_completion()
        self.row['source_pages'] = self.review['verses'][0]['source_pages'] = PAGE
        self.batch['boundary_completions'][0]['new_row']['source_pages'] = PAGE
        self.run_case()

    def test_unlisted_boundary_replacement(self):
        self.configure_completion()
        self.batch['boundary_completions'] = []
        self.run_case()

    def test_unknown_page(self):
        self.row['source_pages'] = self.review['verses'][0]['source_pages'] = f'gb:{BOOK_ID}:PT898'
        self.run_case()

    def test_wrong_book(self):
        self.batch['book_id'] = 'wrong'
        self.run_case()

    def test_empty_page_id(self):
        self.batch['source_pages'][0]['page_id'] = 'PT'
        self.run_case()

    def test_wrong_url(self):
        self.batch['source_pages'][0]['url'] += '0'
        self.run_case()

    def test_missing_review(self):
        self.review['verses'] = []
        self.run_case()

    def test_changed_translation(self):
        self.review['verses'][0]['text'] = 'ಬದಲಾವಣೆ'
        self.run_case()

    def test_empty_sanskrit(self):
        self.review['verses'][0]['source_sanskrit'] = ''
        self.run_case()

    def test_unlisted_addition(self):
        self.batch['added_keys'] = []
        self.run_case()

    def test_numeric_pdf_addition(self):
        self.row['source_pages'] = self.review['verses'][0]['source_pages'] = '134'
        self.run_case()

    def test_duplicate_page(self):
        self.batch['source_pages'].append(copy.deepcopy(self.batch['source_pages'][0]))
        self.run_case()

    def test_missing_coverage_page(self):
        self.coverage['source_pages'] = []
        self.run_case()

    def configure_second_khanda(self, unresolved=False):
        if unresolved:
            self.configure_unresolved()
        row, review, batch, boundary = copy.deepcopy((self.row, self.review, self.batch, self.coverage))
        row.update(khanda='2', chapter='1', verse='1', source_pages=PAGE_2)
        review['book_id'] = BOOK_ID_2
        review['verses'][0].update(key=[2,1,1], source_pages=PAGE_2)
        batch.update(file='batch-google-test-2.tsv', book_id=BOOK_ID_2,
                     review_file='translation/google-test-review-2.json',
                     coverage_boundary='google-books-test-2', added_keys=[[2,1,1]],
                     source_pages=[{'id':PAGE_2, 'page_id':'PT15',
                                    'url':f'https://books.google.com/books?id={BOOK_ID_2}&pg=PT15'}])
        # Lexical replay order is part of the provenance contract.
        self.batch['file'] = 'batch-google-test-1.tsv'
        boundary['source_pages'] = [PAGE, PAGE_2]
        boundary['chapter_counts_by_khanda'] = {'1':[40], '2':[1]}
        if unresolved:
            boundary['review_required_keys'] = [[1,53,40], [2,1,1]]
            record = copy.deepcopy(self.registry['records'][0])
            record.update(id='kh2-ch1-v1', khanda=2, chapter=1, verse_start=1, verse_end=1,
                          book_id=BOOK_ID_2, google_books_pages=['PT15'],
                          google_books_page_url=f'https://books.google.com/books?id={BOOK_ID_2}&pg=PT15')
            self.registry['records'].append(record)
        self.extra_batches.append((row, review, batch, boundary))
        self.manifest['batches'].append(batch)
        return row, review, batch, boundary

    def test_valid_two_khanda_batches(self):
        self.configure_second_khanda()
        self.run_case(True)

    def test_valid_two_khanda_unresolved_registry(self):
        self.configure_second_khanda(unresolved=True)
        self.run_case(True)

    def test_second_batch_cannot_drop_previous_pages(self):
        _, _, _, boundary = self.configure_second_khanda()
        boundary['source_pages'] = [PAGE_2]
        self.run_case()

    def test_second_batch_cannot_drop_previous_unresolved(self):
        _, _, _, boundary = self.configure_second_khanda(unresolved=True)
        boundary['review_required_keys'] = [[2,1,1]]
        self.run_case()

    def test_second_khanda_rejects_first_book_even_if_consistently_labeled(self):
        row, review, batch, boundary = self.configure_second_khanda()
        wrong_page = f'gb:{BOOK_ID}:PT15'
        row['source_pages'] = review['verses'][0]['source_pages'] = wrong_page
        review['book_id'] = batch['book_id'] = BOOK_ID
        batch['source_pages'] = [{'id':wrong_page, 'page_id':'PT15',
                                 'url':f'https://books.google.com/books?id={BOOK_ID}&pg=PT15'}]
        boundary['source_pages'] = [PAGE, wrong_page]
        self.run_case()

    def test_first_khanda_rejects_second_book_even_if_consistently_labeled(self):
        self.row['source_pages'] = self.review['verses'][0]['source_pages'] = PAGE_2
        self.review['book_id'] = self.batch['book_id'] = BOOK_ID_2
        self.batch['source_pages'] = [{'id':PAGE_2, 'page_id':'PT15',
                                     'url':f'https://books.google.com/books?id={BOOK_ID_2}&pg=PT15'}]
        self.coverage['source_pages'] = [PAGE_2]
        self.run_case()

    def test_second_khanda_wrong_review_book(self):
        _, review, _, _ = self.configure_second_khanda()
        review['book_id'] = BOOK_ID
        self.run_case()

    def test_second_khanda_matching_volume_metadata(self):
        _, review, batch, _ = self.configure_second_khanda()
        review['volume'] = batch['volume'] = 2
        self.run_case(True)

    def test_second_khanda_wrong_review_volume(self):
        _, review, _, _ = self.configure_second_khanda()
        review['volume'] = 1
        self.run_case()

    def test_second_khanda_wrong_batch_volume(self):
        _, _, batch, _ = self.configure_second_khanda()
        batch['volume'] = 1
        self.run_case()

    def test_second_khanda_wrong_source_token(self):
        row, review, _, _ = self.configure_second_khanda()
        row['source_pages'] = review['verses'][0]['source_pages'] = PAGE
        self.run_case()

    def test_second_khanda_registry_requires_khanda_identity(self):
        self.configure_second_khanda(unresolved=True)
        del self.registry['records'][1]['khanda']
        self.run_case()

    def test_second_khanda_registry_rejects_wrong_volume(self):
        self.configure_second_khanda(unresolved=True)
        self.registry['records'][1]['book_id'] = BOOK_ID
        self.run_case()

    def test_source_token_helpers_enforce_volume_and_preserve_numeric_ids(self):
        for filename in ('validate_book.py', 'validate_source_review.py'):
            with self.subTest(validator=filename):
                tree = ast.parse((ROOT/filename).read_text())
                nodes = [node for node in tree.body if
                         isinstance(node, ast.FunctionDef) and node.name == 'source_ids' or
                         isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'GOOGLE_BOOKS_BY_KHANDA' for t in node.targets)]
                namespace = {'re':re}
                exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, 'exec'), namespace)
                source_ids = namespace['source_ids']
                self.assertEqual(source_ids('14,133,'+PAGE, 1), {'14','133',PAGE})
                self.assertEqual(source_ids(PAGE_2, 2), {PAGE_2})
                for value, khanda in ((PAGE,2), (PAGE_2,1), ('133',2), (PAGE_2,3),
                                      ('gb:unknown:PT15',None), (PAGE_2+','+PAGE_2,2)):
                    with self.assertRaises(AssertionError, msg=(filename,value,khanda)):
                        source_ids(value, khanda)

if __name__ == '__main__':
    unittest.main()
