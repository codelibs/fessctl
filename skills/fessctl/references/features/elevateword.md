# Elevate Word (fessctl `elevateword`)

## What it is

Elevate Words (also called "Additional Words") are operator-curated entries that are pushed into the Fess suggest dictionary so that they appear at—or near—the top of keyword autocomplete results. Normally, suggest entries are derived automatically from search queries and indexed content; elevate words let administrators inject preferred terms that may not yet have enough query/content signal to surface organically.

In the Fess Admin UI, manage these entries from **Suggest > Additional Word** (`/admin/elevateword/`). Each entry pairs a `suggest_word` with a numeric `boost`; higher boost values rank the term higher in the suggest dropdown. Entries can optionally carry a `reading` (for kana / phonetic matching), and can be scoped by labels (`target_label`, `label_type_ids`) and roles (via `permissions`).

The `fessctl elevateword` subcommand group is a thin wrapper around the admin REST API (`/api/admin/elevateword`). It supports CRUD operations plus CSV import and export, and is suitable for scripted, declarative management of the elevate-word dictionary across environments.

## When to use

- Promote a brand or product name in autocomplete the moment it ships, before organic query signal exists (for example, a freshly launched SKU code).
- Ensure event names, campaign keywords, or seasonal terms surface at the top of suggestions during a marketing window.
- Guarantee that internal jargon, acronyms, or tenant-specific terminology appears for users behind a particular role or label scope.
- Bulk-seed a curated suggest dictionary as part of an environment provisioning pipeline (dev / staging / prod parity).

## Subcommand surface

| Subcommand | Purpose | Key required inputs |
|------------|---------|---------------------|
| `create` | Create a new elevate word entry. | `--suggest-word`, `--boost` |
| `update` | Update an existing entry by ID; only provided fields are overwritten. | positional `config_id` (other flags optional) |
| `delete` | Delete an entry by ID. | positional `config_id` |
| `get` | Retrieve a single entry by ID. | positional `config_id` |
| `list` | List entries with paging. | `--page`, `--size` (both optional, defaults `1` / `100`) |
| `upload` | Import elevate words from a CSV file. Asks for confirmation unless `--yes`. | `<file>`, `--yes/-y` |
| `download` | Write all elevate words as CSV to standard output, or to `--file` (refuses to overwrite unless `--force`). | `--file/-f`, `--force` |

All commands accept `--output / -o` with `text` (default), `json`, or `yaml`. Always reconfirm with `fessctl elevateword <sub> --help`.

## Resource JSON shape

The payload sent to the admin API (and returned in `response.setting`) follows this shape. `suggest_word` and `boost` are required; the rest are optional or system-managed.

```json
{
  "id": "abc123",
  "crud_mode": 1,
  "suggest_word": "FessSearch",
  "reading": "fessusaachi",
  "boost": 10.0,
  "target_label": "product",
  "label_type_ids": ["lbl-001", "lbl-002"],
  "permissions": "{role}admin\n{role}guest",
  "version_no": 1,
  "created_by": "admin",
  "created_time": 1714694400000,
  "updated_by": "admin",
  "updated_time": 1714694400000
}
```

Notes verified against `commands/elevateword.py`:

- `permissions` is sent as a newline-joined string (the CLI joins repeated `--permission` flags with `\n`).
- `label_type_ids` is a list, supplied via repeated `--label-type-id` flags. It is stored and returned by `get`, but `list` shows it empty.
- `--target-label` is accepted but the server does not return it: `get` shows `target_label` as `-`.
- `created_time` / `updated_time` are epoch milliseconds (UTC); the CLI defaults to "now" if omitted.

## CSV import and export

`download` writes `elevate.csv` as exported by Fess: UTF-8, every field in double quotes, five columns, one entry per line.

```csv
"SuggestWord","Reading","Permissions","Labels","Boost"
"FessSearch","fessusaachi","{role}admin,{role}guest","product","10.0"
```

`Permissions` and `Labels` hold comma-separated values (permissions in the `{role}name` syntax, labels as the label type `value`). `upload` reads the same layout:

- **It merges; it never replaces.** Entries missing from the file are kept. A word that does not exist yet is added (an empty `Boost` means `1.0`).
- **An existing word with an empty `Reading` and an empty `Boost` is deleted.** A file with only a `SuggestWord` column therefore adds new words on the first upload and deletes them on the second.
  Fess removes the entry but leaves the word in the suggest index's own elevate list, so a later `suggest delete-all` (or a suggest rebuild) brings it back into the suggestions; delete words with `elevateword delete` when that matters.
- Any other row for an existing word overwrites its `Reading`, `Permissions` and `Boost` (an empty `Permissions` clears them). A row is matched by word, and by permissions as well when it has some, so one word can exist once per permission set; a row without permissions that matches several entries is skipped.
- **`Labels` are only ever added**: a label the entry lacks is attached, none is removed, and a label that does not exist is ignored.
- **The first line is always dropped as a header**, whatever it contains. A file without a header silently loses its first entry.
- **The import runs in the background.** `upload` exits 0 once Fess has accepted the file; a row it cannot store (for example a `Boost` that is not a number) is skipped with only a log entry in Fess, and the other rows are still imported. `download` or `list` a few seconds later to see the result.
- Encoding is the server's `csv.file.encoding` system property (default UTF-8); `fessctl` sends the bytes as they are, and bytes invalid in that encoding are stored as replacement characters. Standard CSV quoting is understood (`"a,b"`, `""` for a quote), so a download can be uploaded again unchanged.

## Relationships

- Entries are populated into the **suggest index** used by the suggest API and the autocomplete dropdown in the search UI.
- Depends on the **suggest feature being enabled** in `fess_config.properties` (`suggest.search.log`, `suggest.document.contents`, etc.).
- After create / update / delete, a **suggest reload / rebuild** is required for the new word to appear in autocomplete (verify via the Suggest admin page or the relevant scheduler job).
- Label scoping interacts with `labeltype` configurations; role scoping interacts with `role` and `group` definitions.
- Related curation features: **Bad Word** (suppresses suggestions) and **Key Match** (boosts whole search results, not just suggestions).

## Gotchas

- **Suggest reload required.** Creating an elevate word does not immediately rewrite the live suggest index; trigger a suggest update (admin UI button or the suggest indexer job) before validating.
- **`reading` vs surface form.** `suggest_word` is what users see; `reading` is used to match typed input (e.g., kana for Japanese). Omitting `reading` for non-ASCII terms can hurt matchability.
- **Label / role scoping is restrictive.** If `target_label` or `permissions` are set, the word only surfaces for users whose context matches; an empty scope means "visible to all".
- **Casing and tokenization** depend on the suggest analyzer; the literal `suggest_word` may be lowercased or otherwise normalized at index time.
- **`--version-no` is optional on create** (default `0`; Fess ignores it); the server manages `version_no`.
- **`update` is a merge.** The CLI fetches the current setting first, then overlays only the flags you provided, so you do not need to resend unchanged fields.
- **`upload` is impossible on Fess 15.6 to 15.8.** Those servers route the upload only as PUT and cannot read a multipart PUT; 15.9 added POST and 14.x always used POST. `fessctl` refuses the upload there with an explanatory error; `download` works on every version.
- **Permissions format.** Use the Fess permission syntax (e.g., `{role}admin`, `{user}alice`); repeat the `--permission` flag per entry.

## Examples

Minimal create (promote `FessSearch` with boost `10.0`):

```bash
fessctl elevateword create \
  --suggest-word "FessSearch" \
  --boost 10.0
```

Update an existing entry to raise its boost and add a reading:

```bash
fessctl elevateword update abc123 \
  --boost 25.0 \
  --reading "fessusaachi"
```

Export, add an entry and import again (the first line of the file is the header):

```bash
fessctl elevateword download --file elevate.csv
echo '"NewTerm","nyuutaamu","","","3"' >> elevate.csv
fessctl elevateword upload elevate.csv --yes
```

List all elevate words and filter via `jq` (machine-readable output):

```bash
fessctl elevateword list --output json \
  | jq '.response.settings[] | select(.boost >= 10) | {id, suggest_word, boost}'
```

## See also

- fess-docs: en/15.6/admin/elevateword-guide.rst
- workflows.md: Recipe 5
- Related features: `references/features/badword.md`, `references/features/keymatch.md`
