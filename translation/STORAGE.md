# Coverage and unresolved registry storage

`coverage.json` and `unresolved-passages.json` are checksummed indexes. Their
complete logical documents are reconstructed by `json_storage.py` from immutable,
content-addressed JSON shards under `translation/storage/`. All other JSON files
retain their existing format. Never read these two indexes with `json.loads`
when you need the logical records, or edit their encoded nodes manually.

```python
from pathlib import Path
from json_storage import load_json_document, save_json_document

path = Path('translation/unresolved-passages.json')
registry = load_json_document(path)
# Make only the separately authorized record changes here.
save_json_document(path, registry)
```

Use the same API for `translation/coverage.json`. It accepts legacy plain JSON,
so isolated test fixtures and external full-document imports remain supported.
To inspect or edit a plain export outside the tracked tree:

```sh
python3 json_storage.py export translation/coverage.json /tmp/coverage-expanded.json
```

To import an edited full export, load it with `json.load`, then pass the complete
value to `save_json_document` at the canonical path. Stage both index files and
`translation/storage/` after any authorized update. The save operation writes
immutable shards before atomically replacing the index, then removes only
unreferenced shards in that document's own namespace. Git keeps previous versions.
No historical boundary or record is discarded from the current logical document.

The codec preserves dictionary order, list order, scalar types, Unicode, nulls,
unknown fields, flags and acceptance states. All containers are explicitly tagged
internally, so literal data resembling references is preserved as data. Shared
objects are decoded into independent mutable values: editing a new boundary
cannot modify an earlier one through aliasing. Cumulative arrays use stable
64-item chunks; repeated chunks and evidence values are stored once by SHA256.

The loader validates shard paths, file hashes, object hashes and the complete
order-sensitive logical document hash. Writers preflight an 8 MiB limit per
index/shard, leaving ample room below the hosting limit. The format needs only
Python's standard library. `tests/test_json_storage.py` tests corruption and
interrupted writes and replays both complete document migrations from the pre-migration Git commit
recorded in `storage-migration-equivalence.json`. That report also records the
verified equality of the actual migrated documents at migration time. Later
authorized adjudications may change logical records without rewriting this
historical migration receipt.

The migration changes storage only. Source TSVs, review artifacts, unresolved
history and the published HTML/EPUB are unchanged. Rebuilding and normal
provenance validation continue to use the same logical values.
