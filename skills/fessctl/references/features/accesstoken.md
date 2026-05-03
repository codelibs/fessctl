# Access Tokens (fessctl `accesstoken`)

## What it is

An access token is a credential issued by Fess that authorizes calls to the Fess admin and search APIs. In the admin UI it is managed under **System -> Access Token**, where each token carries a name, a permission expression, an optional request-parameter alias, and an optional expiration date. Permissions are written using the `{user|group|role}name` notation (for example `{group}developer`) and define the privilege the token confers on requests it accompanies.

The `fessctl accesstoken` command group wraps the corresponding admin API endpoints so you can provision, inspect, modify, and revoke tokens from automation and scripts. This is useful for CI pipelines, scheduled audits, and bulk lifecycle management where the web UI is not practical.

Note that fessctl itself authenticates every privileged call with an access token supplied via the `FESS_ACCESS_TOKEN` environment variable (see `references/authentication.md`). The token you create with `fessctl accesstoken create` is the same kind of token fessctl consumes, so this command effectively bootstraps and maintains the credentials for fessctl itself and for any other API client.

## When to use

- Provision a long-lived service-account token for a CI job that pushes crawl configs, schedulers, or dictionaries via fessctl.
- Rotate an existing token by creating a replacement, updating the consumer's environment, then deleting the old one.
- Audit issued tokens (names, permissions, expiration) by listing them in JSON for downstream review or compliance reporting.
- Issue a short-lived token with an `--expires` value for a one-off integration or contractor.

## Subcommand surface

| Subcommand | Required arguments | Key options | Purpose |
|------------|--------------------|-------------|---------|
| `create`   | `--name`           | `--token`, `--permission` (repeatable), `--parameter-name`, `--expires`, `--created-by`, `--created-time`, `--output/-o` | Create a new access token. |
| `update`   | `accesstoken_id` (positional) | `--name`, `--token`, `--permission` (repeatable), `--parameter-name`, `--expires`, `--updated-by`, `--updated-time`, `--output/-o` | Update an existing token in place. |
| `delete`   | `accesstoken_id` (positional) | `--output/-o` | Delete a token by ID. |
| `get`      | `accesstoken_id` (positional) | `--output/-o` | Retrieve full details for a single token. |
| `list`     | (none)             | `--page/-p`, `--size/-s`, `--output/-o` | List tokens with pagination. |

Always reconfirm with `fessctl accesstoken <sub> --help`.

## Resource JSON shape

```json
{
  "crud_mode": 1,
  "name": "ci-pipeline",
  "token": "optional-explicit-token-string",
  "permissions": "{role}admin\n{group}developer",
  "parameter_name": null,
  "expires": "2026-12-31T23:59:59",
  "created_by": "admin",
  "created_time": 1746230400000,
  "updated_by": "admin",
  "updated_time": 1746230400000
}
```

Required on create: `name` and at least one entry in `permissions` (passed as repeated `--permission` flags, joined with newlines by fessctl). `expires` is optional but recommended for non-service tokens; the CLI accepts `yyyy-MM-ddTHH:mm:ss`. `parameter_name` is optional and only meaningful for trusted internal embedding scenarios. `crud_mode` is set automatically (`1` for create, `2` for update).

## Relationships

- The token authorizes a fessctl session: the value is sent on every API call via `FESS_ACCESS_TOKEN`, so this resource is the gate for all other `fessctl` subcommands.
- Permission strings reference users, groups, and roles defined under `references/features/user.md` and `references/features/role.md` (and groups). Those entities must exist for the permission to resolve at request time.
- See `references/authentication.md` for how fessctl consumes the issued token.
- The `parameter_name` field interacts with the search API's permission-via-query-parameter feature; only enable it on trusted internal networks.

## Gotchas

- The full token value is shown only at creation time; if you discard it you must create a new token and delete the old one.
- Deleting the token currently used by your fessctl session (the value in `FESS_ACCESS_TOKEN`) immediately invalidates that session and logs you out of subsequent API calls.
- Permission strings are exact: use the documented `{user}name`, `{group}name`, `{role}name` form (for example `{role}admin-api`). Typos silently grant nothing.
- Treat tokens as secrets: never commit them to git, never echo them into shared logs, and store them in a secrets manager or CI secret store.
- `--permission` is repeatable; pass the flag once per permission entry rather than comma-joining values.
- `--expires` uses `yyyy-MM-ddTHH:mm:ss` (no timezone suffix); the server interprets it in its configured timezone.
- `update` performs a read-modify-write: fields you do not pass are preserved from the current record, but `--permission` replaces the entire permission list when supplied.

## Examples

```bash
# Minimal create: issue a token for an admin-API role with a hard expiration
fessctl accesstoken create \
  --name ci-pipeline \
  --permission '{role}admin-api' \
  --expires 2026-12-31T23:59:59
```

```bash
# Update: rename and replace permissions on an existing token
fessctl accesstoken update <ACCESSTOKEN_ID> \
  --name ci-pipeline-prod \
  --permission '{role}admin-api' \
  --permission '{group}release'
```

```bash
# List and filter via JSON output
fessctl accesstoken list --size 200 --output json \
  | jq '.response.settings[] | select(.expires == null or .expires < "2026-06-01") | {id, name, expires, permissions}'
```

## See also

- fess-docs: en/15.6/admin/accesstoken-guide.rst
- workflows.md: n/a
- Related features: `references/features/user.md`, `references/features/role.md`, plus cross-link `references/authentication.md`
