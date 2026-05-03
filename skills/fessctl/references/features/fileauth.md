# File Authentication Credentials (fessctl `fileauth`)

## What it is

File Authentication credentials let the Fess crawler log in to network file sources that require authentication before content can be fetched. According to the Fess admin guide (`en/15.6/admin/fileauth-guide.rst`), Fess supports two authentication schemes for file crawling: FTP and SAMBA (Windows shared folders / SMB). Each entry stores a hostname, port, scheme, username, password, and optional parameters, and is bound to a specific File Crawl configuration.

In the admin UI, these records are managed under **Crawler > File Authentication**. Creating a record is essentially populating the same form fields that the UI exposes (Hostname, Port, Scheme, Username, Password, Parameters, File System Config). The `fessctl fileauth` subcommands wrap the equivalent admin API endpoints so the same credentials can be created, listed, retrieved, updated, and deleted from automation.

A File Authentication entry is meaningless on its own — it must reference an existing File Crawl configuration (`file_config_id`) for the crawler to consult it when visiting matching SMB/FTP URLs.

## When to use

- Crawling a Windows shared folder (`smb://server/share/...`) that requires a domain user instead of guest access.
- Crawling an internal FTP server where anonymous login is disabled.
- Rotating the password used by the crawler for an existing SMB or FTP source without recreating the File Crawl configuration.
- Auditing or exporting all file-credential entries (e.g. for review) via `list --output json`.

## Subcommand surface

| Subcommand | Purpose | Required arguments / options |
|------------|---------|------------------------------|
| `create` | Create a new FileAuth credential and bind it to a File Crawl config. | `--username`, `--file-config-id`; optional `--password`, `--hostname`, `--port`, `--protocol-scheme`, `--parameters`, `--created-by`, `--created-time`, `--output` |
| `update` | Update fields of an existing FileAuth (fetched first, then patched). | `config_id` arg; optional `--username`, `--password`, `--hostname`, `--port`, `--protocol-scheme`, `--parameters`, `--file-config-id`, `--updated-by`, `--updated-time`, `--output` |
| `delete` | Delete a FileAuth by ID. | `config_id` arg; optional `--output` |
| `get` | Retrieve a single FileAuth by ID with full detail rendering. | `config_id` arg; optional `--output` |
| `list` | List FileAuth records with paging. | Optional `--page/-p`, `--size/-s`, `--output/-o` |

Always reconfirm with `fessctl fileauth <sub> --help`.

## Resource JSON shape

```json
{
  "crud_mode": 1,
  "username": "crawler-user",
  "password": "secret",
  "hostname": "fileserver.example.com",
  "port": 445,
  "protocol_scheme": "smb",
  "parameters": "domain=CORP",
  "file_config_id": "FILE_CONFIG_ID_HERE",
  "created_by": "admin",
  "created_time": 1714694400000
}
```

Required on create: `username`, `file_config_id`. `crud_mode` is set internally (`1` for create, `2` for update). On update, `updated_by` and `updated_time` replace the created counterparts and the existing record is fetched first so unspecified fields are preserved.

## Relationships

- Depends on `fileconfig`: a FileAuth must reference an existing File Crawl configuration via `--file-config-id`. Create the `fileconfig` first, then attach credentials.
- The crawler matches the auth entry by hostname/port/scheme when fetching URLs that belong to the bound `fileconfig`.
- Parallel to `webauth` (HTTP/Web crawler credentials) and `dataconfig` credentials, but only consulted by the file crawler.
- Deleting a `fileconfig` does not implicitly clean up its FileAuth rows; remove them explicitly via `fessctl fileauth delete`.

## Gotchas

- Secret hygiene: `--password` is passed on the command line and may be captured in shell history. Prefer setting it via a wrapper script that reads from a secret store, or update the value out-of-band in the UI.
- `--protocol-scheme` accepts values such as `smb` or `ftp` (the help text lists `file, smb` as examples). Match the scheme used by the bound `fileconfig` URLs; mismatches mean the crawler will never consult the credential.
- For SMB / Windows shares, the NTLM domain is supplied through `--parameters` using the form `domain=FUGA` (per the admin guide). It is not a separate field.
- `--port` is optional; omit it to let the crawler use the protocol default (e.g. 445 for SMB, 21 for FTP). If you do specify it, ensure it matches the share's actual listener.
- `update` performs a read-modify-write: if the record was changed concurrently in the UI, your update may overwrite those edits. The `version_no` returned by `get` reflects the optimistic-locking version maintained by Fess.
- `created_time` / `updated_time` default to "now" in milliseconds; only override them when migrating data.
- The list response key is `settings` (plural), and IDs are opaque strings — always copy them from `list` or `get` output rather than constructing them.

## Examples

```bash
# Minimal create: SMB credential bound to an existing FileConfig
fessctl fileauth create \
  --username crawler-user \
  --password 's3cret!' \
  --hostname fileserver.example.com \
  --port 445 \
  --protocol-scheme smb \
  --parameters 'domain=CORP' \
  --file-config-id FILE_CONFIG_ID_HERE
```

```bash
# Update only the password for an existing FileAuth
fessctl fileauth update FILEAUTH_ID_HERE \
  --password 'rotated-password'
```

```bash
# List all FileAuths and filter for SMB entries on a specific host
fessctl fileauth list --size 200 --output json \
  | jq '.response.settings[] | select(.protocol_scheme == "smb" and .hostname == "fileserver.example.com")'
```

## See also

- fess-docs: en/15.6/admin/fileauth-guide.rst
- workflows.md: n/a
- Related features: `references/features/fileconfig.md`
