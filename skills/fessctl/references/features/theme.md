# Themes (fessctl `theme`)

## What it is
A theme is a static search UI published as a Maven artifact (for example `filesearch`, `docsearch`, `codesearch`). The Admin UI installs them from the theme page; the admin API lets you list the themes available for this Fess line and install one.

Requires a Fess version that provides `/api/admin/theme` (Fess 15.9.0 and later; absent from earlier versions).

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `available` | List installable `name`/`version` pairs for this Fess line. | none |
| `install` | Download and install one theme. | `<name> <version>` |

Always reconfirm with `fessctl theme <sub> --help`.

## Resource JSON shape
```json
{
  "response": {
    "status": 0,
    "themes": [
      {"name": "filesearch", "version": "15.9.4"},
      {"name": "docsearch", "version": "15.9.11"}
    ]
  }
}
```

## Gotchas
- `install` makes the Fess server download the theme from the theme repository, so the server needs outbound access to it.
- A theme that does not exist or is not compatible with the running Fess fails with an error message and a non-zero exit code.
- `available` can list many versions of the same theme; pick the newest for your Fess line.
- There is no `uninstall` in the admin API.

## Examples
```bash
fessctl theme available --output json | jq -r '.response.themes[] | select(.name == "filesearch") | .version'
fessctl theme install filesearch 15.9.4
```
