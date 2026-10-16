# System info (fessctl `systeminfo`)

## What it is
The system information of the running Fess server, the data of the Admin UI system information page: the properties to attach to a bug report, the environment variables, the `fess_config.properties` values in effect, and the JVM system properties.

Read only. Available in every version fessctl supports (14.19.2, 15.6.1, 15.7.0, 15.8.0, 15.9.0).

## When to use
- Attach the server environment to a bug report or support request.
- Check which configuration value Fess is really using (`fess_props`) or which environment variable reached the JVM (`env_props`).

## Subcommand surface
`systeminfo` takes no subcommand; it takes `--output text|json|yaml`.

| Command | Purpose |
| --- | --- |
| `fessctl systeminfo` | Show the four property groups. Text output is one `NAME \| VALUE` table per group (the Fess group alone has several hundred rows); `json`/`yaml` return the full response. |

Always reconfirm with `fessctl systeminfo --help`.

## Resource JSON shape
```json
{
  "response": {
    "status": 0,
    "version": "15.9",
    "bug_report_props": [{"label": "java.runtime.version", "value": "21.0.12.1+1-LTS"}],
    "env_props": [{"label": "FESS_PORT", "value": "8080"}],
    "fess_props": [{"label": "domain.title", "value": "Fess"}],
    "system_props": [{"label": "java.specification.version", "value": "21"}]
  }
}
```

## Gotchas
- The output includes environment variables and configuration values of the server; review it before pasting it into a public issue.
- Use `--output json` with `jq` to pick one value: `fessctl systeminfo -o json | jq -r '.response.fess_props[] | select(.label == "domain.title") | .value'`.

## Examples
```bash
fessctl systeminfo
fessctl systeminfo --output yaml
fessctl systeminfo -o json | jq -r '.response.bug_report_props[] | "\(.label)=\(.value)"'
```
