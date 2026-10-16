# Suggest words (fessctl `suggest`)

## What it is
The suggest index holds the words behind the search box auto-complete. Fess fills it from two sources: the content of crawled documents (document words) and the queries users searched for (query words). The Admin UI Suggest page shows the counts and offers the deletes; the admin API offers the same.

Available in every version fessctl supports (14.19.2, 15.6.1, 15.7.0, 15.8.0, 15.9.0).

## When to use
- Check whether suggestions exist (`info`): the counts are 0 until the **Suggest Indexer** scheduler job has run.
- Remove words after a change in the crawl targets, or remove query words that should not be suggested.

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `info` | Show `total_words_num`, `document_words_num` and `query_words_num`. | none |
| `delete-all` | Delete every word. Fess re-adds the elevate words afterwards. Asks for confirmation unless `--yes` is given. | none |
| `delete-document` | Delete the words that come from documents. Asks for confirmation unless `--yes` is given. | none |
| `delete-query` | Delete the words that come from search queries. Asks for confirmation unless `--yes` is given. | none |

Always reconfirm with `fessctl suggest <sub> --help`.

## Resource JSON shape
```json
{
  "response": {
    "status": 0,
    "setting": {"total_words_num": 17, "document_words_num": 17, "query_words_num": 4}
  }
}
```
The delete commands return only `status` (and `version`).

## Gotchas
- A word can come from both sources, so `document_words_num` plus `query_words_num` can exceed `total_words_num`; `delete-document` removes the document origin of such a word and `delete-query` the query origin.
- Deleted words come back: the **Suggest Indexer** job (`fessctl scheduler start suggest_indexer`) re-creates the document words from the index and the query words from the search log.
- The counts are read from the search engine and can lag a moment behind an index run.
- None of these APIs needs the CodeLibs search engine plugins (the 15.9 `404` for plugin-less engines applies to the dictionary APIs only).

## Examples
```bash
fessctl suggest info
fessctl suggest delete-query --yes
fessctl suggest delete-all --yes --output json
fessctl scheduler start suggest_indexer
```
