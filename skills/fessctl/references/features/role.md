# Roles (fessctl `role`)

## What it is

Roles let you group users for the purpose of access control inside Fess. A role is a thin object — essentially just a name plus optional attributes — but it becomes meaningful when referenced from users, groups, and crawl configurations (web/file/data). Roles are especially useful when integrating with LDAP or other external identity systems, where role names typically map to directory groups.

In the admin UI, roles are managed under **User > Role** (left sidebar). The list page shows all roles; clicking a role name opens its edit screen, and a Delete button is available there as well.

`fessctl role` exposes the same CRUD surface over the admin REST API, so role provisioning can be scripted alongside user/group setup.

## When to use

- Preparing access-controlled search by creating roles such as `admin`, `sales`, or `engineering` before assigning them to users.
- Mirroring LDAP/AD groups into Fess so that crawled documents can be tagged with the same role names.
- Restricting a `webconfig`/`fileconfig`/`dataconfig` to a subset of users by attaching roles via the permissions field (`{role}name`).
- Auditing or exporting the current role list as JSON/YAML for backup or diffing across environments.

## Subcommand surface

| Subcommand | Purpose |
|---|---|
| `create` | Create a new role with a name (max 100 chars) and optional `--attribute key=value` pairs. |
| `update` | Update an existing role by ID. Re-fetches current state, then applies new attributes / `--updated-by` / `--updated-time`. |
| `delete` | Delete a role by ID. |
| `getbyname` | Convenience: look up a role by its name (URL-safe base64 encodes the name and delegates to `get`). |
| `get` | Retrieve a single role by ID and render details. |
| `list` | List roles with `--page` / `--size` pagination. |

Always reconfirm with `fessctl role <sub> --help`.

## Resource JSON shape

```json
{
  "name": "sales",                  // required, max 100 chars
  "attributes": {                   // optional, default {} — free-form key/value map
    "ldap_dn": "cn=sales,ou=groups,dc=example,dc=com"
  },
  "id": "AY...",                    // optional, default server-assigned on create; required for update/delete
  "version_no": 1,                  // optional, default managed by server (optimistic locking)
  "crud_mode": 2,                   // optional, default set by fessctl on update (2 = edit)
  "updated_by": "admin",            // optional, default "admin" on update
  "updated_time": 1735689600000     // optional, default current UTC epoch millis on update
}
```

## Relationships

- Referenced by `user` resources via the `roles` array — a user inherits all permissions implied by their roles.
- Referenced by `group` resources via the `roles` array — group membership can carry roles transitively.
- Referenced by `webconfig`, `fileconfig`, and `dataconfig` permissions strings using the `{role}name` syntax (e.g., `{role}admin`). Documents crawled under such a config become searchable only by users who hold that role.
- Role names also appear in search-time access control: query-time role filtering uses the same names.

## Gotchas

- **Name length**: limited to 100 characters; longer names are rejected by the API.
- **Naming conventions**: stick to lowercase alphanumerics and avoid spaces/special characters — role names appear verbatim inside permission strings like `{role}sales` and in URL-safe base64 lookups (`getbyname`).
- **Deletion order**: before deleting a role, remove or update any `user`/`group` that lists it in `roles`, and any `webconfig`/`fileconfig`/`dataconfig` whose `permissions` references `{role}<name>`. Otherwise you will leave dangling references that silently exclude documents from search results.
- **Optimistic locking**: `version_no` is managed by the server. `update` re-fetches the role first to obtain the current version; do not hand-edit it.
- **`getbyname`**: encodes the name with URL-safe base64 before calling the `get` endpoint — confirm the role actually exists with `list` if `getbyname` returns not-found.
- **Built-in `admin` role**: the bundled administrator account ships with an `admin` role; renaming or deleting it can lock you out of the admin UI.
- **Attribute schema**: `attributes` is free-form. Keys are not validated by the server, so typos silently succeed.

## Examples

Minimal create:

```bash
fessctl role create sales
```

Typical update (replace attributes on an existing role):

```bash
fessctl role update AYxxxxxxxxxxxxxxxxxx \
  --attribute ldap_dn='cn=sales,ou=groups,dc=example,dc=com' \
  --attribute description='Sales team' \
  --updated-by admin
```

List and filter via JSON output:

```bash
fessctl role list --size 200 --output json \
  | jq -r '.response.settings[] | select(.name | startswith("sales")) | "\(.id)\t\(.name)"'
```

## See also

- fess-docs: en/15.6/admin/role-guide.rst
- workflows.md: Recipe 4 (provisioning a user with admin permissions)
- Related features: `references/features/user.md`, `references/features/group.md`
