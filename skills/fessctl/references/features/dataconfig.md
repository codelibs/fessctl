# Datastore Configs (fessctl `dataconfig`)

## What it is

Fess supports crawling content from data sources that are not plain web pages or files — relational databases, CSV/TSV files, SaaS APIs (Slack, SharePoint), Elasticsearch indexes, and more. Each such source is configured as a **Data Store** crawl, which pairs a **handler** (the connector implementation) with a free-form **parameter** block and a **Groovy script** that maps source records to Fess document fields.

In the admin UI this lives at **Crawler > Data Store** (`/admin/dataconfig/`). From there you can create, edit, and delete data store crawl configurations. Each entry has a name, a handler name (e.g. `DatabaseDataStore`, `CsvDataStore`, `EsDataStore`, `CsvListDataStore`, or one provided by an installed `fess-ds-*` plugin), parameters, a script, boost, permissions, virtual hosts, sort order, status, and description.

In fessctl terminology, "datastore" specifically refers to a `fess-ds-*` connector or a built-in handler. The actual ingestion is triggered by a scheduler job that invokes the configured handler against the configured parameters.

## When to use

- Crawl a relational database (MySQL, PostgreSQL, Oracle) using `DatabaseDataStore` and a JDBC driver placed in `app/WEB-INF/lib`.
- Index CSV/TSV files in bulk via `CsvDataStore`, mapping each row to a Fess document.
- Crawl a large file tree incrementally with `CsvListDataStore`, where the CSV lists changed paths and actions (create/modify/delete).
- Ingest content from a SaaS source via an installed plugin — e.g. `fess-ds-slack`, `fess-ds-sharepoint`, `fess-ds-confluence`, `fess-ds-s3`. Each plugin registers its own handler name.

## Subcommand surface

| Subcommand | Purpose | Key arguments |
|---|---|---|
| `create` | Create a new DataConfig | `--name`, `--handler-name`, `--boost`, `--available`, `--sort-order`, `--description`, `--handler-parameter`, `--handler-script`, `--permission` (repeatable), `--virtual-host` (repeatable), `--created-by`, `--created-time`, `--output` |
| `update` | Update an existing DataConfig by ID | `config_id` (positional); same flags as `create`, all optional; plus `--updated-by`, `--updated-time`, `--output` |
| `delete` | Delete a DataConfig by ID | `config_id` (positional), `--output` |
| `get` | Retrieve one DataConfig by ID | `config_id` (positional), `--output` |
| `list` | List DataConfigs (paginated) | `--page`/`-p`, `--size`/`-s`, `--output`/`-o` |

Always reconfirm with `fessctl dataconfig <sub> --help`.

## Resource JSON shape

```json
{
  "crud_mode": 1,
  "name": "products-db",
  "handler_name": "DatabaseDataStore",
  "handler_parameter": "driver=com.mysql.cj.jdbc.Driver\nurl=jdbc:mysql://db.example.com:3306/shop?useUnicode=true&characterEncoding=UTF-8\nusername=fess\npassword=secret\nsql=select id,title,body,updated_at from products",
  "handler_script": "url=\"https://shop.example.com/p/\" + id\nhost=\"shop.example.com\"\nsite=\"shop.example.com\"\ntitle=title\ncontent=body\ndigest=body\ncontent_length=body.length()\nlast_modified=updated_at",
  "boost": 1.0,
  "available": "true",
  "sort_order": 1,
  "description": "Product catalog from MySQL",
  "permissions": "{role}guest",
  "virtual_hosts": "",
  "created_by": "admin",
  "created_time": 1735689600000
}
```

Required on create: `name`, `handler_name`. Recommended in practice: `handler_parameter` (newline-delimited `key=value`) and `handler_script` (Groovy, also `key=value` per line). Optional with defaults: `boost` = `1.0`, `available` = `"true"`, `sort_order` = `1`, `description` = `""`, `permissions` = `"{role}guest"` (joined by newlines if multiple `--permission` flags), `virtual_hosts` = `""` (joined by newlines), `created_by` = `"admin"`, `created_time` = current epoch milliseconds. On update, `crud_mode` is set to `2`, plus `updated_by` and `updated_time`.

## Relationships

- **labeltype** — assign labels through the script or via permissions to let users filter ingested documents in the UI.
- **scheduler** — actual crawling is triggered by a scheduler job (typically the `Default Crawler` job, or a job whose script calls the data-store handler). Without an enabled scheduler job, a DataConfig is inert.
- **fess-ds-\*** plugin — non-built-in `handler_name` values require the corresponding plugin to be installed on the Fess server (see `fessctl plugin install`). The handler name in the config must match the plugin's registered name exactly.
- **JDBC driver / native libs** — `DatabaseDataStore` needs the matching JDBC `.jar` in `app/WEB-INF/lib` and a server restart to be picked up.
- **virtualhost** — controls which virtual host the produced documents are visible under.

## Gotchas

- The `handler_name` must match a class or plugin currently loaded by Fess. Mistyped names produce an error only at crawl time, not at create time.
- For databases, the JDBC driver class name varies by version. MySQL 8 uses `com.mysql.cj.jdbc.Driver`; MySQL 5.x used `com.mysql.jdbc.Driver`. PostgreSQL uses `org.postgresql.Driver`.
- `handler_parameter` and `handler_script` are newline-delimited `key=value`. Pass them as single strings with `\n` literals quoted by your shell (e.g. `--handler-parameter $'driver=...\nurl=...\n...'`).
- The script is **Groovy**. Strings need double quotes; column names from a SQL row become Groovy variables. Mismatches between SQL column names and script variables silently produce empty fields.
- Slack and similar SaaS plugins require workspace-scoped tokens (`xoxb-...`) with the right OAuth scopes. Store them in `handler_parameter` rather than committing them to source control.
- `permissions` must use the prefixes `{role}`, `{group}`, `{user}` (e.g. `{role}guest`). Bare names will not authorize anyone.
- The `available` field is sent as the string `"true"` or `"false"`, not a boolean.
- Behavior of specific `fess-ds-*` plugins is version-pinned to the Fess release. Always cross-check the plugin's README against your `FESS_VERSION`.

## Examples

```bash
# Create a JDBC datastore that crawls a products table.
fessctl dataconfig create \
  --name products-db \
  --handler-name DatabaseDataStore \
  --handler-parameter $'driver=com.mysql.cj.jdbc.Driver\nurl=jdbc:mysql://db.example.com:3306/shop?useUnicode=true&characterEncoding=UTF-8\nusername=fess\npassword=secret\nsql=select id,title,body,updated_at from products' \
  --handler-script $'url="https://shop.example.com/p/" + id\nhost="shop.example.com"\nsite="shop.example.com"\ntitle=title\ncontent=body\ndigest=body\ncontent_length=body.length()\nlast_modified=updated_at' \
  --boost 1.0 \
  --description "Product catalog from MySQL" \
  --permission '{role}guest'
```

```bash
# Toggle an existing datastore off and bump its sort order.
fessctl dataconfig update <config-id> \
  --available false \
  --sort-order 50 \
  --description "Disabled pending schema migration"
```

```bash
# List datastores and filter to those whose name starts with "slack-".
fessctl dataconfig list --size 200 --output json \
  | jq '.response.settings[] | select(.name | startswith("slack-")) | {id,name,handler_name,available}'
```

## See also

- fess-docs: en/15.6/admin/dataconfig-guide.rst
- workflows.md: n/a
- Related features: `references/features/labeltype.md`, `references/features/scheduler.md`
