# Object storage (fessctl `storage`)

## What it is
The storage browser of the Admin UI (**System → Storage**): list, download, upload and delete objects in the S3-compatible or Google Cloud Storage bucket that Fess is configured to use (`storage_*` keys of `fessctl general`).

Every supported version has the API (14.19.2, 15.6.1, 15.7.0, 15.8.0, 15.9.0), with two differences:
- **Upload does not work on 15.6.1 to 15.8.0.** Those releases declare the upload endpoint as `PUT` only and do not parse a multipart `PUT`; the server answers `file is required.`, so fessctl refuses with a message instead of sending the request. Upload works on 14.19.2 (`POST`) and 15.9.0+ (`POST`).
- **An unreachable or unconfigured storage is reported only from 15.9.0.** Before that `list` answers an empty list (`No Storage items found.`) whatever is wrong. 15.9.0 returns an error such as `Storage Access Error: Access key ID cannot be blank.`, or, for a `storage_type` no plugin serves, `No storage client is registered as <type>StorageClient ... install fess-storage-s3 ... or fess-storage-gcs`. In 15.9.0 the S3 and GCS clients are the `fess-storage-s3` / `fess-storage-gcs` plugins (bundled in the 15.9.0 distribution; see `fessctl plugin installed`).

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `list` | List objects and directories under a path. | optional `[PATH]` (default: bucket root) |
| `download` | Write an object to `--file`, or to standard output without it. An existing `--file` is kept unless `--force`. | `<PATH>` |
| `upload` | Upload a local file as `<--dir>/<file name>` (default: bucket root). An existing object of that name is overwritten. | `<FILE>` |
| `delete` | Delete one object. Asks for confirmation unless `--yes` is given. | `<PATH>` |

Always reconfirm with `fessctl storage <sub> --help`.

## Paths
Commands take the plain object path (`docs/2026/report.pdf`, no leading slash); `list` prints the same form in its PATH column. The API itself addresses an object by the URL-safe Base64 of that path (`ZG9jcy8yMDI2L3JlcG9ydC5wZGY=`), which fessctl computes. Directories are prefixes: there is nothing to create or delete.

## Resource JSON shape
```json
{
  "response": {
    "items": [
      {"id": "ZG9jcy8=", "name": "docs", "directory": true, "size": 0, "hashCode": 348235201},
      {"id": "ZG9jcy9hLnR4dA==", "path": "docs", "name": "a.txt", "directory": false, "size": 6,
       "lastModified": "2026-10-16T12:28:45Z", "hashCode": 755113370}
    ],
    "status": 0
  }
}
```
Item keys are camelCase here (`lastModified`, `hashCode`); `path` is absent for items at the bucket root.

## Gotchas
- `download` cannot tell a failure from success by status: Fess streams the object after it has committed a `200`, so a missing object or unreachable storage comes back as `200` with `Content-Length: 0`. fessctl treats that as an error. A real empty object is sent chunked and is written as a 0-byte file.
- `delete` of an object that does not exist succeeds (S3 semantics).
- `list` returns at most `storage.max.items.in.page` items (default 1000); there is no paging.
- Uploaded content goes through multipart `file` plus `path`; names are kept as given.

## Examples
```bash
fessctl storage list
fessctl storage list docs/2026
fessctl storage download docs/2026/report.pdf --file ./report.pdf
fessctl storage download docs/notes.txt | head
fessctl storage upload ./report.pdf --dir docs/2026
fessctl storage delete docs/2026/report.pdf --yes
```
