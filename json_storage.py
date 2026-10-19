"""Lossless, content-addressed storage for cumulative review JSON documents.

The public API loads independent ordinary Python dicts/lists, including legacy
plain JSON. Writers must save through this module rather than edit the index.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

FORMAT = 'mudgala-shared-json-v1'
CHUNK_ITEMS = 64
INTERN_BYTES = 1024
MAX_SHARD_BYTES = 8 * 1024 * 1024


def canonical_bytes(value):
    """Order-sensitive JSON: preserves key/list order and scalar types."""
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _atomic_write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.json-storage-', delete=False) as f:
        temporary = Path(f.name)
        try:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def save_json_document(path, value):
    """Pack a complete logical document; publish its index atomically last.

    Immutable shard filenames include their checksums. Preflight all size limits
    before writes. Prune only obsolete shards in this document's own namespace;
    Git retains previous versions, and all logical historical records survive.
    """
    path = Path(path)
    objects = {}

    def intern(node):
        key = digest(node)
        objects.setdefault(key, node)
        return {'ref': key}

    def encode(v):
        if isinstance(v, dict):
            if not all(isinstance(k, str) for k in v):
                raise ValueError('JSON object keys must be strings')
            node = {'map': [[k, encode(x)] for k, x in v.items()]}
        elif isinstance(v, list):
            items = [encode(x) for x in v]
            if len(items) > CHUNK_ITEMS:
                return intern({'concat': [intern({'list': items[i:i+CHUNK_ITEMS]})
                                          for i in range(0, len(items), CHUNK_ITEMS)]})
            node = {'list': items}
        elif isinstance(v, str) and len(v.encode('utf-8')) >= INTERN_BYTES:
            return intern({'text': v})
        elif v is None or isinstance(v, (str, bool, int, float)):
            canonical_bytes(v)  # Reject NaN/Infinity instead of silently changing them.
            return v
        else:
            raise ValueError('Unsupported JSON value')
        return intern(node) if len(canonical_bytes(node)) >= INTERN_BYTES else node

    root = encode(value)
    buckets = {}
    for key, node in sorted(objects.items()):
        buckets.setdefault(key[:2], {})[key] = node
    namespace = Path('storage') / path.stem
    shards = []
    pending = []
    for bucket, entries in sorted(buckets.items()):
        raw = canonical_bytes({'storage_format': FORMAT + '-objects', 'objects': entries}) + b'\n'
        if len(raw) > MAX_SHARD_BYTES:
            raise ValueError('Storage shard exceeds 8 MiB; increase sharding before saving')
        checksum = hashlib.sha256(raw).hexdigest()
        relative = namespace / (bucket + '-' + checksum + '.json')
        shards.append({'bucket': bucket, 'file': relative.as_posix(), 'sha256': checksum, 'bytes': len(raw)})
        pending.append((path.parent / relative, raw))
    index = {'storage_format': FORMAT, 'logical_sha256': digest(value),
             'root': root, 'shards': shards}
    index_raw = canonical_bytes(index) + b'\n'
    if len(index_raw) > MAX_SHARD_BYTES:
        raise ValueError('Storage index exceeds 8 MiB')
    for target, raw in pending:
        if target.exists():
            if target.read_bytes() != raw:
                raise ValueError('Immutable storage shard changed: ' + str(target))
        else:
            _atomic_write(target, raw)
    _atomic_write(path, index_raw)
    keep = {p for p, _ in pending}
    for old in (path.parent / namespace).glob('*.json'):
        if re.fullmatch(r'[0-9a-f]{2}-[0-9a-f]{64}\.json', old.name) and old not in keep:
            old.unlink()
    return index


def load_json_document(path):
    """Resolve the index with hashes checked; repeated references never alias."""
    path = Path(path)
    index = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(index, dict) and str(index.get('storage_format', '')).startswith('mudgala-shared-json-') and index.get('storage_format') != FORMAT:
        raise ValueError('Unknown document storage format')
    if not isinstance(index, dict) or index.get('storage_format') != FORMAT:
        return index
    descriptors = {}
    for shard in index['shards']:
        bucket = shard['bucket']
        if not re.fullmatch(r'[0-9a-f]{2}', bucket) or bucket in descriptors:
            raise ValueError('Invalid/duplicate storage bucket')
        relative = Path(shard['file'])
        expected = Path('storage') / path.stem / (bucket + '-' + shard['sha256'] + '.json')
        if relative != expected or relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Storage shard path escapes document namespace')
        target = path.parent / relative
        if not target.resolve().is_relative_to(path.parent.resolve()):
            raise ValueError('Storage shard path escapes document directory')
        descriptors[bucket] = shard
    cache = {}
    checked = set()
    active = set()

    def object_node(key):
        if not isinstance(key, str) or not re.fullmatch(r'[0-9a-f]{64}', key):
            raise ValueError('Invalid content reference')
        bucket = key[:2]
        if bucket not in cache:
            shard = descriptors[bucket]
            raw = (path.parent / shard['file']).read_bytes()
            if len(raw) != shard['bytes'] or hashlib.sha256(raw).hexdigest() != shard['sha256']:
                raise ValueError('Storage shard checksum mismatch')
            doc = json.loads(raw)
            if doc['storage_format'] != FORMAT + '-objects':
                raise ValueError('Unknown storage shard format')
            cache[bucket] = doc['objects']
        node = cache[bucket][key]
        if key not in checked:
            if digest(node) != key:
                raise ValueError('Content object checksum mismatch')
            checked.add(key)
        return node

    def decode(node, depth=0):
        if depth > 128:
            raise ValueError('Storage nesting exceeds limit')
        if not isinstance(node, dict):
            if isinstance(node, list):
                raise ValueError('Untagged storage list')
            return node
        if len(node) != 1:
            raise ValueError('Malformed storage node')
        kind, value = next(iter(node.items()))
        if kind == 'ref':
            if value in active:
                raise ValueError('Cyclic content reference')
            active.add(value)
            try:
                return decode(object_node(value), depth + 1)
            finally:
                active.remove(value)
        if kind == 'text' and isinstance(value, str):
            return value
        if kind == 'list':
            return [decode(x, depth + 1) for x in value]
        if kind == 'concat':
            result = []
            for x in value:
                chunk = decode(x, depth + 1)
                if not isinstance(chunk, list):
                    raise ValueError('Non-list storage chunk')
                result.extend(chunk)
            return result
        if kind == 'map':
            result = {}
            for k, v in value:
                if not isinstance(k, str) or k in result:
                    raise ValueError('Invalid/duplicate logical key')
                result[k] = decode(v, depth + 1)
            return result
        raise ValueError('Unknown storage node')

    result = decode(index['root'])
    if digest(result) != index['logical_sha256']:
        raise ValueError('Logical document checksum mismatch')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['pack', 'export'])
    parser.add_argument('path', type=Path)
    parser.add_argument('destination', nargs='?', type=Path)
    args = parser.parse_args()
    document = load_json_document(args.path)
    if args.action == 'pack':
        if args.destination:
            parser.error('pack does not take a destination')
        save_json_document(args.path, document)
    else:
        if not args.destination or args.destination.resolve() == args.path.resolve():
            parser.error('export requires a separate destination')
        _atomic_write(args.destination, json.dumps(document, ensure_ascii=False, indent=2).encode('utf-8') + b'\n')
