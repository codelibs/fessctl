# Output formats

Every fessctl subcommand that returns data accepts `--output` (or `-o`) to choose between three serializations. The default value is `text` (markdown).

## Available formats

| Format     | Best for | Notes |
|------------|----------|-------|
| `text` (default) | Reading in chat or a terminal | Markdown tables and headings, AI/human friendly. **Do not parse it programmatically — column layout is presentational and may change between releases.** |
| `json`     | Piping to `jq`, scripting     | Stable, machine-readable. Returns the **raw Fess admin API response** as-is — top-level shape is `{"response": { ... }}`. See "JSON shape" below for the keys you will actually navigate. |
| `yaml`     | Hand-editing, version control diffs | Same content as `json`, just YAML-encoded. Useful for capturing settings to a file you intend to read or edit by eye. |

The implementation lives in `src/fessctl/utils.py`; if `--help` lists a format not shown here, prefer `--help` as the source of truth.

## JSON shape

`fessctl --output json` echoes the upstream Fess admin API payload verbatim, so jq paths must navigate through `.response`. The relevant keys vary by verb:

| Verb              | jq path to the data                       |
|-------------------|-------------------------------------------|
| `list`            | `.response.settings[]` (one per row)      |
| `get`             | `.response.setting`                       |
| `create` / `update` | `.response.id` (the new/affected ID), plus `.response.status` (0 = success) |
| `delete`          | `.response.status` (0 = success)          |
| `joblog list`     | `.response.logs[]`                        |
| `joblog get`      | `.response.log`                           |
| `crawlinginfo list` | `.response.logs[]`                      |
| `crawlinginfo get`  | `.response.log`                         |

Status codes other than 0 indicate an error; the message is at `.response.message`.

## When to use which

- **Asking Claude to summarize a list of resources** → `text` (concise markdown).
- **Filtering a list before acting** → `json | jq`.
- **Saving config for review or backup** → `yaml`.
- **Anything that another shell command will consume** → `json`, never `text`.

## Identifying resources on the command line

Resource IDs are passed as **positional arguments**, not as `--id`:

```bash
fessctl webconfig get <CONFIG_ID>
fessctl badword delete <BADWORD_ID>
fessctl user get <USER_ID>
```

Discover IDs with `list --output json | jq '.response.settings[].id'` (or `.logs[].id` for joblog/crawlinginfo).

## Idiomatic pipelines

```bash
# 1. List then filter to high-boost crawl configs
fessctl webconfig list --output json \
  | jq '.response.settings[] | select(.boost > 1.0)'

# 2. Extract one field across many rows
fessctl user list --output json \
  | jq -r '.response.settings[].name'

# 3. Capture one config to YAML for review
fessctl webconfig get <CONFIG_ID> --output yaml > webconfig-snapshot.yaml

# 4. Save a list as a baseline for diffing later
fessctl scheduler list --output json > scheduler-before.json
# ... make changes ...
fessctl scheduler list --output json > scheduler-after.json
diff <(jq -S '.response.settings' scheduler-before.json) \
     <(jq -S '.response.settings' scheduler-after.json)

# 5. Bulk delete by filter
fessctl badword list --output json \
  | jq -r '.response.settings[] | select(.suggest_word | test("^_test")) | .id' \
  | xargs -I{} fessctl badword delete {}
```

`fessctl` does not provide a `--from-file` import flag (verified in `src/fessctl/commands/`). To re-create a resource from a captured YAML, parse the file yourself and reissue `create`/`update` with explicit flags. The captured YAML's payload is at `.response.setting`:

```bash
yq '.response.setting | "--name " + .name + " --url " + .urls' webconfig-snapshot.yaml
# Then feed those flags into a fresh `fessctl webconfig create ...` invocation.
```

Round-trip restore requires composing several commands; do not assume a single-flag import path exists.

## Caveats

- `text` output is rendered for humans only. Scripts that grep markdown will break the next time the table layout shifts.
- `json` field names track the Fess admin API directly, so they may differ subtly between Fess versions. Pin `FESS_VERSION` and rerun if you see unexpected keys.
- `yaml` output preserves nesting from the underlying API but does not include comments. If you serialize and then re-import, expect identifier and timestamp fields to need stripping.
