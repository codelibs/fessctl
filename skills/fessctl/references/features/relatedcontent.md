# Related Content (fessctl `relatedcontent`)

## What it is

Related Content is a Fess feature that displays a custom HTML or text snippet at the top of search results whenever the user's search query matches a configured search term. The administrator registers a term and the corresponding content body, and Fess injects that snippet alongside the natural search results when the term is matched.

In the Fess admin UI it is reached via **Crawler > Related Content**, where you can list, create, edit, and delete entries. The configuration is intentionally small (term + content, optionally scoped by virtual host), making it useful for promotional banners, in-result advisories, or short editorial answers tied to a known query.

`fessctl relatedcontent` exposes the same lifecycle through the admin API so that Related Content entries can be managed from scripts, CI pipelines, or migration tools alongside the rest of your Fess configuration.

## When to use

- Showing a curated answer or banner ("Office is closed on May 5") whenever users search a known term.
- Promoting a campaign or product page above the organic results for a navigational query (e.g. term `pricing`).
- Surfacing a help-desk notice or maintenance message tied to a specific keyword without re-ranking the index.
- Providing localized or virtual-host-specific in-result content by scoping entries with `virtual_host`.

## Subcommand surface

| Subcommand | Purpose | Key arguments |
| --- | --- | --- |
| `create` | Register a new Related Content entry | `--term`, `--content`, `--sort-order`, `--virtual-host`, `--created-by`, `--created-time`, `--output/-o` |
| `update` | Modify an existing entry by ID | `config_id` (positional); optional `--term`, `--content`, `--sort-order`, `--virtual-host`, `--updated-by`, `--updated-time`, `--output/-o` |
| `delete` | Remove a Related Content entry by ID | `config_id` (positional), `--output/-o` |
| `get` | Show full detail of one entry | `config_id` (positional), `--output/-o` |
| `list` | List Related Content entries with paging | `--page/-p`, `--size/-s`, `--output/-o` |

Always reconfirm with `fessctl relatedcontent <sub> --help`.

## Resource JSON shape

```json
{
  "crud_mode": 1,
  "term": "holiday",
  "content": "<div class=\"notice\">Our office is closed May 3-5.</div>",
  "sort_order": 0,
  "virtual_host": "search.example.com",
  "created_by": "admin",
  "created_time": 1714694400000,
  "updated_by": "admin",
  "updated_time": 1714694400000
}
```

Required when creating: `term` and `content`. Optional: `sort_order` (defaults to `0`) and `virtual_host` (only sent when provided). `created_by` / `created_time` (and `updated_by` / `updated_time` on update) default to `admin` and the current UTC time in milliseconds. `id` and `version_no` are returned by the server and used by `update` for optimistic locking.

## Relationships

- Surfaced in the UI search results page when the user's query term matches the configured `term`.
- Operates purely at search-render time; it does not affect the index, crawler, or document scoring.
- When `virtual_host` is set, the entry only applies to searches arriving through that virtual host (see the Fess virtual host configuration guide).
- `sort_order` controls relative ordering when multiple Related Content entries match the same query.
- Complementary to ranking-side tools such as `keymatch` (document pinning), `boostdoc` (document-level boosting), and `relatedquery` (query suggestions); Related Content is the only one that injects raw markup.

## Gotchas

- Related Content changes do not take effect immediately for live search; the Related Content cache must be reloaded (typically via the admin UI or by restarting Fess) for new or updated entries to be applied.
- The `content` field is rendered into the search results page; HTML is generally not escaped, so untrusted markup is a XSS risk - only register content you trust and escape user-supplied values yourself.
- The `term` is matched against the user's search query; matching is sensitive to casing and tokenization, so an entry registered as `Pricing` may not fire for the query `pricing` depending on analyzer settings.
- `virtual_host` scopes an entry to one host. An entry without `virtual_host` applies broadly; mixing scoped and unscoped entries can produce overlapping snippets.
- `sort_order` is a plain integer and is not auto-deduplicated across entries; assign distinct values when ordering matters.
- `update` performs a read-modify-write: it first fetches the existing entry, so the target ID must already exist or the command exits non-zero.

## Examples

Minimal create:

```bash
fessctl relatedcontent create \
  --term "holiday" \
  --content "<div class=\"notice\">Our office is closed May 3-5.</div>"
```

Update an existing entry (change content and bump sort order):

```bash
fessctl relatedcontent update RC_ID_HERE \
  --content "<div class=\"notice\">Office reopens May 6.</div>" \
  --sort-order 10
```

List entries and filter to those whose term contains `holiday` using `jq`:

```bash
fessctl relatedcontent list --output json \
  | jq '.response.settings[] | select(.term | test("holiday"))'
```

## See also

- fess-docs: en/15.6/admin/relatedcontent-guide.rst
- workflows.md: n/a
- Related features: `references/features/relatedquery.md`, `references/features/keymatch.md`
