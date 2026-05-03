# Multi-feature recipes

Each per-feature reference covers one resource. This file collects the small number of operations that genuinely span multiple features and need a defined order. For day-to-day single-resource CRUD, prefer the per-feature file.

All recipes assume `FESS_ENDPOINT`, `FESS_ACCESS_TOKEN`, and `FESS_VERSION` are exported. See `references/authentication.md`.

Conventions used below:

- Resource IDs are **positional arguments**, not `--id` flags.
- `--output json` returns the raw Fess admin API payload — list rows live at `.response.settings[]` (or `.response.logs[]` for `joblog` / `crawlinginfo`); single rows at `.response.setting`.
- Several `create` commands require `--version-no` for optimistic-locking (use `1` for new rows). Confirm with `fessctl <resource> create --help`.

---

## Recipe 1 — Stand up a fresh web crawl

**Goal:** Take a brand-new Fess server from "no crawl configs" to "crawled and searchable" using only fessctl.

**Prerequisites:** Fess is running, an admin token exists, target URL is reachable.

```bash
# 1. Smoke test
fessctl ping

# 2. (Optional) Label so search results can be filtered later
fessctl labeltype create \
  --name engineering \
  --value Engineering

# 3. The crawl config itself (must exist before webauth can bind to it)
WEB_CONFIG_ID=$(fessctl webconfig create \
  --name corp-portal-docs \
  --url "https://portal.example.com/docs/" \
  --included-url "https://portal.example.com/docs/.*" \
  --boost 1.0 \
  --output json | jq -r '.response.id')
echo "Created webconfig $WEB_CONFIG_ID"

# 4. (Optional) Auth credentials for the target site — bind by webconfig ID.
#    Skip this step if the target is public.
fessctl webauth create \
  --web-config-id "$WEB_CONFIG_ID" \
  --hostname portal.example.com \
  --username svc-crawler \
  --password '<secret>' \
  --protocol-scheme https \
  --auth-realm BASIC

# 5. Find the scheduler job that runs web crawls (typically "Default Crawler"
#    or any job whose script invokes the web crawler). Inspect, do not assume
#    a single ID — your Fess install may have customized it.
fessctl scheduler list --output json \
  | jq '.response.settings[] | select(.name | test("Crawler"; "i")) | {id,name,available}'

# 6. Trigger the matching scheduler job (positional ID).
fessctl scheduler start <SCHEDULER_ID>

# 7. Confirm the crawl started and finished.
fessctl joblog list --output json \
  | jq '.response.logs[0]'
```

**Verify:** the most-recent `joblog` entry transitions to a non-error terminal status, and `fessctl crawlinginfo list --output json | jq '.response.logs[0]'` shows a session created near the same timestamp.

---

## Recipe 2 — Export settings from one environment, import into another

**Goal:** Move crawl/auth/label configuration from `fess-staging` to `fess-prod`.

**Prerequisites:** admin tokens for both environments. IDs and timestamps are regenerated on the destination, so any cross-resource references (e.g. `webauth.web_config_id`) must be remapped during re-create.

```bash
# 1. Export from source.
export FESS_ENDPOINT=https://fess-staging.example.com
export FESS_ACCESS_TOKEN=$STAGING_TOKEN
mkdir -p ./fess-export
for r in labeltype webconfig fileconfig dataconfig pathmap webauth fileauth; do
  fessctl "$r" list --output yaml > "./fess-export/${r}.yaml"
done

# 2. Switch to destination.
export FESS_ENDPOINT=https://fess-prod.example.com
export FESS_ACCESS_TOKEN=$PROD_TOKEN

# 3. Re-create each resource on the destination. fessctl 0.1.0 has no
#    --from-file import flag, so each YAML must be parsed and replayed
#    as explicit flags. Example for labeltype:
yq -r '.response.settings[] |
       "fessctl labeltype create --name " + .name + " --value " + .value' \
   ./fess-export/labeltype.yaml | sh

# 4. Import in dependency order: labeltype/webauth/fileauth → webconfig/fileconfig/dataconfig.
#    Map IDs as you go: capture the new webconfig ID returned by `create --output json`
#    and use it for the matching webauth row.
```

**Verify:** `fessctl <r> list` on the destination matches the expected set. Diff the YAML exports if the migration is reversible (and after stripping `id`, `created_time`, `updated_time`, and any other server-populated fields).

---

## Recipe 3 — Investigate a failing crawl

**Goal:** Find out why a scheduled crawl is producing errors or no documents.

```bash
# 1. Which scheduler jobs are enabled?
fessctl scheduler list --output json \
  | jq '.response.settings[] | select(.available == true) | {id,name,target}'

# 2. Most recent job runs and their statuses (snake_case fields, see joblog.md).
fessctl joblog list --output json \
  | jq '.response.logs[] | {id, job_name, job_status, script_result, start_time, end_time}' \
  | head -40

# 3. For a specific failing run, fetch the full log (positional ID).
fessctl joblog get <JOBLOG_ID> --output yaml

# 4. Look at the crawl session metadata.
fessctl crawlinginfo list --output json \
  | jq '.response.logs[] | {session_id, name, value, created_time, expired_time}' \
  | head

fessctl crawlinginfo get <SESSION_ID>
```

If the joblog points at HTTP errors, suspect the target site or `webauth`. If the joblog points at index errors, suspect Fess/OpenSearch health (out of skill scope). For environment-level errors (401, connection refused) see `references/troubleshooting.md`.

---

## Recipe 4 — Provision a user with admin permissions

**Goal:** Create the role and group structure first, then attach a user. Order matters so the user references existing role/group names.

```bash
# 1. Role (or reuse an existing one). `name` is a positional argument.
fessctl role list --output json | jq -r '.response.settings[].name'
fessctl role create search-admin

# 2. Group (optional; useful for organizing users).
fessctl group create platform-team

# 3. The user. `name` and `password` are positional; --role and --group are
#    singular flags that may be repeated.
fessctl user create alice '<initial password>' \
  --role search-admin \
  --group platform-team

# 4. Verify.
fessctl user list --output json \
  | jq '.response.settings[] | select(.name=="alice")'
```

**Caution:** `delete` order is the reverse — drop users before deleting the role/group they reference, otherwise Fess keeps dangling permission strings.

---

## Recipe 5 — Tune search relevance for one query

**Goal:** Ensure that searches for "release notes" surface a curated document and demote noisy hits.

These `create` commands require fields that are easy to forget — `--version-no 1` for new rows, `--sort-order` for boostdoc, `--max-size` and `--boost` for keymatch. `relatedquery --queries` accepts a single newline-separated string (use `$'a\nb'` shell quoting).

```bash
# 1. Boost any document whose URL matches a regex.
fessctl boostdoc create \
  --url-expr 'url:"https://docs.example.com/release/.*"' \
  --boost-expr '2.0' \
  --sort-order 1

# 2. Pin a specific document for a specific query term.
fessctl keymatch create \
  --term 'release notes' \
  --query 'url:"https://docs.example.com/release/latest"' \
  --max-size 10 \
  --boost 100.0 \
  --version-no 1

# 3. Promote a phrase in suggest output.
fessctl elevateword create \
  --suggest-word 'release notes' \
  --boost 100.0 \
  --version-no 1

# 4. Surface alternative queries when the user types the term.
fessctl relatedquery create \
  --term 'release notes' \
  --queries $'changelog\nwhat is new' \
  --version-no 1

# 5. Suppress noise.
fessctl badword create --suggest-word internal-test
```

**Caution:** several of these tunings take effect only after the suggest dictionary is rebuilt or the search index is reloaded. If changes do not appear in search results, trigger the matching maintenance scheduler job (inspect `fessctl scheduler list --output json | jq '.response.settings[] | select(.name | test("Suggest|Index"; "i"))'`).

---

## Out of scope (today)

These recipes intentionally restrict themselves to features fessctl currently wraps. Operations that depend on `failureurl`, `plugin`, `backup`, `searchlist`, `stats`, `storage`, `suggest`, `systeminfo`, or `documents` are not represented here because fessctl 0.1.0 does not expose those subcommands. When fessctl adds them, update this file with the additional recipes.
