# Related Query (fessctl `relatedquery`)

## What it is

Related queries let administrators register alternative search terms that get surfaced when an end user submits a configured term. When the search frontend receives a query that matches the registered `term`, Fess promotes the configured `queries` as related-query suggestions, helping users discover phrasings that perform better against the indexed corpus.

In the admin UI, related queries are managed from **Crawler > Related Query**. Each entry binds a single search term to one or more alternative query expressions and may be scoped to a specific virtual host so that different sites served by the same Fess instance can ship distinct related-query sets.

The `fessctl relatedquery` command group wraps the `/api/admin/relatedquery` endpoints so configurations can be created, listed, retrieved, updated, and deleted from scripts without using the web UI.

## When to use

- Surface synonyms or alternative phrasings (for example, suggest `search engine` when users type `fess`).
- Redirect common misspellings to canonical queries that have better recall.
- Provide brand or product-name aliases for marketing campaigns.
- Tune query coverage per virtual host when multiple sites share one Fess deployment.

## Subcommand surface

| Subcommand | Purpose | Required input |
|------------|---------|----------------|
| `create` | Register a new related query entry. | `--term`, `--queries`, `--version-no` |
| `update` | Modify an existing entry by ID, preserving untouched fields. | `config_id` argument; optional `--term`, `--queries`, `--virtual-host` |
| `delete` | Remove an entry by ID. | `config_id` argument |
| `get` | Fetch a single entry by ID. | `config_id` argument |
| `list` | Page through registered entries. | `--page`, `--size` (both optional) |

Always reconfirm with `fessctl relatedquery <sub> --help`.

## Resource JSON shape

```json
{
  "id": "REL-XXXXXXXXXXXXXXXX",
  "term": "fess",
  "queries": "search engine\nfull text search",
  "virtual_host": "site-a",
  "version_no": 1,
  "crud_mode": 1,
  "created_by": "admin",
  "created_time": 1735689600000,
  "updated_by": "admin",
  "updated_time": 1735689600000
}
```

`term` and `queries` are required by the API. `virtual_host` is optional and only sent when supplied. `queries` is transmitted as a string; multiple alternatives are typically separated by newlines (escape as `\n` on the command line).

## Relationships

- Surfaced through the Fess search UI as related-query suggestions when the user-supplied query matches a registered `term`.
- Changes may require a related-query cache reload before they appear in search responses; restart or trigger a reload after bulk edits.
- `virtual_host` scopes the entry to a specific virtual host configuration; entries without `virtual_host` apply globally.
- Distinct from synonym dictionaries (which rewrite tokens at index/query time): related queries do not modify scoring, they only present alternative searches to the user.

## Gotchas

- After create/update/delete the related-query cache may need to be reloaded before the change is visible in search responses; plan a reload step in automation pipelines.
- The `term` is matched against the user query; casing and whitespace handling depend on Fess's matcher, so register the canonical form you observe in query logs.
- `queries` is a single string field on the wire even though it represents a list. Use newline separators (`$'\n'` in bash, `\n` inside JSON) so the UI renders each alternative on its own line.
- Related queries are not synonyms; they neither expand the underlying query nor rewrite tokens. If you need recall changes, use synonym/stopword dictionaries instead.
- `--version-no` is mandatory on `create`; supply `1` for new entries and trust optimistic locking to bump it on subsequent updates.
- `update` performs a read-modify-write cycle: the command first calls `get` and aborts if the ID is not found.

## Examples

```bash
# Minimal create: associate the term "fess" with two alternative queries.
fessctl relatedquery create \
  --term "fess" \
  --queries $'search engine\nfull text search' \
  --version-no 1
```

```bash
# Update only the queries field for an existing entry.
fessctl relatedquery update REL-1234567890ABCDEF \
  --queries $'search engine\nopen source search\nenterprise search'
```

```bash
# List entries as JSON and filter for a specific virtual host with jq.
fessctl relatedquery list --size 200 --output json \
  | jq '.response.settings[] | select(.virtual_host == "site-a")'
```

## See also

- fess-docs: en/15.6/admin/relatedquery-guide.rst
- workflows.md: Recipe 5
- Related features: `references/features/relatedcontent.md`, `references/features/elevateword.md`
