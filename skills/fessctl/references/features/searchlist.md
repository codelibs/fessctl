# Indexed documents (fessctl `searchlist`)

## What it is
The admin document browser: search the documents that are in the Fess index, read one in full, and add, change or delete documents without a crawl. The Admin UI offers the same list as its Search List page. Every document is addressed by its `doc_id`; the search index `_id` shown in raw responses is a different value and is not accepted by `get`, `update` or `delete`.

Available in every Fess version fessctl supports (14.19.2, 15.6.1, 15.7.0, 15.8.0, 15.9.0).

## When to use
- Check what a crawl indexed: `search "title:foo"`, then `get <doc_id>`.
- Remove a document that should not be searchable: `delete <doc_id>`, or `delete-by-query` for a set of them.
- Add or correct a single document by hand: `create` / `update`. For many documents use `fessctl documents bulk`.

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `search` | Search the index. `--start` is the 0-based offset, `--size` the page size, `--sort`, `--lang` (repeatable). | none (a blank query matches all documents) |
| `get` | Show one document. | `<doc_id>` |
| `create` | Index a new document. | `--url`, `--title`, `--role` (repeatable); `--boost` defaults to 1.0 |
| `update` | Change fields of a document; every field not given is kept. | `<doc_id>` and at least one field option |
| `delete` | Delete one document. | `<doc_id>` |
| `delete-by-query` | Delete every document matching a query. Asks for confirmation unless `--yes` is given. | `<query>` |

`create` and `update` take the same field options: `--url`, `--title`, `--content`, `--role`, `--boost`, `--label`, plus `--field KEY=VALUE` (repeatable) for any other field, for example `--field mimetype=text/plain`. `--role` and `--label` replace the whole list. Always reconfirm with `fessctl searchlist <sub> --help`.

## Resource JSON shape
`get` returns the stored document under `response.doc`; `search` returns hits under `response.docs` with the paging fields beside them.
```json
{
  "response": {
    "status": 0,
    "doc": {
      "doc_id": "104d050992cb4992810ef340fba1c566",
      "url": "https://www.example.com/a.html",
      "title": "A page",
      "content": "...",
      "role": ["Rguest"],
      "label": ["docs"],
      "boost": 1.0,
      "_id": "125cc2...",
      "_version": 2
    }
  }
}
```
`search` reports `record_count` (total hits), `page_size`, `page_number`, `start_record_number` and `end_record_number`. `create` answers `{"id": "<doc_id>", "created": true}`; `delete-by-query` answers `{"count": N}`.

## Gotchas
- The server requires `url`, `title`, `role` and `boost` on every create and update request (`index.admin.required.fields`). `update` reads the stored document first and sends those four back unchanged, so you only give what changes. A stored document that lacks one of them (for example one without a title) is refused unless you set it in the same call.
- `--role` is stored as given: `Rguest` is the guest role, and a document is searchable by a user only when it shares a role with them. The document's index `_id` is derived from its URL and role list, so changing `--url` or `--role` moves the document to a new `_id`; the old one is removed and the `doc_id` stays the same.
- `search` does not take `--page`; this API pages with `--start` and `--size`. The server caps `--size` at 100 (`paging.search.page.max.size`; 0 or less also means 100) and refuses an offset beyond `indexer.max.result.window.size` (10000 by default) with "Could not process the specified query".
- `--sort` accepts only sortable index fields such as `last_modified.desc`, `created`, `timestamp`, `content_length` and `click_count`; `title.desc` is refused.
- Documents are searchable about a second after they are written (index refresh). Poll `search` or `get` after `create`, `update` or a bulk index instead of expecting the result at once. The same delay applies to deletes: for a moment after `delete`, a second `delete` of the same `doc_id` can still report success.
- `create` does not fill defaults: `last_modified`, `timestamp`, `content_length`, `click_count` and `favorite_count` are absent unless you pass them with `--field` (`documents bulk` does fill them).
- Field values given with `--field` are sent as strings; the server converts the numeric and date fields it validates (`boost`, `click_count`, `expires`, ...) and refuses ones that do not convert.
- `delete-by-query` takes a normal Fess query (`*:*` matches everything). `url` is matched whole, so use `url:"https://..."` with the exact URL; a wildcard on it matches nothing. A blank query is refused by the server. A confirmation is asked first; pass `--yes` in scripts.
- Fess 15.8.0 and later refuse a `--content` change on a document whose content was split into chunks by the chunk-embedding pipeline, and drop `content_chunk_vector` and `content_chunk_status` given through `--field`; 15.9.0 also drops the tag field.
- Fess 15.9.0 reports "not found" when `delete` matches no `doc_id`; 14.19.2 through 15.8.0 answer success without deleting anything.

## Examples
```bash
fessctl searchlist search "title:release" --size 20
fessctl searchlist search "*:*" --start 100 --size 100 --output json
fessctl searchlist get DOC_ID
fessctl searchlist create --url https://www.example.com/note --title "Note" --role Rguest --content "hello" --label notes
fessctl searchlist update DOC_ID --title "New title" --boost 2
fessctl searchlist delete DOC_ID
fessctl searchlist delete-by-query 'url:"https://www.example.com/old/page.html"' --yes
```
