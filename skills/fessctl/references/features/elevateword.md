# Elevate Word (fessctl `elevateword`)

## What it is

Elevate Words (also called "Additional Words") are operator-curated entries that are pushed into the Fess suggest dictionary so that they appear at—or near—the top of keyword autocomplete results. Normally, suggest entries are derived automatically from search queries and indexed content; elevate words let administrators inject preferred terms that may not yet have enough query/content signal to surface organically.

In the Fess Admin UI, manage these entries from **Suggest > Additional Word** (`/admin/elevateword/`). Each entry pairs a `suggest_word` with a numeric `boost`; higher boost values rank the term higher in the suggest dropdown. Entries can optionally carry a `reading` (for kana / phonetic matching), and can be scoped by labels (`target_label`, `label_type_ids`) and roles (via `permissions`).

The `fessctl elevateword` subcommand group is a thin wrapper around the admin REST API (`/api/admin/elevateword`). It supports CRUD operations and is suitable for scripted, declarative management of the elevate-word dictionary across environments.

## When to use

- Promote a brand or product name in autocomplete the moment it ships, before organic query signal exists (for example, a freshly launched SKU code).
- Ensure event names, campaign keywords, or seasonal terms surface at the top of suggestions during a marketing window.
- Guarantee that internal jargon, acronyms, or tenant-specific terminology appears for users behind a particular role or label scope.
- Bulk-seed a curated suggest dictionary as part of an environment provisioning pipeline (dev / staging / prod parity).

## Subcommand surface

| Subcommand | Purpose | Key required inputs |
|------------|---------|---------------------|
| `create` | Create a new elevate word entry. | `--suggest-word`, `--boost`, `--version-no` |
| `update` | Update an existing entry by ID; only provided fields are overwritten. | positional `config_id` (other flags optional) |
| `delete` | Delete an entry by ID. | positional `config_id` |
| `get` | Retrieve a single entry by ID. | positional `config_id` |
| `list` | List entries with paging. | `--page`, `--size` (both optional, defaults `1` / `100`) |

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
- `label_type_ids` is a list, supplied via repeated `--label-type-id` flags.
- `created_time` / `updated_time` are epoch milliseconds (UTC); the CLI defaults to "now" if omitted.

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
- **`version_no` is required on create** by this CLI even though it is conceptually optimistic-locking metadata; pass `1` for a brand-new entry.
- **`update` is a merge.** The CLI fetches the current setting first, then overlays only the flags you provided, so you do not need to resend unchanged fields.
- **Permissions format.** Use the Fess permission syntax (e.g., `{role}admin`, `{user}alice`); repeat the `--permission` flag per entry.

## Examples

Minimal create (promote `FessSearch` with boost `10.0`):

```bash
fessctl elevateword create \
  --suggest-word "FessSearch" \
  --boost 10.0 \
  --version-no 1
```

Update an existing entry to raise its boost and add a reading:

```bash
fessctl elevateword update abc123 \
  --boost 25.0 \
  --reading "fessusaachi"
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
