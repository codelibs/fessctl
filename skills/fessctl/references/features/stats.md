# Stats (fessctl `stats`)

## What it is
Runtime statistics of the Fess server: JVM memory, garbage collection and threads, OS memory and load, process file descriptors and CPU, the search engine cluster health, and the filesystem roots.

Read only. Available in every version fessctl supports (14.19.2, 15.6.1, 15.7.0, 15.8.0, 15.9.0).

## When to use
- Check heap usage, thread counts or the load average of the Fess process.
- Check the search engine cluster status (`engine.status`) and shard counts, or the free disk space (`fs`).

## Subcommand surface
`stats` takes no subcommand; it takes `--output text|json|yaml`.

| Command | Purpose |
| --- | --- |
| `fessctl stats` | Show the statistics. Text output is a `NAME \| VALUE` table of dotted names such as `jvm.memory.heap.used`; list items are named by their key or path (`jvm.gc[young].count`, `fs[/].free`). `json`/`yaml` return the response unchanged. |

Always reconfirm with `fessctl stats --help`.

## Resource JSON shape
```json
{
  "response": {
    "status": 0,
    "stats": {
      "jvm": {"memory": {"heap": {"used": 366768360, "max": 536870912, "percent": 68}}, "gc": [{"key": "young", "count": 10, "time": 48}], "threads": {"count": 37, "peak": 37}, "uptime": 26797},
      "os": {"memory": {"physical": {"free": 5921939456, "total": 50425147392}}, "cpu": {"percent": 0}, "load_averages": [2.12, 0.98, 0.86]},
      "process": {"file_fescriptor": {"open": 221, "max": 1048576}},
      "engine": {"status": "green", "cluster_name": "fess-search", "number_of_nodes": 1, "active_shards": 65, "unassigned_shards": 0},
      "fs": [{"path": "/", "used": 182361546752, "free": 101632278528, "total": 270233210880, "percent": 67}]
    }
  }
}
```
Sizes are bytes, times are milliseconds. A few keys are spelled oddly by the server and passed through unchanged (for example `process.file_fescriptor`).

## Gotchas
- When Fess cannot reach the search engine, the call still succeeds: `engine.status` is `red` and `engine.exception` carries the message. Check the field, not the exit code.

## Examples
```bash
fessctl stats
fessctl stats -o json | jq '.response.stats.engine.status'
fessctl stats -o json | jq '.response.stats.jvm.memory.heap.percent'
```
