# Plugins (fessctl `plugin`)

## What it is
Plugins are jars (data stores, ingest, script engines, web apps, thumbnail generators, crawlers, LLM clients, and from 15.9 object storage and SSO) that Fess downloads from its plugin repositories into `WEB-INF/plugin`. The Admin UI manages them under **System → Plugin**.

Available in every supported Fess version (14.19.2, 15.6.1, 15.7.0, 15.8.0, 15.9.0). Install is `PUT` on 14.x and `POST` on 15.x; fessctl picks the method. The versions on offer follow the Fess line (for example `15.9.0` plugins on Fess 15.9.0).

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `installed` | List the installed plugins. | none |
| `available` | List what the plugin repositories offer. | none |
| `install` | Ask Fess to download and install one plugin. | `<name> <version>` |
| `uninstall` | Ask Fess to delete one plugin jar. Asks for confirmation unless `--yes` is given. | `<name> <version>` |

Always reconfirm with `fessctl plugin <sub> --help`.

## Resource JSON shape
```json
{
  "response": {
    "plugins": [
      {"name": "fess-ds-csv", "id": "fess-ds-csv:15.9.0", "type": "fess-ds", "version": "15.9.0",
       "url": "https://maven.codelibs.org/release/org/codelibs/fess/fess-ds-csv/15.9.0/fess-ds-csv-15.9.0.jar"}
    ],
    "status": 0
  }
}
```
`installed` entries have no `url`.

## Gotchas
- `install` and `uninstall` only report that the request was accepted: Fess downloads or deletes the jar in a background thread and logs any failure instead of reporting it. Check `plugin installed` afterwards (it can take a few seconds), and a plugin that is not installed can still be "uninstalled" successfully.
- A new plugin is active only after Fess is restarted; so is the removal of one.
- `install` makes the Fess server download the jar, so the server needs outbound access to the plugin repository. A name/version pair that is not in `available` is rejected with `invalid name or version`.
- Installing a plugin also deletes other installed versions of the same plugin.
- `uninstall` needs the exact installed version; check `plugin installed`.

## Examples
```bash
fessctl plugin available --output json | jq -r '.response.plugins[] | select(.type == "fess-ds") | .id'
fessctl plugin install fess-ds-csv 15.9.0
fessctl plugin installed
fessctl plugin uninstall fess-ds-csv 15.9.0 --yes
```
