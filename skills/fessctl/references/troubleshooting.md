# Troubleshooting

Symptoms and recoveries for the errors fessctl users hit most often. Each section starts with what the user sees, then likely causes and fixes.

## `401 Unauthorized` / `403 Forbidden`

```
HTTP 401: Unauthorized
```

Causes:

- `FESS_ACCESS_TOKEN` is unset, mistyped, or has been deleted in the admin UI.
- The token was issued for a non-admin user; most fessctl operations require admin (`Radmin-api`) permission.
- You exported the token in one shell but are running fessctl from another shell where the env var was not inherited.

Recovery:

```bash
echo "${FESS_ACCESS_TOKEN:-UNSET}"          # 1. confirm the env var is exported
fessctl ping                                 # 2. ping does NOT need a token; if this works the endpoint is reachable
fessctl user list --size 1                   # 3. this DOES need a token
# If still 401: re-issue
fessctl accesstoken create --name claude-cli --permissions "Radmin-api"
export FESS_ACCESS_TOKEN=<new value>
```

## `404 Not Found`

```
HTTP 404: Not Found
```

Causes:

- The `--id` you passed does not exist in this Fess server (typo, copy-pasted from a different env, or the resource was deleted).
- `FESS_ENDPOINT` points at the wrong server.
- A previous `delete` ran successfully and the ID is now gone.

Recovery:

```bash
fessctl <resource> list --output json | jq '.[] | {id,name}'
```

Find the live ID, retry. Resource IDs do not survive an export/import — see `references/conventions.md`.

## `Connection refused` / DNS failure

```
httpx.ConnectError: [Errno 61] Connection refused
```

Causes:

- Fess server is not running, or is not listening on the port in `FESS_ENDPOINT`.
- You are running fessctl inside Docker but `FESS_ENDPOINT=http://localhost:8080` resolves to the *container's* loopback, not the host.
- The endpoint URL is missing the scheme (`https://...` vs `host:port`).

Recovery:

```bash
curl -fsS "${FESS_ENDPOINT}/" >/dev/null && echo OK || echo "endpoint unreachable"
```

For Docker → host:

- macOS / Windows: invoke with `--add-host=host.docker.internal:host-gateway` and set `FESS_ENDPOINT=http://host.docker.internal:8080`.
- Linux: pass `--network host` and keep `FESS_ENDPOINT=http://localhost:8080`.

## API version mismatch

Symptoms vary: missing fields, unexpected `400 Bad Request`, or `KeyError` when fessctl parses a response.

Cause: `FESS_VERSION` does not match the running server's major.minor. fessctl shapes some requests/responses by version.

Recovery:

```bash
curl -fsS "${FESS_ENDPOINT}/api/v1/health" | jq .   # find the running Fess version
export FESS_VERSION=<that version>
```

If the Fess server is newer than any version fessctl knows about, you may also need to update fessctl itself.

## SSL / certificate errors

```
ssl.SSLCertVerificationError: certificate verify failed
```

Cause: Fess is fronted by HTTPS with a self-signed or internal-CA certificate, and the OS / Python trust store does not include that CA.

Recovery: fessctl uses `httpx` with the system trust store (no dedicated `FESS_VERIFY_SSL` env var exists in v0.1.0 — see `src/fessctl/api/client.py`). The pragmatic fixes are:

- Add the issuing CA to the system trust store (`/etc/ssl/certs`, macOS Keychain, Windows certificate manager).
- For local dev only, terminate TLS at a reverse proxy and point fessctl at the plain-HTTP backend.

Do not edit fessctl source to disable verification. If you genuinely need to, raise an issue upstream rather than carrying a local patch.

## Empty `list` results when data should exist

Causes:

- `--page` advanced past the last page.
- A filter combination upstream of fessctl (e.g. shell quoting issues) is hiding rows.

Recovery:

```bash
fessctl <resource> list --page 1 --size 100 --output json | jq 'length'
```

If `length` is 0, the resource really is empty in this environment. Confirm you are pointed at the right `FESS_ENDPOINT`.

## `uv run fessctl` slow on the first invocation

Cause: cold virtualenv build inside `repos/fessctl/.venv`.

Recovery: run `uv sync` once up front in `repos/fessctl`. Subsequent `uv run fessctl ...` calls reuse the cached environment and start in well under a second.

## Docker pull or auth errors against `ghcr.io`

```
denied: requested access to the resource is denied
```

Causes:

- Rate limiting from anonymous pulls.
- Pulling from a private mirror without prior `docker login`.

Recovery:

```bash
docker login ghcr.io                         # if behind auth
docker pull ghcr.io/codelibs/fessctl:0.1.0   # pin a specific tag, not `latest`
```

If `latest` is unavailable in your environment, prefer a pinned version tag matching `FESS_VERSION`.
