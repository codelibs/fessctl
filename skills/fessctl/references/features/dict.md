# Dictionaries (fessctl `dict`)

## What it is
Fess keeps its analyzer dictionaries as text files in the search engine's dictionary directory: synonyms, character mappings, Japanese (kuromoji) user words, stop words, protected words and stemmer overrides. The Admin UI edits them under **System → Dictionary**; the admin API lists the files and manages both their entries and the whole file.

`fessctl dict list` shows the files (`type`, `id`, `path`, `timestamp`). Every other command is `fessctl dict <type> <sub> <dict_id> ...`, where `<dict_id>` is the `id` from `dict list` (a URL-safe base64 of the path, e.g. `c3lub255bS50eHQ=` for `synonym.txt`). Which files exist depends on the search engine image; most languages have `stopwords`/`protwords`/`stemmeroverride` files, `ja` has `kuromoji` and `mapping`, and there is one `synonym.txt`.

Available in all supported versions (14.19.2, 15.6.1, 15.7.0, 15.8.0, 15.9.0) with the same fields, except for `upload` (see Gotchas).

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `dict list` | List the dictionary files; `--type` narrows to one type. | none |
| `dict <type> list` | Page through the entries of one file (`--page`, `--size`). | `<dict_id>` |
| `dict <type> get` | Show one entry. | `<dict_id> <item_id>` |
| `dict <type> create` | Add an entry. | `<dict_id>` and every field option of the type |
| `dict <type> update` | Change an entry; unspecified fields are kept. | `<dict_id> <item_id>` |
| `dict <type> delete` | Delete one entry. | `<dict_id> <item_id>` |
| `dict <type> upload` | Replace the whole file with a local file. Asks for confirmation unless `--yes`. | `<dict_id> <file>` |
| `dict <type> download` | Write the file to standard output, or to `--file` (refuses to overwrite unless `--force`). | `<dict_id>` |

Always reconfirm with `fessctl dict <type> <sub> --help`.

## Types and their fields
| `<type>` | Options of `create` / `update` | API fields |
| --- | --- | --- |
| `synonym` | `--source` (repeatable), `--target` (repeatable) | `inputs`, `outputs` |
| `mapping` | `--source` (repeatable), `--target` | `inputs`, `output` |
| `kuromoji` | `--token`, `--segmentation`, `--reading`, `--pos` | same names |
| `stopwords` | `--word` | `input` |
| `protwords` | `--word` | `input` |
| `stemmeroverride` | `--source`, `--target` | `input`, `output` |

A repeatable option is sent as one value per line (`inputs` is `"a\nb"`).

## Resource JSON shape
`list` returns the entries under `response.settings`, `get` returns one under `response.setting`:
```json
{"id": 2, "dict_id": "c3lub255bS50eHQ=", "inputs": "tv\ntelevision", "outputs": "tv"}
```
`dict list` returns `{"id": "c3lub255bS50eHQ=", "type": "synonym", "path": "synonym.txt", "timestamp": "2026-10-16T12:24:48"}` rows.

## Gotchas
- **`upload` is impossible on Fess 15.6 to 15.8.** Those servers route the upload only as PUT and cannot read a multipart PUT (the error is "File is required"); 15.9 added POST, and 14.x always used POST. `fessctl` therefore refuses an upload on 15.6 to 15.8 with an explanatory error. Use `download`, edit, and the Admin UI there.
- `upload` replaces the whole file, including entries added with `create`; `download` first when unsure. The file is in the engine's plain-text dictionary format; `download` one to see it (a synonym rule is a line such as `a,b=>c,d`).
- Entry IDs are positions in the file. Deleting an entry can shift the IDs of the ones after it, and a new entry may reuse an ID, so look an entry up again (by its content) before updating or deleting it after any change.
- Fess before 15.9 reports the ID of a new entry as `0`; `create` then prints no ID. Find it with `list`.
- `update` reads the entry first and sends it back with only the given options changed (the API's PUT replaces the whole entry). A repeatable option such as `--target` replaces all the values; it does not append.
- `list` and `get` of an unknown `<dict_id>`: `list` shows nothing (exit 0), `get` fails. `create` in an unknown dictionary fails on 15.9 but reports success without storing anything on earlier versions.
- Fess validates entries: synonym and mapping sources may not contain `,` or `=>` (15.9), a mapping source may not already exist, a kuromoji token may be registered once, and the number of words in `--segmentation` and `--reading` must match.
- Error messages of `download` and `upload` on a bad `<dict_id>` mention "protwords" for every type; that is the server's wording.

## Examples
```bash
fessctl dict list --type synonym
fessctl dict synonym create c3lub255bS50eHQ= --source tv --source television --target tv
fessctl dict synonym list c3lub255bS50eHQ=
fessctl dict synonym update c3lub255bS50eHQ= 2 --target "tv set"
fessctl dict synonym delete c3lub255bS50eHQ= 2

fessctl dict kuromoji create amEva3Vyb21vamkudHh0 \
  --token 令和 --segmentation 令和 --reading レイワ --pos 名詞-固有名詞-一般

fessctl dict stopwords download ZW4vc3RvcHdvcmRzLnR4dA== --file stopwords.txt
fessctl dict stopwords upload ZW4vc3RvcHdvcmRzLnR4dA== stopwords.txt --yes
```
