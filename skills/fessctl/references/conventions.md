# fessctl conventions

Patterns that hold across most fessctl subcommands. Each per-feature reference notes deviations.

## CRUD verb pattern

Every resource type exposes a uniform set of verbs:

```
fessctl <resource> list      # paginated list
fessctl <resource> get       # one resource by --id
fessctl <resource> create    # new resource, fields via flags
fessctl <resource> update    # mutate one resource by --id
fessctl <resource> delete    # remove one resource by --id
```

Exceptions:

- **`crawlinginfo`** is effectively read-only history: it exposes only `list`, `get`, `delete`. There is no `create` or `update`. Verify with `grep '@crawlinginfo_app.command' src/fessctl/commands/crawlinginfo.py` if in doubt.
- The top-level `fessctl ping` is not part of any resource group; it is the smoke test for endpoint reachability.

When in doubt, run `fessctl <resource> --help` to see the verbs offered for a particular resource, then `fessctl <resource> <verb> --help` for the flag list.

## Identifiers

Most resources use opaque Fess-internal IDs (e.g. ULID-like strings). Treat them as opaque — they are not URLs, not human-readable, and may differ between environments after an export/import.

- `get`, `update`, `delete` always require `--id`.
- IDs are discovered via `list`. The `id` field is included in `list --output json` output.
- Do not hard-code IDs across environments. After importing settings into a new Fess server, IDs will be regenerated.

## Pagination

`list` is paginated with two flags (verified in `webconfig.py`):

| Flag | Default | Notes |
|------|---------|-------|
| `--page` / `-p` | `1` | 1-indexed page number. |
| `--size` / `-s` | `100` | Page size. |

A single `list` call returns one page. To enumerate all rows, increment `--page` until an empty page is returned. There is no `--all` shortcut at v0.1.0.

## Required vs optional fields

Fields are exposed as Typer options. Required fields are marked with `...` (Typer's required sentinel) in the source; running `fessctl <resource> <verb> --help` shows them with no default value, while optional fields show their default. The most reliable check is always `--help`. Do not infer requiredness from the JSON shape alone — Fess server-side validation is stricter than what fessctl encodes.

## Idempotency

`create` is **not** idempotent. Re-running a `create` with the same logical name will produce a duplicate row. Patterns to emulate upsert:

```bash
# Look up first, decide to create or update
existing_id=$(fessctl webconfig list --output json | jq -r '.[] | select(.name=="foo") | .id')
if [[ -z "$existing_id" ]]; then
  fessctl webconfig create --name foo ...
else
  fessctl webconfig update --id "$existing_id" ...
fi
```

`delete` is idempotent in spirit (deleting a missing ID yields a 404, but the end state is the same).

## Bulk operations

fessctl does not provide native bulk verbs. Compose with shell:

```bash
fessctl badword list --output json \
  | jq -r '.[].id' \
  | xargs -I{} fessctl badword delete --id {}
```

When deleting in bulk, capture a backup first (`fessctl <resource> list --output yaml > before.yaml`) so the operation is reversible.

## Cross-resource dependencies

A high-level dependency map (each per-feature file restates the relevant edges):

- `webconfig` → references `labeltype`, `webauth` by ID/name.
- `fileconfig` → references `labeltype`, `fileauth`.
- `dataconfig` → references `labeltype`.
- `scheduler` → triggers a `webconfig` / `fileconfig` / `dataconfig` crawl; produces `joblog` rows; populates `crawlinginfo` history.
- `user` → references `role`, `group`.
- `keymatch`, `boostdoc`, `elevateword`, `badword`, `relatedcontent`, `relatedquery` → tune search-time behavior; depend on indexed documents existing.
- `accesstoken` → grants permissions for fessctl itself; deleting your own active token logs you out.

When deleting, work outward from leaves: delete `user`s before the `role`s they reference, delete `webconfig`s before the `labeltype`s they cite (or accept that Fess will tolerate dangling references but log warnings).
