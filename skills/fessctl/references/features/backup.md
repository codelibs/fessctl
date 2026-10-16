# Backup files (fessctl `backup`)

## What it is
The files the Admin UI backup page offers for download: index dumps in Elasticsearch/OpenSearch bulk format (`fess_config.bulk`, `fess_basic_config.bulk`, `fess_user.bulk`), the `system.properties` file, the index mappings (`fess.json`, `doc.json`) and the search, click, favorite, user-info and chat logs as NDJSON. The admin API lists the ids and streams one file. It is download only; restoring a backup is not available through the admin API.

Available in every version fessctl supports (14.19.2, 15.6.1, 15.7.0, 15.8.0, 15.9.0), with differences noted below.

## When to use
- Take a copy of the Fess configuration (crawl configs, labels, users, system properties) before an upgrade or a risky change.
- Export the search log for analysis outside Fess.

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `list` | List the downloadable files. | none |
| `download` | Write one file to a local file. Refuses to overwrite unless `--force` is given. | `<backup_id> --dest PATH` |

Always reconfirm with `fessctl backup <sub> --help`.

## Resource JSON shape
```json
{
  "response": {
    "status": 0,
    "total": 2,
    "files": [
      {"name": "fess_config.bulk", "id": "fess_config.bulk"},
      {"name": "search_log.ndjson", "id": "search_log.ndjson"}
    ]
  }
}
```
The id equals the name. `download` with `--output json` returns `{"response": {"status": 0, "path": "...", "size": 6463}}`. An unknown id returns `status` 1 with `Could not find any backup index.` (`Could not find index for backup.` in 14.x) and creates no file.

## Gotchas
- The dumps contain everything stored in the index, including access tokens and crawl credentials. Treat the files as secrets.
- An empty file is a valid result: a search log with no entries downloads as 0 bytes.
- Before 15.9.0 `fess.json` and `doc.json` are listed but download as empty files (the mapping export was added in 15.9.0), and `chat_log.ndjson` is listed only from 15.9.0.
- Fess answers a path whose last segment has an extension (`.../backup/file/fess_config.bulk`) with a bare `404 Not Found.` in 15.9 and a redirect in older versions, instead of running the action. fessctl requests the id with a trailing slash, which Fess serves.
- The file is written to a temporary `.part` file next to the destination and renamed on success, so a failed transfer leaves no partial file. Large dumps are streamed; the read timeout applies per chunk (60 s).

## Examples
```bash
fessctl backup list
fessctl backup download fess_config.bulk --dest ./fess_config.bulk
fessctl backup download system.properties --dest ./system.properties --force
fessctl backup download search_log.ndjson --dest ./search_log.ndjson -o json
```
