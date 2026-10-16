# General settings (fessctl `general`)

## What it is
The General page of the Admin UI (**System → General**): crawl and purge defaults, search-log and user-info switches, LDAP, notification text, log levels, object-storage connection, RAG chat and the SSO provider settings (OpenID Connect, SAML, SPNEGO, Entra ID). The admin API exposes the whole page as one flat object of snake_case keys.

Available in every supported Fess version (14.19.2, 15.6.1, 15.7.0, 15.8.0, 15.9.0). The set of keys grows with the version (`get` returned 37 keys on 14.19.2, 100 on 15.8.0 and 102 on 15.9.0; six LDAP keys are left out while unset); `get` shows exactly what the server under test has. Update is `POST` on 14.x and `PUT` on 15.x; fessctl picks the method.

## Subcommand surface
| Subcommand | Purpose | Required arguments |
| --- | --- | --- |
| `get` | Show every setting. | none |
| `update` | Change settings; every setting not given keeps its value. | one or more `--set KEY=VALUE` |

Always reconfirm with `fessctl general <sub> --help`.

## How update works
`update` first reads the current settings, then sends the four fields the server requires on every request (`day_for_cleanup`, `crawling_thread_count`, `failure_count_threshold`, `csv_file_encoding`, with their current values) plus only the keys given with `--set`. The server merges the request into the stored settings (a key that is absent or null keeps its value), so a one-key change leaves all other settings as they were; read back with `get` they are identical.

- `KEY` must be a name `get` shows (the LDAP keys `ldap_provider_url`, `ldap_security_principal`, `ldap_admin_security_principal`, `ldap_admin_security_credentials`, `ldap_base_dn`, `ldap_account_filter` are left out of `get` while unset but can be set). An unknown key is rejected locally, because the server would accept it and ignore it silently.
- A setting that is an integer in `get` takes an integer; checkbox-like settings are the strings `true` / `false`.
- The value after the first `=` is taken literally, so it may contain `=`.

## Resource JSON shape
```json
{
  "response": {
    "setting": {
      "day_for_cleanup": 3,
      "crawling_thread_count": 5,
      "failure_count_threshold": -1,
      "csv_file_encoding": "UTF-8",
      "login_required": "false",
      "purge_job_log_day": -1,
      "storage_secret_key": "**********"
    },
    "version": "15.9",
    "status": 0
  }
}
```

## Gotchas
- Secrets (`storage_access_key`, `storage_secret_key`, `oic_client_id`, `oic_client_secret`, `entraid_client_id`, `entraid_client_secret`, `spnego_preauth_password`) are masked as `**********` by `get` (`ldap_admin_security_credentials` is never returned at all) and are never sent back by `update`. A new value replaces the secret; a value made only of `*` is ignored by the server. A secret cannot be cleared through the API (an empty value is ignored); the exception is `spnego_preauth_password`, where an empty value removes it.
- There is no way to remove a key: an empty value (`--set key=`) stores an empty string. For the unset LDAP keys that turns "absent" into "empty". This differs from the Admin UI, where a blank field removes the system property.
- Bad values are rejected by the server with a message and a non-zero exit (for example `day_for_cleanup` above 1000, or from 15.8 on `spnego_prompt_ntlm=true` together with `spnego_allow_basic=false` when `sso_type=spnego`); nothing is changed in that case.

## Examples
```bash
fessctl general get
fessctl general get --output json | jq -r '.response.setting.crawling_user_agent'
fessctl general update --set purge_job_log_day=30 --set notification_login="Maintenance tonight"
fessctl general update --set storage_endpoint=http://s3.example.com:4566 --set storage_access_key=KEY --set storage_secret_key=SECRET --set storage_bucket=fess
```
