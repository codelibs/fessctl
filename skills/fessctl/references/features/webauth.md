# Web Authentication Credentials (fessctl `webauth`)

## What it is

Web Authentication entries store the credentials Fess presents to protected web sites during a crawl. Each row binds a username/password (and optional realm, port, scheme parameters) to a specific Web Crawl Config so that the crawler can fetch pages that require login. Without a matching `webauth` row, requests to protected URLs return 401/403 and the crawler skips them.

In the admin UI this corresponds to **Crawler -> Web Authentication** (left menu). Records are managed independently of the web config rows but cannot exist without one — the relationship is enforced by `web_config_id`.

Fess supports four authentication schemes for web crawling:

- **BASIC** — RFC 7617 HTTP Basic auth.
- **DIGEST** — RFC 7616 HTTP Digest auth.
- **NTLM** — NT LAN Manager auth (Windows / corporate intranets); requires `workstation` and `domain` via the Parameters field.
- **FORM** — HTML form-based login (handled via the `form_scheme` config on the related web config; the credentials live here).

## When to use

- Crawling a private corporate portal (SharePoint, intranet wiki, JIRA) that sits behind BASIC or NTLM auth.
- Ingesting pages from a legacy web app that prompts via DIGEST.
- Crawling a SaaS or CMS site whose content is only visible after a FORM login.
- Rotating a service-account password without touching the underlying web config.

## Subcommand surface

| Command  | Decorator                       | Purpose                                         | Key inputs                                                                 |
|----------|---------------------------------|-------------------------------------------------|----------------------------------------------------------------------------|
| `create` | `@webauth_app.command("create")` | Register a new credential row                   | `--username`, `--web-config-id` (required); `--password`, `--hostname`, `--port`, `--auth-realm`, `--protocol-scheme`, `--parameters`, `--created-by`, `--created-time`, `--output/-o` |
| `update` | `@webauth_app.command("update")` | Modify an existing credential by ID             | `config_id` (positional); same optional fields as create plus `--web-config-id`, `--updated-by`, `--updated-time`, `--output/-o` |
| `delete` | `@webauth_app.command("delete")` | Remove a credential by ID                       | `config_id` (positional); `--output/-o`                                    |
| `get`    | `@webauth_app.command("get")`    | Fetch a single credential row                   | `config_id` (positional); `--output/-o`                                    |
| `list`   | `@webauth_app.command("list")`   | List credentials (paged)                        | `--page/-p` (default 1), `--size/-s` (default 100), `--output/-o`           |

Always reconfirm with `fessctl webauth <sub> --help`.

## Resource JSON shape

```json
{
  "id": "abc123",
  "crud_mode": 1,
  "hostname": "intranet.example.com",
  "port": 443,
  "auth_realm": "Corporate",
  "protocol_scheme": "BASIC",
  "username": "svc-crawler",
  "password": "REDACTED",
  "parameters": "workstation=WS01\ndomain=CORP",
  "web_config_id": "WCID-XYZ",
  "created_by": "admin",
  "created_time": 1714723200000,
  "updated_by": "admin",
  "updated_time": 1714723200000,
  "version_no": 1
}
```

Required on create: `username`, `web_config_id`. All other fields are optional but at least `password` and `protocol_scheme` are needed for a working credential. `port = -1` means "any port".

## Relationships

- Depends on `webconfig`: every `webauth` row binds to a single Web Crawl Config via `web_config_id`. Create the webconfig first, then attach credentials.
- Multiple `webauth` rows may share a single `web_config_id` (e.g., one per hostname or realm).
- For FORM authentication, the form-submission scheme itself is configured on the related webconfig; only the credentials live in `webauth`.
- NTLM relies on the `parameters` field for `workstation` / `domain` — these are part of the auth contract, not the webconfig.

## Gotchas

- **Secret hygiene**: passing `--password` puts the secret in shell history and the process list. Prefer reading from a file or env var (e.g., `--password "$WEBAUTH_PW"` after `read -rs WEBAUTH_PW`) and clearing the variable afterwards.
- **Scheme casing**: Fess expects upper-case scheme tokens (`BASIC`, `DIGEST`, `NTLM`, `FORM`). Lower-case values may be accepted but are not idiomatic.
- **NTLM domain syntax**: use newline-separated `workstation=...` / `domain=...` inside `--parameters`. Quote the whole value in the shell, e.g. `--parameters $'workstation=WS01\ndomain=CORP'`.
- **Port semantics**: `--port -1` means "match any port"; omitting `--port` does the same. Do not set `0`.
- **Hostname omitted**: if `--hostname` is absent, the credential applies to every host reachable via the bound webconfig — handy but easy to over-share.
- **Deletion does NOT cascade**: removing a `webauth` row leaves its `web_config_id` intact. Conversely, deleting the webconfig does not remove orphan webauth rows; clean them up explicitly.
- **Update preserves unspecified fields**: `update` first re-fetches the existing row, so omitted flags keep their stored values. Use this to rotate just the password without resending hostname/port.

## Examples

Minimal create (BASIC auth bound to an existing webconfig):

```bash
fessctl webauth create \
  --username svc-crawler \
  --password 'S3cretPa$$' \
  --web-config-id WCID-XYZ \
  --hostname intranet.example.com \
  --port 443 \
  --protocol-scheme BASIC
```

Update — rotate the password without touching anything else:

```bash
read -rs NEW_PW
fessctl webauth update <WEBAUTH_ID> --password "$NEW_PW" --updated-by admin
unset NEW_PW
```

List and filter via JSON output (find all credentials bound to one webconfig):

```bash
fessctl webauth list --output json \
  | jq '.response.settings[] | select(.web_config_id == "WCID-XYZ") | {id, username, hostname, port}'
```

## See also

- fess-docs: en/15.6/admin/webauth-guide.rst
- workflows.md: Recipe 1
- Related features: `references/features/webconfig.md`
