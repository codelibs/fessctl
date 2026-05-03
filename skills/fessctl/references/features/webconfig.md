# Web Crawl Configs (fessctl `webconfig`)

## What it is

A Web Crawl Config (Web Config) defines how the Fess crawler fetches a web site or web application: where to start crawling, which URLs to follow or index, how aggressively to fetch, and which permissions to attach to the resulting documents. In the admin UI it lives at **Crawler -> Web Config** (left sidebar: "Crawler > Web"). Each entry corresponds to one logical site (for example, a corporate portal, a wiki, or a public homepage).

The `fessctl webconfig` subcommand is a thin CRUD wrapper over the Fess admin API for these entries. It lets you script initial crawl setup, update threading and interval, attach label types and web authentications, and roll out the same configuration across multiple environments.

## When to use

- Bootstrapping a new Fess instance with a fixed set of sites (Infra-as-Code style).
- Tuning crawl parameters (`--num-of-thread`, `--interval-time`, `--depth`) without clicking through the admin UI.
- Disabling a site temporarily for maintenance via `--available false` instead of deleting it.
- Diffing or backing up Web Config definitions by piping `list`/`get` output through `--output json | jq`.

## Subcommand surface

| Subcommand | Purpose | Notes |
|------------|---------|-------|
| `create`   | Create a new Web Config. | Requires `--name` and at least one `--url`. Sensible defaults for threads, interval, excluded URLs, permissions. |
| `update`   | Update an existing Web Config by ID. | Takes positional `CONFIG_ID`. Only fields explicitly passed are overwritten; the rest are preserved via a read-modify-write cycle. |
| `delete`   | Delete a Web Config by ID. | Irreversible. Does not cascade-delete related Web Auth entries. |
| `get`      | Retrieve one Web Config by ID. | Renders a Markdown detail view by default; switch with `--output json` or `--output yaml`. |
| `list`     | List Web Configs. | Supports `--page` / `--size` pagination. Default page size is 100. |

Always reconfirm with `fessctl webconfig <sub> --help`.

## Resource JSON shape

```json
{
  "name": "Fess",                          // required
  "urls": "https://fess.codelibs.org/",    // required, newline-joined when multiple
  "user_agent": "Mozilla/5.0 (compatible; Fess/FessCTL; +http://fess.codelibs.org/bot.html)", // optional, default shown
  "num_of_thread": 1,                       // optional, default 1
  "interval_time": 10000,                   // optional, default 10000 (ms)
  "boost": 1.0,                              // optional, default 1.0
  "available": true,                         // optional, default true
  "sort_order": 1,                           // optional, default 1
  "description": "",                        // optional
  "label_type_ids": [],                     // optional, list of label type IDs
  "included_urls": "",                      // optional, newline-joined regex list
  "excluded_urls": "(?i).*(css|js|jpeg|jpg|gif|png|bmp|wmv|xml|ico|exe)", // optional, default shown
  "included_doc_urls": "",                  // optional
  "excluded_doc_urls": "",                  // optional
  "config_parameter": "",                   // optional, key=value lines (e.g. client.robotsTxtEnabled=false)
  "depth": 1,                                // optional, default 1
  "max_access_count": 1000000,              // optional, default 1000000
  "permissions": "{role}guest",             // optional, default "{role}guest"
  "virtual_hosts": "",                      // optional
  "created_by": "admin",                    // optional, default "admin"
  "created_time": 1714723200000              // optional, defaults to now (epoch ms, UTC)
}
```

## Relationships

- **Label Type** (`fessctl labeltype`): attach via `--label-type-id` to surface this site under a label filter in search results.
- **Web Authentication** (`fessctl webauth`): for protected sites (BASIC, DIGEST, NTLM, Form), create the Web Config first and then bind a Web Auth entry to it by name.
- **Scheduler** (`fessctl scheduler`): the default crawler job picks up entries with `available: true`. Disable a config instead of deleting it to skip a single run.
- **Role / Group / User** (`fessctl role`, `group`, `user`): values referenced by `--permission` (`{role}name`, `{group}name`, `{user}name`) must exist for permissions to take effect.
- Safe deletion order: remove dependent Web Auth entries first, then delete the Web Config, then drop unused Label Types.

## Gotchas

- All multi-value fields (`--url`, `--included-url`, `--excluded-url`, `--config-parameter`, `--permission`, `--virtual-host`) are newline-joined into a single string before being sent to the Fess API; pass the option multiple times instead of comma-separating.
- `update` performs a read-modify-write: if the config ID does not exist the command exits non-zero. Fields not specified retain their current value.
- The default `excluded_urls` regex blocks common static assets. If you actually need to crawl JS/CSS/images, override it explicitly with `--excluded-url ""` (or a narrower pattern).
- Included/Excluded URL patterns are Java regular expressions (per the admin guide), not glob patterns.
- `--available false` removes the entry from the next default crawler run but preserves already-indexed documents; `delete` only removes the configuration record, not the indexed data.
- The `permissions` value must exactly match the Fess permission syntax (`{role}guest`, `{user}alice`, `{group}dev`); free-form names are silently ignored at search time.
- All admin-API calls require an authenticated admin user as configured in `fessctl` settings.
- Virtual host values are matched against incoming search request hosts; see the Fess virtual host documentation before populating this field.

## Examples

```bash
# Minimal: crawl a public site under default settings
fessctl webconfig create \
  --name "Fess" \
  --url "https://fess.codelibs.org/" \
  --included-url "https://fess.codelibs.org/.*"
```

```bash
# Typical update: bump threads and interval for an existing config
fessctl webconfig update W1a2b3c4d5 \
  --num-of-thread 3 \
  --interval-time 5000 \
  --description "Tuned for nightly full crawl"
```

```bash
# List all configs and filter the disabled ones for review
fessctl webconfig list --size 200 --output json \
  | jq '.response.settings[] | select(.available == false) | {id, name, sort_order}'
```

## See also

- fess-docs: en/15.6/admin/webconfig-guide.rst
- workflows.md: Recipe 1 (initial web crawl setup)
- Related features: `references/features/labeltype.md`, `references/features/webauth.md`, `references/features/scheduler.md`
