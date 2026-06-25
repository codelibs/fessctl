# Label Types (fessctl `labeltype`)

## What it is
Label Types classify documents in the Fess search index. Each label has a human-readable `name` (shown to end users) and a machine-readable `value` (the identifier persisted on each document). Inclusion/exclusion is driven by URL regular-expression patterns: any crawled document whose URL matches an `included_paths` regex (and does not match `excluded_paths`) is tagged with that label at index time.

In the admin UI labels are managed at `Crawler > Label`. Once at least one label is registered, a label pull-down appears in the search options so end users can filter results, and the same labels surface as facets/refinements alongside the result list. Labels are also referenced from web, file, and data store crawl configs to scope which crawl jobs may emit which labels.

## When to use
- Categorize crawled web/file content by department, product, or site (e.g. "HR docs", "Engineering wiki") so the same Fess instance serves many audiences.
- Give end users a one-click facet to narrow a search to a known subset (e.g. "Manuals only" vs "All content").
- Carve out a virtual-host-specific catalog when the same Fess instance is fronted by multiple hostnames.
- Combine with `--permission` to scope a label so only certain roles/groups/users see it in the dropdown and in results.

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `create` | Register a new label type. | `--name`, `--value`, `--version-no` |
| `update` | Modify an existing label type by ID; unspecified fields are preserved. | `<config_id>` |
| `delete` | Permanently delete a label type by ID. | `<config_id>` |
| `get` | Show one label type's full detail. | `<config_id>` |
| `list` | Page through all label types (default page size 100). | none |

Always reconfirm with `fessctl labeltype <sub> --help`.

## Resource JSON shape
```json
{
  "crud_mode": 1,
  "name": "Engineering",
  "value": "eng",
  "version_no": 1,
  "sort_order": 0,
  "included_paths": "https://wiki.example.com/eng/.*\nhttps://docs.example.com/eng/.*",
  "excluded_paths": "https://wiki.example.com/eng/private/.*",
  "permissions": "{role}admin\n{group}developer",
  "virtual_host": "eng.search.example.com",
  "created_by": "admin",
  "created_time": 1714694400000,
  "updated_by": "admin",
  "updated_time": 1714694400000
}
```
Required: `name`, `value`, `version_no`. Optional: `sort_order`, `included_paths`, `excluded_paths`, `permissions`, `virtual_host`. The CLI accepts repeatable `--included-path`, `--excluded-path`, and `--permission` flags and joins them with newlines before posting (matching the admin UI's multi-line text areas).

## Relationships
- Web crawl configs (`fessctl webconfig`) reference labels via `label_type_ids` so a single web crawl can tag every emitted document.
- File system crawl configs (`fessctl fileconfig`) reference labels the same way via `label_type_ids`.
- Data store configs (`fessctl dataconfig`) also accept `label_type_ids` to tag rows ingested from external sources.
- Labels surface in the search UI as a pull-down filter and in the JSON search response as facets/refinements.
- `permissions` entries follow the standard `{user}name`, `{role}name`, `{group}name` syntax shared with role/group management.
- `virtual_host` ties into the Virtual Host configuration documented under `config/security-virtual-host`.

## Gotchas
- Labels are written onto documents at index time. Adding, renaming, or re-scoping a label has no effect on already-indexed content until you recrawl the affected configs.
- `value` is the identifier stored on every document and used in queries; restrict it to alphanumeric characters and avoid changing it after content has been indexed (existing docs would be orphaned).
- Deleting a label that is still listed in a crawl config's `label_type_ids` leaves dangling references. Either drop the label from each `webconfig`/`fileconfig`/`dataconfig` first, or accept that the references will resolve to nothing.
- `included_paths` and `excluded_paths` are regular expressions, not glob patterns; remember to escape `.` and anchor with `.*` where appropriate.
- `--version-no` is required on `create` and is used for optimistic concurrency on `update`; bump it deliberately when scripting bulk updates.
- `created_time`/`updated_time` are epoch milliseconds (UTC). The CLI auto-fills them with "now" if omitted.

## Examples
```bash
# Minimal create: a label that tags everything under /docs/
fessctl labeltype create \
  --name "Documentation" \
  --value docs \
  --version-no 1 \
  --included-path "https://www.example.com/docs/.*"
```

```bash
# Update: add an exclusion and restrict visibility to the developer group
fessctl labeltype update LABEL_ID \
  --excluded-path "https://www.example.com/docs/internal/.*" \
  --permission "{group}developer"
```

```bash
# List and filter via JSON output to find a label by value
fessctl labeltype list --output json \
  | jq '.response.settings[] | select(.value == "docs")'
```

## See also
- fess-docs: en/15.6/admin/labeltype-guide.rst
- workflows.md: Recipe 1
- Related features: `references/features/webconfig.md`, `references/features/fileconfig.md`, `references/features/dataconfig.md`
