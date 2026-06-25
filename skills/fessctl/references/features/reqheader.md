# Request Header (fessctl `reqheader`)

## What it is
Request Headers are extra HTTP headers that Fess attaches to outgoing fetches when its web crawler retrieves documents. Each header is a name/value pair bound to a specific Web Crawl Configuration (`web_config_id`), so the same crawler can target multiple sites while sending different headers to each one.

Typical headers include `User-Agent`, `Cookie`, `Accept-Language`, `Authorization`, or any custom token (e.g. `X-Api-Key`) that the upstream site requires. The fess-docs guide notes these can be used to drive automatic login on systems whose authentication is keyed on header values.

In the Admin UI this resource lives under "Crawler > Request Header". The `fessctl reqheader` subcommand exposes the same CRUD surface via the admin API.

## When to use
- Inject an API token (`Authorization: Bearer ...` or `X-Api-Key: ...`) when crawling a protected internal endpoint that does not use HTTP Basic / Digest auth (which would belong to `webauth`).
- Override the default crawler `User-Agent` so analytics or WAF rules can identify Fess traffic separately from real users.
- Send `Accept-Language: ja-JP` (or similar) so a multilingual site returns the locale you want indexed.
- Pass a sticky `Cookie` header for sites whose session is provisioned out-of-band and merely needs to be replayed on each fetch.

## Subcommand surface
| Subcommand | Required args | Key options | Purpose |
|---|---|---|---|
| `create` | `--name`, `--value`, `--web-config-id` | `--created-by`, `--created-time`, `--output/-o` | Register a new header bound to a web config. |
| `update` | `REQHEADER_ID` (positional) | `--name`, `--value`, `--web-config-id`, `--updated-by`, `--updated-time`, `--output/-o` | Patch fields on an existing header (fetched then merged). |
| `delete` | `REQHEADER_ID` (positional) | `--output/-o` | Remove the header by ID. |
| `get` | `REQHEADER_ID` (positional) | `--output/-o` | Show one header's details. |
| `list` | none | `--page/-p`, `--size/-s`, `--output/-o` | Paginated listing (default `size=100`). |

Always reconfirm with `fessctl reqheader <sub> --help`.

## Resource JSON shape
```json
{
  "crud_mode": 1,
  "name": "X-Api-Key",
  "value": "s3cr3t-token",
  "web_config_id": "WEB-CONFIG-ID-HERE",
  "created_by": "admin",
  "created_time": 1735689600000,
  "updated_by": "admin",
  "updated_time": 1735689600000
}
```
Required on create: `name` (max 100), `value` (max 1000), `web_config_id` (max 1000). `crud_mode` is set automatically by fessctl (`1` for create, `2` for update). On `get`, the response also exposes audit fields (`id`, `version_no`) and may surface auxiliary fields rendered by the detail formatter (`hostname`, `port`, `auth_realm`, `protocol_scheme`, `username`, `password`, `parameters`).

## Relationships
- Depends on `webconfig`: the `--web-config-id` MUST point to an existing Web Crawl Configuration (`fessctl webconfig list`). The header only fires for crawls run by that web config.
- Complementary to `webauth`: use `webauth` for Basic / Digest / NTLM / Form auth; use `reqheader` for token / cookie / custom header auth.
- Has no link to `fileconfig` or `dataconfig` — it applies only to web (HTTP) fetches.

## Gotchas
- Secret hygiene: header values are stored in plain text in the Fess index. Treat tokens like credentials — do not paste them into shell history (`HISTFILE`), shared logs, or `--output json` dumps you commit to git. Consider sourcing the value from `$ENV_VAR` at the call site.
- A `User-Agent` reqheader overrides the default crawler UA configured in `fess_config.properties` for that web config only. Verify the change with a probe request before relying on it.
- `update` performs a fetch-then-merge: the current record is read, your `--name` / `--value` / `--web-config-id` overlay it, then the whole document is re-sent. Omitted flags are preserved, not cleared.
- Deleting a reqheader does NOT cascade to or modify the parent webconfig; the crawl simply stops sending that header on the next run. Conversely, deleting a webconfig leaves orphan reqheader rows referencing a missing `web_config_id` — clean them up explicitly.
- `created_time` / `updated_time` default to "now" in UTC milliseconds. Override only when reproducing or migrating data.
- `list` is paginated (`--page`, `--size`, default `size=100`); pipe through `jq` for filtering since there is no server-side `--name` filter flag.

## Examples
Minimal create — bind an API key header to an existing web config:
```bash
fessctl reqheader create \
  --name "X-Api-Key" \
  --value "$INTERNAL_API_TOKEN" \
  --web-config-id "WEB-CFG-123abc"
```

Update the value (e.g. token rotation) without touching name or binding:
```bash
fessctl reqheader update REQHDR-456def \
  --value "$NEW_INTERNAL_API_TOKEN" \
  --updated-by "rotation-bot"
```

List and filter by web config via JSON output:
```bash
fessctl reqheader list --output json \
  | jq '.response.settings[] | select(.web_config_id == "WEB-CFG-123abc")'
```

## See also
- fess-docs: en/15.6/admin/reqheader-guide.rst
- workflows.md: n/a
- Related features: `references/features/webconfig.md`, `references/features/webauth.md`
