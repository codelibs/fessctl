# Boost Document (fessctl `boostdoc`)

## What it is

Document Boost lets you reorder search results so that documents matching a URL condition consistently rank higher (or lower) regardless of the search keywords. Each rule pairs a Groovy condition over the document URL with a Groovy boost-value expression; when a crawled document matches the condition, its index-time boost factor is multiplied by the expression's result. This means rules are evaluated **at index time**, not query time — re-crawling (or re-indexing) is required for changes to take effect on existing documents.

In the admin UI, rules are managed under **Crawler > Document Boost** (left sidebar). The list page shows each configured rule, and clicking the URL expression opens its edit screen where the boost value and sort order can be tuned.

`fessctl boostdoc` exposes the same CRUD surface over the Fess admin REST API, so boost rules can be provisioned alongside crawl configs and scheduler jobs in a scripted workflow.

## When to use

- Promote canonical product or pricing pages above blog mentions of the same keywords.
- Pin a "what's new" or release-notes URL pattern to the top during a launch window.
- Demote (boost < 1.0) archived or legacy URL prefixes that should still be indexed but rarely surfaced.
- Apply a tenant-wide weighting (e.g., docs from `support.example.com` slightly outranking forum posts).

## Subcommand surface

| Subcommand | Purpose |
|---|---|
| `create` | Create a new rule. Requires `--url-expr`, `--boost-expr`, `--sort-order`; optional `--created-by`, `--created-time`. |
| `update` | Update an existing rule by ID. Re-fetches current state, then applies any of `--url-expr`, `--boost-expr`, `--sort-order`, `--updated-by`, `--updated-time`. |
| `delete` | Delete a rule by ID. |
| `get` | Retrieve a single rule by ID and render details. |
| `list` | List rules with `--page` / `--size` pagination. |

Always reconfirm with `fessctl boostdoc <sub> --help`.

## Resource JSON shape

```json
{
  "url_expr": "url.matches(\"https://www.example.com/products/.*\")",  // required, Groovy boolean expression
  "boost_expr": "2.0",                                                   // required, Groovy expression evaluating to a number
  "sort_order": 1,                                                       // required, non-negative integer; controls evaluation order in the admin list
  "id": "AY...",                                                         // server-assigned on create; required for update/delete
  "version_no": 1,                                                       // managed by server (optimistic locking)
  "crud_mode": 1,                                                        // 1 = create, 2 = edit; set automatically by fessctl
  "created_by": "admin",                                                 // defaults to "admin" on create
  "created_time": 1735689600000,                                         // UTC epoch millis; defaults to now on create
  "updated_by": "admin",                                                 // defaults to "admin" on update
  "updated_time": 1735689600000                                          // UTC epoch millis; defaults to now on update
}
```

## Relationships

- Applied **at index time** by the crawler/indexer pipeline — the resulting boost is baked into each document's stored boost factor, so existing documents are not retroactively re-scored when a rule changes.
- Depends on documents being indexed via `webconfig`, `fileconfig`, or `dataconfig`. A re-crawl (or full re-index) of affected URLs is required for new/changed rules to take effect.
- Complements `keymatch` (keyword-conditional pinning) and `elevateword` (suggest-time elevation), which both act at query time rather than index time.
- Sort order influences which rule is evaluated first when multiple `url_expr` patterns match the same URL.

## Gotchas

- **Groovy syntax**: both `url_expr` and `boost_expr` are Groovy. Inside `url.matches("...")` the regex must be a full match, and backslashes need escaping in JSON payloads (`\\.` → `\\\\.`).
- **Re-crawl required**: because boosting happens at index time, editing a rule does **not** rescore already-indexed documents. Re-crawl the matched URLs (or run a full re-index) for the change to be visible.
- **Boost magnitude**: very large values (e.g., `1000.0`) can crowd out keyword relevance entirely. Start small (`1.5`–`3.0`) and tune.
- **Demotion**: use a fractional value (e.g., `0.1`) in `boost_expr` to push results down rather than promoting them.
- **Sort order conflicts**: when multiple rules match, the lower `sort_order` is applied first. Decide on a numbering scheme (e.g., increments of 10) up front to make later inserts easy.
- **Interaction with keymatch / elevateword**: those features run at query time and stack on top of any index-time boost. A document that is boosted here can still be re-pinned by a matching `keymatch` rule.
- **Optimistic locking**: `version_no` is server-managed. `update` re-fetches the rule first; do not hand-edit it.

## Examples

Minimal create — promote all product pages with a 2x boost:

```bash
fessctl boostdoc create \
  --url-expr 'url.matches("https://www.example.com/products/.*")' \
  --boost-expr '2.0' \
  --sort-order 10
```

Update an existing rule to demote an archive prefix:

```bash
fessctl boostdoc update AYxxxxxxxxxxxxxxxxxx \
  --url-expr 'url.matches("https://www.example.com/archive/.*")' \
  --boost-expr '0.2' \
  --sort-order 90 \
  --updated-by admin
```

List and filter via JSON output (find rules with non-default boost):

```bash
fessctl boostdoc list --size 200 --output json \
  | jq -r '.response.settings[] | select(.boost_expr != "1.0") | "\(.sort_order)\t\(.id)\t\(.url_expr)\t\(.boost_expr)"'
```

## See also

- fess-docs: en/15.6/admin/boostdoc-guide.rst
- workflows.md: Recipe 5
- Related features: `references/features/keymatch.md`, `references/features/elevateword.md`
