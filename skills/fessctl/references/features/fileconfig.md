# File Crawl Configs (fessctl `fileconfig`)

## What it is
File Crawl Configs define how the Fess crawler walks a file system or remote object store and indexes the documents it finds. Each config carries a starting path (for example `file:/`, `smb://`, `s3://`, `gcs://`), include/exclude regular expressions, depth and concurrency limits, permissions, and arbitrary client parameters that get passed to the underlying crawler client (S3, GCS, SMB, etc.).

In the Fess admin UI these records are managed under **Crawler > File System**. Authentication for protected shares (SMB, SFTP, S3, GCS credentials, etc.) is stored separately under **Crawler > File Authentication** and joined to a config by hostname/scheme. Indexing is normally executed by the default crawler scheduler job, which only picks up configs whose `available` flag is true.

The `fessctl fileconfig` subcommands are a one-to-one wrapper over the corresponding `/api/admin/fileconfig` admin endpoints used by that screen.

## When to use
- Onboarding a new shared folder, S3 bucket, or GCS bucket that should be searchable from Fess.
- Tightening or widening crawl scope by editing include/exclude regex without touching the UI.
- Bulk-disabling a noisy file source by flipping `--available false` ahead of the next scheduled job.
- Exporting an existing file config (`get -o yaml`) so it can be version-controlled or replayed in another environment.

## Subcommand surface

| Subcommand | Purpose | Notes |
| --- | --- | --- |
| `create` | Register a new file crawl config. | `--name` and at least one `--path` are required; other options take crawler-friendly defaults (1 thread, 10000 ms interval, depth 1, max 1,000,000 docs, permission `{role}guest`). |
| `update` | Patch an existing config by ID. | Fetches the current record first, applies only the flags you pass, and re-submits with `crud_mode=2`. ID is a positional argument. |
| `delete` | Remove a config by ID. | Hard delete; pair with `get -o yaml` first if you need a backup. |
| `get` | Show a single config in markdown, JSON, or YAML. | Renders all stored fields including `version_no`, `created_time`, and `updated_time` (epoch ms is converted to UTC ISO 8601 in text mode). |
| `list` | List configs with `--page` / `--size` paging. | Default size is 100; text output shows ID and Name only — switch to `-o json` for the full payload. |

Always reconfirm with `fessctl fileconfig <sub> --help`.

## Resource JSON shape

```json
{
  "crud_mode": 1,
  "name": "Shared Folder",
  "paths": "smb://SERVER/SharedFolder/",
  "num_of_thread": 1,                 // optional, default 1
  "interval_time": 10000,             // optional, default 10000 (ms)
  "boost": 1.0,                       // optional, default 1.0
  "available": true,                  // optional, default true
  "sort_order": 1,                    // optional, default 1
  "description": "",                  // optional, default ""
  "label_type_ids": [],               // optional, default []
  "included_paths": "",               // optional, newline-joined regex list
  "excluded_paths": "",               // optional, newline-joined regex list
  "included_doc_paths": "",           // optional, newline-joined regex list
  "excluded_doc_paths": "",           // optional, newline-joined regex list
  "config_parameter": "",             // optional, newline-joined key=value pairs
  "depth": 1,                         // optional, default 1
  "max_access_count": 1000000,        // optional, default 1000000
  "permissions": "{role}guest",       // optional, default "{role}guest"
  "virtual_hosts": "",                // optional, newline-joined hostnames
  "created_by": "admin",              // optional, default "admin"
  "created_time": 1714694400000       // optional, defaults to current UTC epoch ms
}
```

Repeated CLI flags (for example multiple `--path` or `--config-parameter` arguments) are joined with newlines before being sent to the API, mirroring how the admin form serializes textarea fields.

## Relationships
- **`labeltype`**: `--label-type-id` values must exist as Label Type IDs; create them first via `fessctl labeltype create` so search results can be filtered by label.
- **`fileauth`**: SMB/FTP/SFTP/S3/GCS sources that need credentials require a matching File Authentication record (`fessctl fileauth ...`) keyed by the same hostname/scheme.
- **`scheduler`**: Only configs with `available=true` are picked up by the default crawler job. Use `fessctl scheduler` to inspect or trigger that job.
- **`role` / `group` / `user`**: Strings in `--permission` (`{role}...`, `{group}...`, `{user}...`) must reference identities managed by the corresponding `fessctl` resource commands.
- **`webconfig` / `dataconfig`**: Sibling crawl-source resources; they share scheduler and label-type wiring but use different paths/clients.

## Gotchas
- Path scheme matters: use `file:/absolute/path` for local filesystems, `smb://HOST/Share/` for Windows shares, `s3://bucket/`, or `gcs://bucket/`. Trailing slashes are recommended for directories so the include/exclude regex anchors behave predictably.
- Include/exclude expressions are Java-flavored regular expressions matched against the full path; remember to escape dots and to use `.*` (not glob `*`) for wildcards.
- Cloud-storage credentials live in `--config-parameter` as `key=value` lines (e.g. `client.accessKey=...`, `client.secretKey=...`, `client.region=...` for S3, or `client.projectId=...`, `client.credentialsFile=...` for GCS). Treat these like secrets and avoid committing them to YAML exports.
- `update` requires the existing config to be readable — if `get_fileconfig` fails the command exits before sending an update, so confirm the ID with `fessctl fileconfig list` first.
- `delete` is irreversible from the CLI; there is no soft-delete or trash recovery in Fess.
- `created_time` / `updated_time` are epoch milliseconds (UTC). The CLI defaults them to "now"; only override when reproducing historical state.
- Available since Fess 15.6 admin API; older versions may reject newer fields such as `gcs://` schemes or extra client parameters.

## Examples

```bash
# Minimal create: crawl a local share with defaults
fessctl fileconfig create \
  --name "Share Directory" \
  --path "file:/home/share"
```

```bash
# Typical update: tighten scope and lower concurrency on an existing config
fessctl fileconfig update FCONFIG_ID \
  --excluded-path ".*/\.git/.*" \
  --excluded-path ".*\.tmp$" \
  --num-of-thread 2 \
  --interval-time 5000 \
  --available true
```

```bash
# List and filter via JSON output
fessctl fileconfig list --size 200 --output json \
  | jq '.response.settings[] | select(.paths | startswith("smb://")) | {id, name, paths}'
```

## See also
- fess-docs: en/15.6/admin/fileconfig-guide.rst
- workflows.md: n/a
- Related features: `references/features/fileauth.md`, `references/features/labeltype.md`, `references/features/scheduler.md`
