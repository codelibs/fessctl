# Path Mapping (fessctl `pathmap`)

## What it is

A Path Mapping is a regex-based URL rewrite rule applied by Fess at crawl time and/or display time. The administrator defines a Java regular expression and a replacement string; matching URLs are rewritten before being indexed, before being shown in search results, or while extracting links from HTML during web crawling. In the admin UI it lives at **Crawler -> Path Mapping** (left sidebar: "Crawler > Path Mapping").

Typical use is bridging the gap between how the crawler reaches content and how end users should see or click it. For example, the file crawler may reach documents at `file:/srv/documents/...` while users should see `http://fileserver.example.com/documents/...`. Path Mapping handles that translation declaratively, without modifying crawl configs or post-processing the index.

The `fessctl pathmap` subcommand is a thin CRUD wrapper over the Fess admin API for these entries. It is convenient for scripting environment migrations, normalizing URLs across Fess instances, and rolling out the same rewrite ruleset to multiple deployments.

## When to use

- Rewriting an internal file-server path (`file:/srv/...`) to a public web URL so search results are clickable.
- Keeping the original path in the index but presenting a friendlier URL only at display time (`Displaying` mode).
- Migrating a site between hostnames: rewrite extracted links from `old-server.example.com` to `new-server.example.com` so the crawler enqueues the new host (`Extracted URL Conversion`).
- Stripping or normalizing tracking parameters and trailing slashes so duplicate-looking URLs collapse to a single canonical form.

## Subcommand surface

| Subcommand | Purpose | Notes |
|------------|---------|-------|
| `create`   | Create a new Path Mapping. | Requires `--regex` and `--process-type`. `--replacement` is optional but almost always wanted. |
| `update`   | Update an existing Path Mapping by ID. | Takes positional `CONFIG_ID`. Read-modify-write: only fields explicitly passed are overwritten. |
| `delete`   | Delete a Path Mapping by ID. | Irreversible. Already-indexed documents keep whatever URL was stored at index time. |
| `get`      | Retrieve one Path Mapping by ID. | Renders a Markdown detail view by default; switch with `--output json` or `--output yaml`. |
| `list`     | List Path Mappings. | Supports `--page` / `--size` pagination. Default page size is 100. |

Always reconfirm with `fessctl pathmap <sub> --help`.

## Resource JSON shape

```json
{
  "regex": "file:/srv/documents/",                       // required, Java regex
  "replacement": "http://fileserver.example.com/documents/", // optional but typically required
  "process_type": "C",                                    // required: C=Crawling, D=Displaying, B=Both, E=Extracted URL
  "user_agent": "",                                       // optional, regex matched against UA; empty = all
  "sort_order": 0,                                        // optional, ascending application order
  "created_by": "admin",                                  // optional, default "admin"
  "created_time": 1714723200000                           // optional, defaults to now (epoch ms, UTC)
}
```

The `process_type` field is sent verbatim as supplied on the command line. Acceptable values follow the admin UI semantics: Crawling, Displaying, Crawling/Displaying (Both), and Extracted URL Conversion. Confirm the exact code your Fess version expects via `fessctl pathmap get <id> --output json` against an entry created in the UI.

## Relationships

- Applied during **crawling** (rewrites URL before indexing) and/or **display** (rewrites URL when rendering search results) depending on `process_type`.
- Affects **all crawl configs** (Web, File, Data) globally; there is no per-config scoping. Use `user_agent` for narrower targeting on the web crawler.
- `Extracted URL Conversion` only affects the **web crawler** when extracting links from HTML; it does not apply to file or datastore crawlers.
- Interacts with `fessctl webconfig` and `fessctl fileconfig`: the rewritten URL is what ends up in the index, so permissions, label filters, and virtual hosts should be evaluated against the post-rewrite URL.
- Multiple mappings are applied in `sort_order` ascending; chain rules carefully so earlier rewrites do not invalidate later regex matches.

## Gotchas

- Changes to `Crawling` (or `Both`) mappings only affect documents indexed **after** the change. Existing documents keep their stored URL until re-crawled; trigger a recrawl to apply the new mapping retroactively.
- Regex syntax is **Java** regex, not POSIX or PCRE. Special characters (`.`, `?`, `+`, `(`, `)`) must be escaped with backslashes; use back references like `$1`, `$2` in the replacement.
- When passing patterns via shell, quote them in single quotes to prevent the shell from interpreting `$1`, backslashes, or parentheses. For example: `--regex 'http://old\.example\.com/(.*)' --replacement 'http://new.example.com/$1'`.
- `process_type` is sent as a raw string. Provide the value your Fess version stores (typically a single letter such as `C`, `D`, `B`, `E`); verify by inspecting an existing UI-created entry with `--output json` first.
- `user_agent` is itself a regex; an empty value matches all requests. Be precise to avoid unintentionally rewriting all crawler traffic.
- `Extracted URL Conversion` does not change URLs already saved in the index; it only affects what gets enqueued for crawling.
- `update` performs a read-modify-write: if the config ID does not exist, the command exits non-zero with a "not found" message.
- Deleting a mapping does not undo URL changes already written to the index; you need a recrawl to restore original URLs.

## Examples

```bash
# Minimal create: rewrite file-server paths to a public web URL at index time
fessctl pathmap create \
  --regex 'file:/srv/documents/' \
  --replacement 'http://fileserver.example.com/documents/' \
  --process-type C
```

```bash
# Update an existing mapping: change replacement and bump sort order
fessctl pathmap update PM1a2b3c4d5 \
  --replacement 'https://files.example.com/docs/' \
  --sort-order 10
```

```bash
# List all path mappings as JSON and filter only the display-time rules
fessctl pathmap list --size 200 --output json \
  | jq '.response.settings[] | select(.process_type == "D") | {id, regex, replacement, sort_order}'
```

## See also

- fess-docs: en/15.6/admin/pathmap-guide.rst
- workflows.md: n/a
- Related features: `references/features/webconfig.md`
