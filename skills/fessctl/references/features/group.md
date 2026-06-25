# Groups (fessctl `group`)

## What it is

The Group feature manages the organizational buckets that users belong to in Fess. It is reached through the admin UI menu path **User -> Group**, where you can list, create, edit, and delete group definitions. A group has only two meaningful fields: a `name` and an optional free-form `attributes` map. Groups are commonly used when integrating with an external directory (LDAP/Active Directory) so that the directory's group membership can be mirrored inside Fess.

In Fess's authorization model a *user* is the principal that authenticates, a *role* is a permission grant attached to crawl configurations and documents (issued via permission strings such as `{role}admin`), and a *group* is a separate organizational primitive that can also be referenced as a permission string (`{group}engineering`). Groups do not by themselves grant any specific capability inside the admin UI; they exist so that crawl configs, documents, and users can express access in terms of "anyone in group X."

The `fessctl group` command exposes the same admin REST API that the UI uses, which makes it suitable for scripted provisioning, LDAP mirror jobs, and bulk audits.

## When to use

- Mirror an LDAP/AD organizational unit into Fess so that crawl-config permissions can reference it.
- Create department-style buckets (for example `engineering`, `sales`, `legal`) that several users will share.
- Audit which groups exist before assigning them to a user via `fessctl user create --group`.
- Clean up stale groups left over after a re-org, after first detaching them from any users that still reference them.

## Subcommand surface

| Subcommand | Purpose | Key arguments / options |
|------------|---------|-------------------------|
| `create` | Create a new group. | `name` (arg, max 100 chars), `--attribute/-a key=value` (repeatable), `--output/-o` |
| `update` | Update an existing group (fetched then merged). | `group_id` (arg), `--attribute/-a key=value` (repeatable), `--updated-by`, `--updated-time`, `--output/-o` |
| `delete` | Delete a group by ID. | `group_id` (arg), `--output/-o` |
| `getbyname` | Resolve a group by name (URL-safe base64 encodes the name and calls `get`). | `name` (arg), `--output/-o` |
| `get` | Retrieve a group's full record by ID. | `group_id` (arg), `--output/-o` |
| `list` | List groups with pagination. | `--page/-p` (default 1), `--size/-s` (default 100), `--output/-o` |

Always reconfirm with `fessctl group <sub> --help`.

## Resource JSON shape

```json
{
  "crud_mode": 2,
  "id": "ZW5naW5lZXJpbmc",
  "name": "engineering",
  "attributes": {
    "description": "Product engineering org",
    "ou": "Engineering",
    "owner": "alice"
  },
  "updated_by": "admin",
  "updated_time": 1714694400000,
  "version_no": 1
}
```

Required on create: `name` only. `attributes` is an optional free-form `key=value` map (commonly used to carry LDAP fields such as `description`, `ou`, or `owner`); it has no schema enforcement on the server. `id` is server-assigned and is the URL-safe base64 of the name. `updated_by`, `updated_time`, and `version_no` are managed by the API and only need to be supplied on `update`.

## Relationships

- A **user** references group names (strings) via its `groups` array; see `references/features/user.md`.
- A **role** is an independent permission grant; groups and roles are parallel, not hierarchical. See `references/features/role.md`.
- A group may be referenced by **permission strings** of the form `{group}<name>` inside the `permissions` field of webconfig, fileconfig, and dataconfig records, and inside the per-document `permissions` indexed by the crawler. The match is by name string, not by ID.
- The full effective permission set of a logged-in user is the union of all `{role}...` and `{group}...` entries derived from their roles and groups.

## Gotchas

- Group names are limited to 100 characters and are matched by **name string** everywhere they appear (user records, crawl-config permission lists, document permissions). Renaming a group therefore requires rewriting every reference; the admin API does not cascade renames.
- Deletion order matters: detach the group from every user (`fessctl user update ... --group ...`) and remove `{group}name` permission strings from any webconfig/fileconfig/dataconfig before deleting the group itself, otherwise you will leave dangling permission strings that grant no access but still appear in records.
- `update` performs a read-modify-write: passing `--attribute` **replaces** the entire attribute map; omit the flag to keep the existing attributes untouched. There is no per-key delete flag.
- `getbyname` works by URL-safe base64-encoding the name and delegating to `get`; if the encoded ID is unknown the call returns the same not-found error as `get`.
- The admin UI exposes only `name`; `attributes` are settable via the API/CLI and are useful when mirroring LDAP, but they are not displayed on the standard UI form in 15.6.
- `--updated-time` defaults to "now" in epoch milliseconds and is only worth overriding for deterministic imports or replays.
- Deleting a group never deletes the users that referenced it; it only orphans the reference.

## Examples

```bash
# Minimal create: just a group name
fessctl group create engineering
```

```bash
# Typical update: replace the attribute map on an existing group
fessctl group update ZW5naW5lZXJpbmc \
  --attribute description='Product engineering org' \
  --attribute ou=Engineering \
  --attribute owner=alice
```

```bash
# List all groups as JSON and filter for those tagged with an LDAP ou attribute
fessctl group list --size 500 --output json \
  | jq '.response.settings[] | select(.attributes.ou != null) | {id, name, ou: .attributes.ou}'
```

## See also

- fess-docs: en/15.6/admin/group-guide.rst
- workflows.md: Recipe 4
- Related features: `references/features/user.md`, `references/features/role.md`
