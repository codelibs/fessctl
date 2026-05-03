# Multi-feature recipes

Each per-feature reference covers one resource. This file collects the small number of operations that genuinely span multiple features and need a defined order. For day-to-day single-resource CRUD, prefer the per-feature file.

All recipes assume `FESS_ENDPOINT`, `FESS_ACCESS_TOKEN`, and `FESS_VERSION` are exported. See `references/authentication.md`.

---

## Recipe 1 — Stand up a fresh web crawl

**Goal:** Take a brand-new Fess server from "no crawl configs" to "crawled and searchable" using only fessctl.

**Prerequisites:** Fess is running, an admin token exists, target URL is reachable.

```bash
# 1. Smoke test
fessctl ping

# 2. (Optional) Auth credentials for the target site
#    Skip this step if the target is public.
fessctl webauth create --name corp-portal \
  --hostname portal.example.com \
  --username svc-crawler \
  --password '<secret>'

# 3. (Optional) Label so search results can be filtered later
fessctl labeltype create --name engineering --value Engineering

# 4. The crawl config itself
fessctl webconfig create \
  --name corp-portal-docs \
  --url "https://portal.example.com/docs/" \
  --included-urls "https://portal.example.com/docs/.*" \
  --boost 1.0

# 5. Find the scheduler job that runs web crawls
fessctl scheduler list --output json \
  | jq '.[] | select(.name | test("WebCrawler"; "i")) | {id,name,available}'

# 6. Trigger that job (subcommand may vary; confirm with --help)
fessctl scheduler --help

# 7. Confirm the crawl started and finished
fessctl joblog list --output json | jq '.[0]'
```

**Verify:** the matching `joblog` entry transitions to a non-error terminal state, and `crawlinginfo list` shows a session for the new config.

---

## Recipe 2 — Export settings from one environment, import into another

**Goal:** Move crawl/auth/label configuration from `fess-staging` to `fess-prod`.

**Prerequisites:** admin tokens for both environments; fields like IDs and timestamps will be regenerated on the destination.

```bash
# 1. Export from source
export FESS_ENDPOINT=https://fess-staging.example.com
export FESS_ACCESS_TOKEN=$STAGING_TOKEN
mkdir -p ./fess-export
for r in webauth fileauth labeltype webconfig fileconfig dataconfig pathmap; do
  fessctl "$r" list --output yaml > "./fess-export/${r}.yaml"
done

# 2. Switch to destination
export FESS_ENDPOINT=https://fess-prod.example.com
export FESS_ACCESS_TOKEN=$PROD_TOKEN

# 3. Re-create each resource on the destination (no native --from-file at v0.1.0;
#    you must read each YAML and reissue create with explicit flags). For example:
yq '.data[] | "fessctl labeltype create --name=" + .name + " --value=" + .value' \
   ./fess-export/labeltype.yaml | sh
```

**Verify:** `fessctl <r> list` on the destination matches what you expected. Diff the YAML exports if the migration is reversible. Re-creating dependents (webconfig depends on labeltype/webauth) requires that you reload IDs after the prerequisite resources land.

---

## Recipe 3 — Investigate a failing crawl

**Goal:** Find out why a scheduled crawl is producing errors or no documents.

```bash
# 1. Which job is failing?
fessctl scheduler list --output json \
  | jq '.[] | select(.available == true)' \
  | head

# 2. Most recent job runs and their statuses
fessctl joblog list --output json \
  | jq '.[] | {id, jobName, jobStatus, scriptResult, startTime, endTime}' \
  | head -40

# 3. For a specific failing run, fetch the full log
fessctl joblog get --id <joblog id> --output yaml

# 4. Look at the crawl session metadata
fessctl crawlinginfo list --output json \
  | jq '.[] | {sessionId, name, createdTime, expiredTime}' \
  | head

fessctl crawlinginfo get --id <session id>
```

If the joblog points at HTTP errors, suspect the target site or `webauth`. If the joblog points at index errors, suspect Fess/OpenSearch health (out of skill scope). For environment-level errors (401, connection refused) see `references/troubleshooting.md`.

---

## Recipe 4 — Provision a user with admin permissions

**Goal:** Create the role and group structure first, then attach a user. Order matters so the user references existing role/group IDs.

```bash
# 1. Role (or reuse an existing one)
fessctl role list --output json | jq -r '.[].name'
fessctl role create --name search-admin

# 2. Group (optional; useful for organizing users)
fessctl group create --name platform-team

# 3. The user, tied to the role and group
fessctl user create \
  --name alice \
  --password '<initial password>' \
  --roles search-admin \
  --groups platform-team

# 4. Verify
fessctl user list --output json | jq '.[] | select(.name=="alice")'
```

**Caution:** `delete` order is the reverse — drop users before deleting the role/group they reference, otherwise Fess keeps dangling references.

---

## Recipe 5 — Tune search relevance for one query

**Goal:** Ensure that searches for "release notes" surface a curated document and demote noisy hits.

```bash
# 1. Boost any document whose URL matches a pattern
fessctl boostdoc create \
  --url-expr 'url:"https://docs.example.com/release/*"' \
  --boost-expr '2.0'

# 2. Pin a specific document for a specific query term
fessctl keymatch create \
  --term 'release notes' \
  --query 'url:"https://docs.example.com/release/latest"' \
  --max-size 10 \
  --boost 100.0

# 3. Suggest a related query when the user types a near-term
fessctl elevateword create --suggest-word "release notes" --boost 100.0
fessctl relatedquery create \
  --term 'release notes' \
  --queries '["changelog","what is new"]'

# 4. Filter out noise
fessctl badword create --suggest-word "internal-test"
```

**Caution:** Several of these tunings take effect only after the suggest cache and/or search index are reloaded. If changes do not appear in search results, trigger the relevant scheduler job (see Recipe 1, step 5).

---

## Out of scope (today)

These recipes intentionally restrict themselves to features fessctl currently wraps. Operations that depend on `failureurl`, `plugin`, `backup`, `searchlist`, `stats`, `storage`, `suggest`, `systeminfo`, or `documents` are not represented here because fessctl 0.1.0 does not expose those subcommands. When fessctl adds them, update this file with the additional recipes.
