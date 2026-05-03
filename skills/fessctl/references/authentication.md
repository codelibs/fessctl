# Authenticating with Fess

Every fessctl call other than `ping` is authenticated with a Fess access token sent as a Bearer header. This file covers the three required environment variables, how to issue a token, where to keep it, and how to verify the wiring.

## Required environment variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `FESS_ENDPOINT`     | optional | `http://localhost:8080`    | Base URL of the target Fess server. Include scheme; do not include a trailing `/`. |
| `FESS_ACCESS_TOKEN` | **yes** for any non-`ping` call | none | Bearer token issued from the Fess admin UI or via `fessctl accesstoken create`. |
| `FESS_VERSION`      | optional | `15.4.0` (as of fessctl 0.1.0) | Must match the major.minor of the target Fess server so request shapes line up. Set it explicitly — do not rely on the default. |

Defaults live in `src/fessctl/config/settings.py`. The defaults are conservative and may lag the latest Fess release; for any non-trivial work, set `FESS_ENDPOINT` and `FESS_VERSION` explicitly.

## Issuing an access token

### Via the admin UI

1. Browse to `${FESS_ENDPOINT}/admin/` and sign in with an admin account.
2. Open **System → Access Token**.
3. Click **Create New**, give the token a name (e.g. `claude-cli`), and select the permissions it needs. For most fessctl operations the `Radmin-api` permission is required.
4. Save and copy the generated token value. It is shown only once.

### Via fessctl (after you already have one admin token)

```bash
fessctl accesstoken create \
  --name claude-cli \
  --permissions "Radmin-api"
```

See `references/features/accesstoken.md` for the full subcommand surface (list, get, update, delete).

## Where to put the token

Pick the option that matches how you run fessctl.

- **direnv (`.envrc` per project):**
  ```bash
  export FESS_ENDPOINT=http://localhost:8080
  export FESS_ACCESS_TOKEN=eyJhbGciOi...
  export FESS_VERSION=15.6.0
  ```
  Add `.envrc` to `.gitignore`. Run `direnv allow` to activate.

- **Shell rc (`~/.zshrc`, `~/.bashrc`):** acceptable for personal machines, but prefer per-project `.envrc` so different Fess environments do not collide.

- **GitHub Codespaces / Actions:** store as encrypted secrets and inject via `env:` in the workflow.

- **Docker invocation:** pass `-e FESS_ACCESS_TOKEN` (the host environment variable is forwarded to the container — do **not** put the token on the command line where it would land in shell history).

Never commit a token to git, and never include it in chat output, log files, or documentation examples.

## Token scope and expiry

Fess access tokens are bearer tokens. The token's permissions are fixed at creation time; rotating permissions means issuing a new token and deleting the old one. Tokens do not auto-rotate. If a token leaks, delete it immediately via:

```bash
fessctl accesstoken list --output json | jq '.[] | select(.name=="claude-cli")'
fessctl accesstoken delete --id <id>
```

Most fessctl subcommands require admin-equivalent permission. A token issued for a non-admin user will succeed at `ping` and may succeed at some read-only `list` operations but will fail with `403 Forbidden` on `create`/`update`/`delete`.

## Smoke test

The canonical wired-up check is two commands:

```bash
fessctl ping                         # no token required
fessctl user list --size 1           # token required, admin permission required
```

Expected:

- `ping` succeeds when `FESS_ENDPOINT` is reachable.
- `user list --size 1` succeeds when both `FESS_ACCESS_TOKEN` and `FESS_VERSION` are correct and the token has admin permission.

## Common 401 / 403 causes

If `user list` fails after `ping` succeeds, the token is the problem. See `references/troubleshooting.md` for the full diagnostic flow; the short list is: token unset, token typo, token expired or revoked, or token issued without `Radmin-api` permission.
