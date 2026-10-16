# Failure URLs (fessctl `failureurl`)

## What it is
A failure URL is a record of a URL the crawler could not fetch or process. The Admin UI shows them under **System → Failure URL**. Fess writes the rows itself during crawls; each carries the URL, the error name and log, how many times it failed (`error_count`), the last access time, and the id of the crawl config that hit it.

The surface is read and clean-up only: there is no `create` or `update`.

## When to use
- Find out why a crawl skipped documents: `list` with `--error-name` or `--url`.
- Find URLs that keep failing: `list --error-count-min 3`.
- Reset after fixing the cause (credentials, network, robots rules): `delete` one row, or `delete-all`.

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `list` | Page through failure URLs (`--page`, `--size`); narrow with `--url`, `--error-name`, `--error-count-min`, `--error-count-max`. | none |
| `get` | Show one row in full, including the error log. | `<failureurl_id>` |
| `delete` | Delete one row. | `<failureurl_id>` |
| `delete-all` | Delete every row. Asks for confirmation unless `--yes` is given. | none |

Always reconfirm with `fessctl failureurl <sub> --help`.

## Resource JSON shape
Rows are returned under `response.logs` (list) or `response.log` (single).
```json
{
  "id": "AY1n...e1Q",
  "url": "https://www.example.com/missing.html",
  "thread_name": "Crawler-20260503120000-1-2",
  "error_name": "org.codelibs.fess.crawler.exception.CrawlingAccessException",
  "error_log": "...stack trace...",
  "error_count": 3,
  "last_access_time": 1714723200000,
  "config_id": "W_x1..."
}
```

## Gotchas
- `delete-all` removes every row, not just those shown by a filter; there is no filtered delete.

## Examples
```bash
fessctl failureurl list --error-count-min 3
fessctl failureurl list --url "https://www.example.com/missing.html" --output json
fessctl failureurl get FAILURE_ID
fessctl failureurl delete FAILURE_ID
fessctl failureurl delete-all --yes
```
