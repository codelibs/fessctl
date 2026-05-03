# Users (fessctl `user`)

## What it is

The User feature manages the authenticated principals that can log in to Fess (both administrators and end users for permission-restricted search). It is reached through the admin UI menu path **User → User**, where you can list, create, edit, and delete user accounts. Each user has a name and password, and may be associated with one or more roles and/or groups.

In Fess's authorization model, a *user* is the identity that authenticates, a *role* is a permission grant attached to crawl configurations and documents, and a *group* is an organizational bucket for collecting users. Roles drive access control on indexed content; groups are an additional grouping primitive that can also be used in role-based filtering. A user inherits the union of permissions from every role and group it belongs to.

The `fessctl user` command exposes the same admin REST API used by the UI, so it is suitable for scripted provisioning, CI bootstrap, and bulk audits.

## When to use

- Provision a new administrator account during initial Fess bootstrap (a user attached to the `admin` role).
- Create a search-only viewer account so internal users can hit role-restricted documents.
- Rotate or reset the password of an existing account after a security event.
- Audit the user directory by dumping `list --output json` and filtering with `jq`.
- Re-assign a user from one team's group/role to another during a re-org.

## Subcommand surface

| Subcommand | Purpose | Key arguments / options |
|------------|---------|-------------------------|
| `create` | Create a new user. | `name` (arg), `password` (arg), `--attribute/-a key=value` (repeatable), `--role/-r` (repeatable), `--group/-g` (repeatable), `--output/-o` |
| `update` | Update an existing user (fetched then merged). | `user_id` (arg), `--password/-p`, `--attribute/-a`, `--role/-r`, `--group/-g`, `--updated-by`, `--updated-time`, `--output/-o` |
| `delete` | Delete a user by ID. | `user_id` (arg), `--output/-o` |
| `getbyname` | Resolve a user by name (URL-safe base64 encodes the name and calls `get`). | `name` (arg), `--output/-o` |
| `get` | Retrieve a user's full record by ID. | `user_id` (arg), `--output/-o` |
| `list` | List users with pagination. | `--page/-p` (default 1), `--size/-s` (default 100), `--output/-o` |

Always reconfirm with `fessctl user <sub> --help`.

## Resource JSON shape

```json
{
  "crud_mode": 2,
  "id": "QWRtaW4",
  "name": "alice",
  "password": "PLAINTEXT_AT_SUBMIT",
  "confirm_password": "PLAINTEXT_AT_SUBMIT",
  "roles": ["admin", "search-user"],
  "groups": ["engineering"],
  "attributes": {
    "mail": "alice@example.com",
    "surname": "Doe",
    "givenName": "Alice",
    "employeeNumber": "E-1024",
    "departmentNumber": "42",
    "title": "Staff Engineer"
  },
  "updated_by": "admin",
  "updated_time": 1714694400000,
  "version_no": 1
}
```

Required on create: `name` and `password` (the CLI auto-fills `confirm_password` to match). `roles`, `groups`, and `attributes` are optional. Extended LDAP-style fields such as `mail`, `surname`, `givenName`, `employeeNumber`, etc. are passed through the `--attribute` map rather than as top-level flags.

## Relationships

- A user references **role** names (strings) via the `roles` array. Each name must already exist as a Fess role; see `references/features/role.md`.
- A user references **group** names (strings) via the `groups` array. Each name must already exist as a Fess group; see `references/features/group.md`.
- API tokens issued for this principal live in the access-token resource; see `references/features/accesstoken.md`.
- Deletion order: delete (or reassign) the **users** first, then the role or group they reference. Removing a role or group that is still listed inside an active user record can leave dangling permission strings.
- `roles` and `groups` are matched by **name string**, not by internal ID, so renaming a role/group requires updating every user that references it.

## Gotchas

- Passwords are submitted in plaintext over the admin API; always run against TLS-protected endpoints. Fess hashes them server-side per `fess_config.properties`.
- The built-in `admin` user is special: deleting it locks you out of the admin UI. Rotate its password with `update` instead of recreating it.
- Password rotation is only possible through `update` (`--password`); there is no dedicated `passwd` subcommand. The CLI rejects passwords longer than 100 characters.
- Deleting the user you are currently authenticated as immediately invalidates your session.
- Role and group references are plain strings: a typo silently grants no permissions rather than erroring.
- `update` performs read-modify-write: omitted flags fall back to the existing values, but explicitly passing `--role` or `--group` **replaces** the entire list, it does not append.
- `getbyname` works by URL-safe base64-encoding the name and reusing `get`; it will fail the same way `get` does if the resulting ID is unknown.
- `--updated-time` defaults to "now" in epoch milliseconds; only override it for deterministic reproductions or imports.

## Examples

```bash
# Minimal create: just username and password
fessctl user create alice 'S3cret!Pass'
```

```bash
# Typical update: rotate password and replace role/group assignment
fessctl user update QWxpY2U \
  --password 'N3wS3cret!' \
  --role admin \
  --role search-user \
  --group engineering
```

```bash
# Audit: list users as JSON and show only those with the admin role
fessctl user list --size 500 --output json \
  | jq '.response.settings[] | select(.roles | index("admin")) | {id, name, roles, groups}'
```

## See also

- fess-docs: en/15.6/admin/user-guide.rst
- workflows.md: Recipe 4 (provisioning a user with admin permissions)
- Related features: `references/features/role.md`, `references/features/group.md`, `references/features/accesstoken.md`
