"""Validate this review checkpoint without modifying files (Python 3.10+)."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

def main():
    manifest=json.loads((ROOT/'manifest.json').read_text())
    checksums=json.loads((ROOT/'checksums.json').read_text())
    actual={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and p.name!='checksums.json' and '__pycache__' not in p.parts}
    assert actual==set(checksums), 'Unexpected or missing files'
    for name,digest in checksums.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, ('Checksum mismatch',name)
    all_ids=[]; totals={}
    for row in manifest['chapters']:
        chapter=json.loads((ROOT/row['source_file']).read_text())
        reading=(ROOT/row['reading_file']).read_text()
        entries=chapter['entries'];ids=[e['id'] for e in entries]
        assert len(ids)==len(set(ids)), ('Repeated ID',row['source_file'])
        assert [v for g in chapter['groups'] for v in g['verse_ids']]==ids, ('Group order',row['source_file'])
        assert len(entries)==row['records']
        assert len(chapter['groups'])==row['groups']
        assert not re.search(r'[\u0900-\u0963\u0966-\u097f]',reading), ('Devanagari letters in Kannada-script reading copy',row['reading_file'])
        for entry in entries:
            assert entry['sanskrit_kannada_script'] in reading
            assert entry['kannada_meaning'] in reading
            assert entry['meaning_status'] in {'pending','draft','qualified-draft','accepted-qualified-draft'}
        assert sum(e['meaning_status']=='pending' for e in entries)==row['pending_meanings']
        assert sum(e['meaning_status']=='accepted-qualified-draft' for e in entries)==row['accepted_qualified_meanings']
        k=str(row['khanda']);t=totals.setdefault(k,{'chapters':0,'records':0,'pending_meanings':0,'accepted_qualified_meanings':0})
        t['chapters']+=1
        for key in ('records','pending_meanings','accepted_qualified_meanings'):t[key]+=row[key]
        all_ids.extend(ids)
    assert len(all_ids)==len(set(all_ids))==manifest['total_records']
    for k,summary in totals.items():
        for key,value in summary.items():assert value==manifest['khandas'][k][key]
    for path in ROOT.rglob('*'):
        if path.suffix in {'.json','.md'}:
            text=path.read_text()
            assert not any(s in text for s in ('/Users/','/workspace/','/tmp/','/home/','/root/','private-review','thread_id','agent_id')), ('Local or coordination metadata',str(path))
    for path in ROOT.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
            assert (path.parent/target).is_file(), ('Broken relative link',str(path),target)
    print(f'PASS: {len(manifest["chapters"])} chapters, {len(all_ids):,} unique records, all hashes, text pairs, groups and links.')
    print('This validates preservation and structure, not linguistic or theological correctness.')

if __name__=='__main__':main()
