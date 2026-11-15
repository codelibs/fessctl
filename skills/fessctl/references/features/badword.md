# Bad Word (fessctl `badword`)

## What it is

Bad words are terms the administrator wants to suppress from the **Suggest** feature in Fess. Once registered, the term is filtered out of suggestion candidates the next time the suggest index is rebuilt or reloaded, so end users never see the term as a typeahead/autocomplete entry.

The Fess admin UI exposes this under **Suggest > Bad Word** (left sidebar). Each entry holds a single `suggest_word` value and standard audit columns (`created_by`, `created_time`, `updated_by`, `updated_time`, `version_no`). The CSV download/upload screens read and write a single-column file (see **CSV import and export**).

Note: the official documentation (`badword-guide.rst`) describes the scope strictly as "exclude it from Suggest." Bad words do **not** rewrite or block primary search results; for that, use the role/permission system or content filtering. Verify the runtime behavior of your specific Fess version before promising end users that bad words will also disappear from full-text search hits.

## When to use

- Suppress profanity or slurs from suggest output on a public-facing search portal.
- Hide internal codenames, project aliases, or unreleased product names that leaked into the suggest index from crawled documents.
- Remove personally identifying tokens (phone numbers, employee IDs) that the suggest collector picked up from logs.
- Quickly silence a trending but undesirable query term reported by support, without retraining or recrawling.

## Subcommand surface

| Subcommand | Purpose | Key arguments / options |
|---|---|---|
| `create` | Register a new bad word. | `--suggest-word` (required, no whitespace), `--created-by`, `--created-time`, `--output/-o` |
| `update` | Modify an existing bad word entry. | `config_id` (positional), `--suggest-word`, `--updated-by`, `--updated-time`, `--output/-o` |
| `delete` | Remove a bad word by ID. | `config_id` (positional), `--output/-o` |
| `get` | Show one bad word entry. | `config_id` (positional), `--output/-o` |
| `list` | Page through registered bad words. | `--page/-p` (default 1), `--size/-s` (default 100), `--output/-o` |
| `upload` | Import bad words from a CSV file. Asks for confirmation unless `--yes`. | `<file>`, `--yes/-y`, `--output/-o` |
| `download` | Write all bad words as CSV to standard output, or to `--file` (refuses to overwrite unless `--force`). | `--file/-f`, `--force`, `--output/-o` |

Always reconfirm with `fessctl badword <sub> --help`.

## Resource JSON shape

```json
{
  "id": "AYabc123XyzExample",
  "crud_mode": 1,
  "suggest_word": "example-bad-term",
  "created_by": "admin",
  "created_time": 1714694400000,
  "updated_by": "admin",
  "updated_time": 1714694400000,
  "version_no": 1
}
```

Required on create: `suggest_word` (string, no whitespace). `crud_mode` is set internally by fessctl (`1` for create, `2` for update). Timestamps are epoch milliseconds in UTC. `id` and `version_no` are managed by Fess.

## CSV import and export

`download` writes `badword.csv` as exported by Fess: UTF-8, every field in double quotes, a header line `"BadWord"`, then one word per line.

```csv
"BadWord"
"exampleterm"
"another term"
```

`upload` reads the same layout. What the server does with the file:

- **It merges; it never replaces.** A word that is not yet registered is added, a word that already exists is only touched (its updated time), and words missing from the file are kept.
- **A line starting with `--` deletes that word** (`--exampleterm`). Deleting a word that does not exist is ignored.
- **The first line is always dropped as a header**, whatever it contains. A file without a header silently loses its first word.
- Only the first column is read. Surrounding whitespace is trimmed and one pair of surrounding double quotes is removed; blank lines are skipped. Words with spaces are accepted here even though `create` rejects them.
- **The import runs in the background.** `upload` exits 0 once Fess has accepted the file; a failure in the import itself (and any row it cannot store) is only written to the Fess log. `download` or `list` a few seconds later to see the result.
- The file is read with the server's `csv.file.encoding` system property (default UTF-8) and `fessctl` sends the bytes as they are. Bytes that are not valid in that encoding are stored as replacement characters without an error; an empty file or a header-only file is accepted and changes nothing.
- Quoting is not parsed on import (but is on export), so a word containing a comma is cut at the comma, and a word containing a double quote comes back from `download` with the quote doubled: uploading that download again registers a second, different word (`a"b` becomes `a""b`).

## Relationships

- **Opposite of `elevateword`**: elevate words *boost* terms in the suggest index, while bad words *suppress* them.
- Depends on the **Suggest** subsystem being enabled (`suggest.search.log` / `suggest.documents` collectors and a populated suggest index).
- Effective only after the suggest index is rebuilt or reloaded — typically via the `SuggestIndexer` scheduler job (see `scheduler.py`) or a manual rebuild from **Suggest > Maintenance**.
- Audit fields (`created_by`, `updated_by`) are free-form strings; pair with `user`/`role` features only for traceability, not enforcement.
- Does not interact with `boostdoc`, `keymatch`, or `dict/synonym`; those operate on the search index, not the suggest index.

## Gotchas

- **Suggest reload required.** Adding or removing a bad word does not retroactively edit the live suggest index; trigger a suggest rebuild before verifying.
- **Whitespace forbidden.** The `--suggest-word` help text states "no whitespace allowed." Use a single token; multi-word phrases will be rejected or behave unexpectedly.
- **Casing and normalization.** Suggest matching applies the analyzer chain configured for the suggest index (lowercasing, ICU folding, etc.). Register the word in the form the analyzer produces, otherwise it may not match candidates.
- **Exact vs prefix.** Bad-word filtering matches the normalized token, not arbitrary substrings. A registered word will not suppress longer compound suggestions that merely contain it as a substring.
- **Search results unaffected.** End users can still type the word and retrieve full-text matches; this feature only hides typeahead suggestions.
- **`upload` is impossible on Fess 15.6 to 15.8.** Those servers route the upload only as PUT and cannot read a multipart PUT; 15.9 added POST and 14.x always used POST. `fessctl` refuses the upload there with an explanatory error; `download` works on every version.
- **Bulk delete with a CSV:** `download`, turn the lines to remove into `--word`, add a header line, and `upload`.
- **Timestamp options auto-fill to "now."** Override `--created-time` / `--updated-time` only when reproducing an exact audit trail; otherwise let fessctl populate them.

## Examples

Minimal create:

```bash
fessctl badword create --suggest-word "exampleterm"
```

Update an existing entry by ID:

```bash
fessctl badword update AYabc123XyzExample \
  --suggest-word "renamedterm" \
  --updated-by "ops-bot"
```

Export, add words and import again (the first line of the file is the header):

```bash
fessctl badword download --file badwords.csv
printf 'newterm\n--oldterm\n' >> badwords.csv
fessctl badword upload badwords.csv --yes
```

List and filter via JSON output piped through `jq` (e.g., extract just the IDs and words):

```bash
fessctl badword list --output json --size 200 \
  | jq -r '.response.settings[] | [.id, .suggest_word] | @tsv'
```

## See also

- fess-docs: en/15.6/admin/badword-guide.rst
- workflows.md: Recipe 5
- Related features: `references/features/elevateword.md`
