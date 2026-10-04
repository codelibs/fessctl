# User Tags (fessctl `tagtype`)

## What it is
A tag type is a named, user-owned list of document URLs. End users create and manage their own tags from the search UI; the admin API lets an administrator list, inspect, create, change, and delete any user's tags. Each tag has a `name`, an `owner` (user name), the tagged documents as `paths` (one URL per line), optional `permissions` (one per line; only the owner can see the tag when empty), an optional `virtual_host`, and a `sort_order`.

Requires a Fess version that provides `/api/admin/tagtype` (introduced by fess#3551; not in Fess 15.9 or earlier).

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `create` | Register a new tag. | `--name`, `--owner` |
| `update` | Modify an existing tag by ID; unspecified fields (including paths) are preserved. | `<config_id>` |
| `delete` | Permanently delete a tag by ID. | `<config_id>` |
| `get` | Show one tag's full detail, including its paths. | `<config_id>` |
| `list` | Page through all tags (default page size 100); paths are not included. | none |

Always reconfirm with `fessctl tagtype <sub> --help`.

## Resource JSON shape
```json
{
  "id": "...",
  "name": "work",
  "owner": "taro",
  "paths": "https://www.example.com/a.html\nhttps://www.example.com/b.html",
  "permissions": "{user}taro\n{group}developer",
  "virtual_host": "",
  "sort_order": 0,
  "seq_no": 7,
  "primary_term": 1
}
```
The CLI accepts repeatable `--path` and `--permission` flags and joins them with newlines before posting.

## Gotchas
- `update` replaces the whole tag on the server. The CLI reads the tag first and sends back every field you did not change, together with its `seq_no`/`primary_term`; if the tag changed in between (e.g. its owner edited it), the update fails with a "changed concurrently" error - re-run it.
- Passing `--path` on `update` replaces the whole path list; it does not append.
- Changing `--name` or `--owner` gives the tag a new ID; `update` reports the new ID.
- `list` omits `paths`; use `get` to see them.

## Examples
```bash
fessctl tagtype create --name work --owner taro \
  --path "https://www.example.com/a.html" --path "https://www.example.com/b.html"

fessctl tagtype update TAG_ID --sort-order 1

fessctl tagtype list --output json | jq '.response.settings[] | select(.owner == "taro")'
```
