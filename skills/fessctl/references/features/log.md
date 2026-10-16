# Log files (fessctl `log`)

## What it is
The log files in the log directory of the Fess server (`audit.log`, `fess.log`, `fess-crawler.log`, ... plus rotated `*.log.gz`), as listed on the Admin UI log files page. The admin API lists them and streams one file.

Available in every version fessctl supports (14.19.2, 15.6.1, 15.7.0, 15.8.0, 15.9.0). Only names ending in `.log` or `.log.gz` are served.

## When to use
- Fetch the server logs for a bug report without shell access to the server.
- Check the crawler, thumbnail or audit log after a failed job.

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `list` | List the log files with their id and last-modified time. | none |
| `download` | Write one log file to a local file. Refuses to overwrite unless `--force` is given. | `<log_id> --dest PATH` |

Always reconfirm with `fessctl log <sub> --help`.

## Resource JSON shape
```json
{
  "response": {
    "status": 0,
    "total": 2,
    "files": [
      {"name": "fess.log", "id": "ZmVzcy5sb2c=", "lastModified": "2026-10-16T12:23:38"},
      {"name": "audit.log", "id": "YXVkaXQubG9n", "lastModified": "2026-10-16T12:23:49"}
    ]
  }
}
```
The `id` is the URL-safe Base64 of the file name. `lastModified` is in the server's local time without a zone (and camelCase, unlike the rest of the API). `download` with `--output json` returns `{"response": {"status": 0, "path": "...", "size": 981}}`.

## Gotchas
- An empty log file downloads as an empty file; a log that Fess has not written to yet is common. Fess also answers an id that names no log file with an empty download, so `download` checks the id against `list` first and fails with `not found` instead.
- Fess decodes the id as standard Base64 while `list` hands out URL-safe Base64. The two differ only for `-` and `_` in an id, which appear only for file names containing characters such as `>`, `?`, `~` or non-ASCII; such a log file cannot be downloaded through the API (`Could not find ...`).
- The file is written to a temporary `.part` file next to the destination and renamed on success, so a failed transfer leaves no partial file.

## Examples
```bash
fessctl log list
fessctl log download "$(fessctl log list -o json | jq -r '.response.files[] | select(.name == "fess.log") | .id')" --dest ./fess.log
fessctl log download YXVkaXQubG9n --dest ./audit.log --force
```
