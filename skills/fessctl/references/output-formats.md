# Output formats

Every fessctl subcommand that returns data accepts `--output` (or `-o`) to choose between three serializations.

## Available formats

| Format     | Best for | Notes |
|------------|----------|-------|
| `markdown` | Reading in chat or a terminal | Human-friendly tables and headings. **Do not parse it programmatically — column layout is presentational and may change between releases.** |
| `json`     | Piping to `jq`, scripting     | Stable, machine-readable. Top-level shape is `{"success": ..., "data": ...}` for action results and an array for `list`. Always start here when chaining commands. |
| `yaml`     | Hand-editing, version control diffs | Useful for capturing settings to a file you intend to read or edit by eye. |

The exact set of supported values is implemented in `src/fessctl/utils.py`; if you see a format mentioned in `--help` that is not listed here, prefer `--help` as the source of truth.

## When to use which

- **Asking Claude to summarize a list of resources** → `markdown` (concise to read).
- **Filtering a list before acting** → `json | jq`.
- **Saving config for review or backup** → `yaml`.
- **Anything that another shell command will consume** → `json` and never `markdown`.

## Idiomatic pipelines

```bash
# 1. List then filter to high-boost crawl configs
fessctl webconfig list --output json | jq '.[] | select(.boost > 1.0)'

# 2. Extract one field across many rows
fessctl user list --output json | jq -r '.[].name'

# 3. Capture config to YAML for review
fessctl webconfig get --id <id> --output yaml > webconfig-snapshot.yaml

# 4. Save a list as a baseline for diffing later
fessctl scheduler list --output json > scheduler-before.json
# ... make changes ...
fessctl scheduler list --output json > scheduler-after.json
diff <(jq -S . scheduler-before.json) <(jq -S . scheduler-after.json)

# 5. Bulk delete by filter
fessctl badword list --output json \
  | jq -r '.[] | select(.suggest_word | test("^_test")) | .id' \
  | xargs -I{} fessctl badword delete --id {}
```

`fessctl` does not currently accept a `--from-file` style input flag (verified in `src/fessctl/commands/`). To re-create a resource from a captured YAML, read it back yourself and re-issue `create`/`update` with the appropriate flags — for example:

```bash
yq '.data | "--name=" + .name + " --url=" + .urls' webconfig-snapshot.yaml
```

Then call `fessctl webconfig create` with those flags. If you need true round-trip restore, use multiple commands; do not assume a single-flag import path exists.

## Caveats

- `markdown` output is rendered for humans only. Scripts that grep markdown will break the next time the table layout shifts.
- `json` field names track the Fess admin API directly, so they may differ subtly between Fess versions. Pin `FESS_VERSION` and rerun if you see unexpected keys.
- `yaml` output preserves nesting from the underlying API but does not include comments. If you serialize and then re-import, expect identifier and timestamp fields to need stripping.
