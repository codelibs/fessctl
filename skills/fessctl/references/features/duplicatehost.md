# Duplicate Host (fessctl `duplicatehost`)

## What it is

Duplicate Host configurations tell the Fess crawler to treat one or more hostnames as equivalent to a single canonical hostname. At crawl time, any URL whose host matches a registered duplicate name is rewritten so that its host becomes the configured regular (canonical) name. This prevents the same content from being fetched, stored, and indexed twice when it is reachable through multiple equivalent hostnames such as `www.example.com` and `example.com`.

The feature is managed in the admin UI under **Crawler > Duplicate Hosts**. Each rule is a simple pair: a Regular Name (the canonical hostname that should appear in the index) and a Duplicate Name (the hostname that will be replaced). Rules are evaluated globally for every web crawl run by the server.

Because the rewrite happens during URL normalization in the crawler, duplicate-host rules apply uniformly to all web crawl configurations on the instance and do not require per-config wiring.

## When to use

- Consolidate `www.example.com` and `example.com` (or other host aliases) into a single canonical host so duplicate documents are not indexed.
- Treat staging or mirror hostnames (for example `mirror.example.com`) as the production host for indexing purposes.
- Normalize legacy or rebranded hostnames after a domain migration so old URLs collapse onto the new canonical name.
- Combine multiple regional hostnames that serve identical content under one canonical name when intentional.

## Subcommand surface

| Subcommand | Purpose | Key inputs |
|------------|---------|------------|
| `create` | Register a new duplicate-host rule. | `--regular-name`, `--duplicate-host-name`, `--sort-order`, optional `--created-by`, `--created-time`, `--output` |
| `update` | Modify an existing rule by ID; only provided fields are changed. | `config_id` (positional), optional `--regular-name`, `--duplicate-host-name`, `--sort-order`, `--updated-by`, `--updated-time`, `--output` |
| `delete` | Remove a rule by ID. | `config_id` (positional), `--output` |
| `get` | Show details of a single rule by ID. | `config_id` (positional), `--output` |
| `list` | List rules with pagination. | `--page`/`-p`, `--size`/`-s`, `--output`/`-o` |

Always reconfirm with `fessctl duplicatehost <sub> --help`.

## Resource JSON shape

```json
{
  "crud_mode": 1,
  "regular_name": "www.example.com",
  "duplicate_host_name": "example.com",
  "sort_order": 1,
  "created_by": "admin",
  "created_time": 1730000000000
}
```

On `update`, the client first fetches the existing setting, sets `crud_mode` to `2`, and overlays `updated_by` and `updated_time` plus any of `regular_name`, `duplicate_host_name`, or `sort_order` you supplied. Read responses (`get`, `list`) also expose `id` and `version_no` returned by the server.

## Relationships

- Rewriting is performed at crawl time during URL normalization, before fetch and storage.
- Rules apply globally to every web crawl; they are not bound to a specific `webconfig` entry.
- They affect what hostname is recorded in the index, so they interact with deduplication and reporting.
- Path-level normalization (`pathmap`) is independent and can be combined with duplicate-host rules.

## Gotchas

- Existing indexed documents are not rewritten. After adding or changing a rule, recrawl the affected sites and remove or expire stale documents to actually collapse duplicates.
- `regular_name` and `duplicate_host_name` are matched as host strings; ports, schemes, and paths are not part of the rule.
- IP addresses and FQDNs are distinct hosts. If a site is reachable both as `192.0.2.10` and `example.com`, register both directions as needed.
- Internationalized Domain Names should be supplied in the form the crawler observes (typically Punycode `xn--...`); mixing Unicode and ASCII forms can lead to non-matching rules.
- `sort_order` is required on `create` and must be a non-negative integer; it controls the order in admin listings, not match precedence.
- `created_time` and `updated_time` default to "now" in milliseconds (UTC). Override only when reproducing or backdating records.

## Examples

```bash
# Minimal create: collapse example.com into www.example.com
fessctl duplicatehost create \
  --regular-name www.example.com \
  --duplicate-host-name example.com \
  --sort-order 1
```

```bash
# Update an existing rule to change the duplicate hostname
fessctl duplicatehost update <config_id> \
  --duplicate-host-name old.example.com \
  --sort-order 5
```

```bash
# List rules and filter for a specific regular name via jq
fessctl duplicatehost list --output json \
  | jq '.response.settings[] | select(.regular_name == "www.example.com")'
```

## See also

- fess-docs: en/15.6/admin/duplicatehost-guide.rst
- workflows.md: n/a
- Related features: `references/features/webconfig.md`, `references/features/pathmap.md`
