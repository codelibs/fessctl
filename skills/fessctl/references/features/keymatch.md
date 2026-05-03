# Key Match (fessctl `keymatch`)

## What it is

Key Match is a Fess relevance-tuning feature that pins specific documents to the top of the search results whenever a user issues a particular search term. The administrator registers a search term, an internal query that selects the documents to promote, a maximum number of documents to elevate, and a boost value used to weight them above the natural ranking.

In the Fess admin UI it is reached via **Crawler > Key Match**, where you can list, create, edit, and delete entries. A common use case described in the documentation is advertising or promoting curated answers for a specific keyword.

`fessctl keymatch` exposes the same lifecycle through the admin API so that Key Match entries can be managed from scripts, CI pipelines, or migration tools alongside the rest of your Fess configuration.

## When to use

- Pinning a curated FAQ or canonical answer to the top whenever a known support query is searched (e.g. term `password reset`, query targeting the official password-reset page).
- Promoting branded or campaign content for navigational queries (e.g. term `pricing`, query selecting the pricing landing page).
- Boosting an internal announcement or policy document for a specific keyword without globally re-ranking the index.
- Overriding poor relevance for an ambiguous term while you investigate analyzer or synonym tuning.

## Subcommand surface

| Subcommand | Purpose | Key arguments |
| --- | --- | --- |
| `create` | Register a new Key Match entry | `--term`, `--query`, `--max-size`, `--boost`, `--version-no`, `--virtual-host`, `--created-by`, `--created-time`, `--output` |
| `update` | Modify an existing entry by ID | `config_id` (positional); optional `--term`, `--query`, `--max-size`, `--boost`, `--version-no`, `--virtual-host`, `--updated-by`, `--updated-time`, `--output` |
| `delete` | Remove a Key Match entry by ID | `config_id` (positional), `--output` |
| `get` | Show full detail of one entry | `config_id` (positional), `--output` |
| `list` | List Key Match entries with paging | `--page/-p`, `--size/-s`, `--output/-o` |

Always reconfirm with `fessctl keymatch <sub> --help`.

## Resource JSON shape

```json
{
  "crud_mode": 1,
  "term": "support",
  "query": "url:https://example.com/support/*",
  "max_size": 10,
  "boost": 100.0,
  "virtual_host": "search.example.com",
  "version_no": 1,
  "created_by": "admin",
  "created_time": 1714694400000,
  "updated_by": "admin",
  "updated_time": 1714694400000
}
```

Required when creating: `term`, `query`, `max_size`, `boost`, `version_no`. `virtual_host` is optional and only sent when provided. `created_by` / `created_time` (and `updated_by` / `updated_time` on update) default to `admin` and the current UTC time in milliseconds.

## Relationships

- Operates on documents already present in the search index; it does not crawl or alter source content.
- Takes effect at search time, evaluated by the same Fess instance that serves the query.
- When `virtual_host` is set, the entry only applies to searches arriving through that virtual host (see the Fess virtual host configuration guide).
- The boost value combines with the regular relevance score, so very large boosts effectively pin the matched documents while smaller ones nudge ordering.
- Sits alongside other ranking tools: `boostdoc` (document-level boosting), `elevateword` (term-level promotion), and `relatedquery` (query suggestions).

## Gotchas

- Key Match changes do not take effect immediately for live search; the Key Match cache must be reloaded (typically via the admin UI or by restarting Fess) for new or updated entries to be applied.
- The `query` field is a Fess query string (e.g. `url:...`, `title:...`); a malformed query yields no promoted documents and no obvious error in search results.
- The `term` is matched against the user's search term; matching follows the same analyzer behavior as ordinary searches, so casing and tokenization can affect when an entry triggers.
- `virtual_host` scopes an entry to one host. An entry without `virtual_host` applies broadly; mixing scoped and unscoped entries can produce surprising overlaps.
- `max_size` caps the number of pinned documents; if the query matches more documents than `max_size`, only that many are elevated.
- Very large `boost` values dominate the score and may hide otherwise relevant results; tune carefully.
- `version_no` is required on `create` and used for optimistic locking on `update`; supply the value returned by `get` to avoid conflicts.

## Examples

Minimal create:

```bash
fessctl keymatch create \
  --term "support" \
  --query "url:https://example.com/support/*" \
  --max-size 10 \
  --boost 100 \
  --version-no 1
```

Update an existing entry (raise the boost and change the query):

```bash
fessctl keymatch update KM_ID_HERE \
  --query "url:https://example.com/support/index.html" \
  --boost 200
```

List entries and filter to those whose term contains `support` using `jq`:

```bash
fessctl keymatch list --output json \
  | jq '.response.settings[] | select(.term | test("support"))'
```

## See also

- fess-docs: en/15.6/admin/keymatch-guide.rst
- workflows.md: Recipe 5 (search relevance tuning)
- Related features: `references/features/boostdoc.md`, `references/features/elevateword.md`, `references/features/relatedquery.md`
