---
name: fessctl
description: Operate Fess via fessctl CLI (admin API client). Use when managing webconfigs, file/data configs, schedulers, users/roles/groups, dictionaries, access tokens, or any Fess admin resource from Claude. Covers CRUD on 22 resource types and cross-feature workflows like initial crawl setup.
license: Apache-2.0
version: 0.1.0
---

# fessctl

`fessctl` is the Python CLI for the Fess admin REST API. This skill teaches Claude to detect/run fessctl, authenticate, and operate every supported resource.

## Detection (run in this order)

1. `command -v fessctl` → use it directly
2. `$FESS_WORKSPACE/repos/fessctl` exists AND `command -v uv` → `cd $FESS_WORKSPACE/repos/fessctl && uv run fessctl`
3. Fall back to `docker run --rm -e FESS_ENDPOINT -e FESS_ACCESS_TOKEN -e FESS_VERSION ghcr.io/codelibs/fessctl:<tag>`

See `references/installation.md` for the exact wrappers.

## Required environment

- `FESS_ENDPOINT` (default `http://localhost:8080`)
- `FESS_ACCESS_TOKEN` (required for any non-`ping` call)
- `FESS_VERSION` (e.g. `15.6.0`; must match the target Fess server)

See `references/authentication.md` for token issuance.

## Always do this first

Before invoking any subcommand the assistant has not seen recently, run `fessctl <subcommand> --help` to confirm the current option surface — fessctl evolves with Fess and `--help` is the source of truth.

## Index — common references

| Topic | File |
|-------|------|
| Install / detection / wrappers | references/installation.md |
| Auth, tokens, env vars         | references/authentication.md |
| Output formats (JSON/YAML/MD)  | references/output-formats.md |
| CRUD conventions, IDs, paging  | references/conventions.md |
| Common errors and recovery     | references/troubleshooting.md |
| Multi-feature recipes          | references/workflows.md |

## Resources — per-feature reference

Each file documents one Fess admin feature: what it is, when to use it, fessctl subcommand surface, JSON shape, gotchas, and examples.

| Feature | File |
|---------|------|
| Web crawl configs        | references/features/webconfig.md |
| File crawl configs       | references/features/fileconfig.md |
| Datastore configs        | references/features/dataconfig.md |
| Web auth credentials     | references/features/webauth.md |
| File auth credentials    | references/features/fileauth.md |
| Crawl scheduler / jobs   | references/features/scheduler.md |
| Job logs                 | references/features/joblog.md |
| Crawling info            | references/features/crawlinginfo.md |
| Users                    | references/features/user.md |
| Roles                    | references/features/role.md |
| Groups                   | references/features/group.md |
| Access tokens            | references/features/accesstoken.md |
| Label types              | references/features/labeltype.md |
| Key match                | references/features/keymatch.md |
| Boost document           | references/features/boostdoc.md |
| Elevate word             | references/features/elevateword.md |
| Bad word                 | references/features/badword.md |
| Related content          | references/features/relatedcontent.md |
| Related query            | references/features/relatedquery.md |
| Path mapping             | references/features/pathmap.md |
| Duplicate host           | references/features/duplicatehost.md |
| Request header           | references/features/reqheader.md |
