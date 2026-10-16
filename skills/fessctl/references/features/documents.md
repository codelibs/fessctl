# Bulk document indexing (fessctl `documents`)

## What it is
Index many documents in one request, straight into the search index, without a crawl. This is the admin `documents/bulk` API. It only indexes; to change or delete documents afterwards use `fessctl searchlist`.

Available in every Fess version fessctl supports (14.19.2, 15.6.1, 15.7.0, 15.8.0, 15.9.0); the request body is identical in all of them.

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `bulk` | Index the documents in a file, or on stdin when the argument is `-`. | `<file>` |

The input is read as one of:
- a JSON array of document objects,
- an object `{"documents": [...]}`,
- NDJSON: one document object per line (blank lines are ignored).

Always reconfirm with `fessctl documents bulk --help`.

## Document fields
`url` and `title` are required. When a document leaves them out, the server fills `role` (the guest roles), `boost` (1.0), `content_length`, `click_count`, `favorite_count`, `last_modified` and `timestamp`. Any other index field (`title`, `content`, `label`, `lang`, `mimetype`, ...) is passed through. Arrays (`role`, `label`, `lang`, `anchor`, `virtual_host`) must be JSON arrays.
```json
{"url": "https://www.example.com/a.html", "title": "A page", "content": "text", "label": ["docs"]}
```

## Response shape
```json
{
  "response": {
    "status": 0,
    "items": [
      {"result": "CREATED", "id": "0ed4f2...e6e1"},
      {"result": "BAD_REQUEST", "message": "mapper_parsing_exception ..."}
    ]
  }
}
```
`items` lists one entry per submitted document, in order. `id` is the index `_id`, not the `doc_id` that `fessctl searchlist` uses.

## Gotchas
- Validation is all-or-nothing: a document without `url` or `title`, or with a value that does not convert (`boost` or `click_count` that is not a number, for example), fails the whole request with status 1 and nothing is indexed.
- Failures at indexing time (a value the index mapping cannot parse) fail only that document. The other documents are indexed, the response has `status` 9, `fessctl` prints every item and exits with code 9.
- The document `_id` is derived from the URL and the role list, so indexing the same URL again with the same roles replaces the document, while the same URL with different roles is a second document.
- `bulk` sends everything in a single request with a short client timeout; split very large files into several calls.
- Documents become searchable about a second later (index refresh).
- There is no delete in this API. Remove what you indexed with `fessctl searchlist delete-by-query`.

## Examples
```bash
fessctl documents bulk docs.json
fessctl documents bulk docs.ndjson --output json
cat docs.ndjson | fessctl documents bulk -
```
