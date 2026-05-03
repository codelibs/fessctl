# Scheduler / Jobs (fessctl `scheduler`)

## What it is

The Scheduler manages cron-like job definitions inside Fess. In the admin UI it lives at **System > Scheduler** (`/admin/scheduler`). Each scheduler row is a named job with a CRON expression, an executor (currently only `groovy`), and a script body. The script typically invokes the `crawlJob` component to start crawls against one or more `webconfig` / `fileconfig` / `dataconfig` IDs, but it can run any Groovy code the container exposes.

A scheduler "job" is the *definition*; an actual *run* is what happens when the cron fires (or when the job is manually started). Each run, when `job_logging` is enabled, produces one row in the **joblog** index, and while a crawler-type job is alive it also populates **crawlinginfo** rows for progress and statistics. The `target` field acts as an identifier filter so jobs can be invoked selectively from batch commands; use `all` if you do not run jobs from the CLI batch entry point.

The default Fess install ships a "Default Crawler" job which is what most operators trigger from the UI's **Start Now** button.

## When to use

- Schedule a recurring crawl (e.g. nightly at 02:00) against a fixed set of webconfig / fileconfig / dataconfig IDs.
- Trigger a one-off crawl ad-hoc without waiting for the cron tick (`scheduler start`).
- Disable a recurring job during maintenance windows without deleting it (`scheduler update --available false`).
- Stop an in-flight job that is misbehaving or consuming too many resources (`scheduler stop`).
- Inspect or export the script body of an existing job before editing it via `scheduler get -o yaml`.

## Subcommand surface

| Subcommand | Purpose |
|------------|---------|
| `create` | Create a new scheduler job (name, target, script_type, cron_expression, script_data, crawler, job_logging, available, sort_order, created_by, created_time). |
| `update` | Update an existing scheduler by ID. Only the flags you pass are overwritten; everything else is preserved by re-fetching the current setting. |
| `delete` | Delete a scheduler by ID. Removes the definition; does not abort an in-flight run. |
| `get` | Fetch a single scheduler by ID and render details (id, name, target, cron, script_type, script_data, crawler, job_logging, available, sort_order, audit fields). |
| `list` | List schedulers with `--page` / `--size` pagination. Default page size is 100. |
| `start` | Start a scheduler run immediately. Returns a `jobLogId` on success when logging is enabled. |
| `stop` | Stop a currently running scheduler. |

Always reconfirm with `fessctl scheduler <sub> --help`.

## Resource JSON shape

```json
{
  "id": "abc123",
  "name": "Nightly Web Crawl",
  "target": "all",
  "cron_expression": "0 0 2 * * ?",
  "script_type": "groovy",
  "script_data": "return container.getComponent(\"crawlJob\").logLevel(\"info\").webConfigIds([\"1\",\"2\"] as String[]).fileConfigIds([] as String[]).dataConfigIds([] as String[]).execute(executor);",
  "job_logging": "true",
  "crawler": "true",
  "available": true,
  "sort_order": 1,
  "created_by": "admin",
  "created_time": 1735689600000,
  "updated_by": "admin",
  "updated_time": 1735689600000,
  "version_no": 1,
  "crud_mode": 1
}
```

Required on create: `name`, `target`, `script_type`. The other fields default to empty strings, `available=true`, and `sort_order=1` in the CLI. Note that `crawler` and `job_logging` are passed as strings (e.g. `"true"` / `"false"`) by the admin API, while `available` is a boolean.

## Relationships

- Scheduler jobs trigger crawls against **webconfig**, **fileconfig**, and **dataconfig** entries by referencing their IDs in the Groovy `script_data`.
- Each run, when `job_logging` is enabled, produces one **joblog** row (start/end time, status, log target).
- While a crawler-type job is running, it populates **crawlinginfo** rows with per-session progress, document counts, and parameters.
- Setting `available=false` (or deleting) prevents *future* runs from firing on the cron, but does **not** abort an in-flight run — use `scheduler stop` for that.
- The `target` value is also used by `job.max.crawler.processes` (in `fess_config.properties`) to cap concurrent crawler-typed jobs.

## Gotchas

- Cron syntax follows the **Quartz** format used by LastaJob. The admin UI hint shows 5 fields (`minute hour day month day-of-week`), but the underlying engine accepts the 6/7-field Quartz form (e.g. `0 0 2 * * ?`). Test before relying on it.
- `script_type` is effectively limited to `groovy` today; passing anything else will create the row but the executor will fail at runtime.
- Groovy scripts run inside the Fess JVM with admin privileges — treat `script_data` as trusted code and review carefully on `update`.
- The schedule fires in the **server's local timezone**, not UTC. Verify the OS / container timezone before choosing cron values.
- `available=false` and "deleted" look similar in effect (no future runs) but only `delete` removes the row; prefer `available=false` for temporary disables so you can re-enable without losing the script.
- `start` returns immediately with a `jobLogId`; the run continues asynchronously. Poll **joblog** to know when it finished.
- `stop` only signals the running job; long-running steps (e.g. a single slow HTTP fetch) may take time to actually halt.
- `update` first re-fetches the current setting and merges your flags on top, so omitting a flag leaves the previous value intact — this is the safe default but means you cannot clear a string field by passing an empty string through the CLI.

## Examples

```bash
# Minimal: create a default-style web crawler job that runs nightly at 02:00
fessctl scheduler create \
  --name "Nightly Web Crawl" \
  --target "all" \
  --script-type "groovy" \
  --cron-expression "0 0 2 * * ?" \
  --script-data 'return container.getComponent("crawlJob").logLevel("info").webConfigIds(["1"] as String[]).fileConfigIds([] as String[]).dataConfigIds([] as String[]).execute(executor);' \
  --job-logging "true" \
  --crawler "true"
```

```bash
# Typical update: temporarily disable a job and shift its schedule to weekends only
fessctl scheduler update <scheduler_id> \
  --available false \
  --cron-expression "0 0 3 ? * SAT,SUN"
```

```bash
# Trigger a one-off run now, then list jobs to see status
fessctl scheduler start <scheduler_id>
fessctl scheduler list
# Inspect the resulting run via the joblog feature using the returned jobLogId
```

## See also

- fess-docs: en/15.6/admin/scheduler-guide.rst
- workflows.md: Recipe 1 (initial setup), Recipe 3 (failing crawl investigation)
- Related features: `references/features/webconfig.md`, `references/features/fileconfig.md`, `references/features/dataconfig.md`, `references/features/joblog.md`, `references/features/crawlinginfo.md`
