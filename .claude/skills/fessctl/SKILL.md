---
name: fessctl
description: Manage Fess search engine via fessctl CLI. Use for CRUD operations on web configs, file configs, data configs, schedulers, users, roles, groups, and more.
---

## Overview

fessctl is a CLI tool for managing Fess search engine via the admin API. It supports 22 resource types with standard CRUD operations.

### Prerequisites

- Python 3.13+
- fessctl installed (`pip install fessctl` or `uv pip install fessctl`)
- Fess server running with API access enabled

## Environment Setup

```bash
export FESS_ENDPOINT="http://localhost:8080"    # Fess server URL
export FESS_ACCESS_TOKEN="your-access-token"    # API access token
export FESS_VERSION="v1"                         # API version (default: v1)
```

## Output Formats

- `text` (default) - Markdown tables and structured output, AI-friendly
- `json` - Raw JSON from API
- `yaml` - YAML formatted output

Use `-o json` for programmatic parsing, `-o text` for human/AI readable output.

## Command Reference

| Resource | Commands | Description |
| --- | --- | --- |
| accesstoken | create, update, delete, get, list | API access tokens |
| badword | create, update, delete, get, list | Bad words for suggest |
| boostdoc | create, update, delete, get, list | Document boost rules |
| crawlinginfo | delete, get, list | Crawling session info |
| dataconfig | create, update, delete, get, list | Data store configs |
| duplicatehost | create, update, delete, get, list | Duplicate host mappings |
| elevateword | create, update, delete, get, list | Promoted search words |
| fileauth | create, update, delete, get, list | File auth credentials |
| fileconfig | create, update, delete, get, list | File crawl configs |
| group | create, update, delete, get, getbyname, list | User groups |
| joblog | delete, get, list | Job execution logs |
| keymatch | create, update, delete, get, list | Key match rules |
| labeltype | create, update, delete, get, list | Label types |
| pathmap | create, update, delete, get, list | Path mappings |
| relatedcontent | create, update, delete, get, list | Related content |
| relatedquery | create, update, delete, get, list | Related queries |
| reqheader | create, update, delete, get, list | Request headers |
| role | create, update, delete, get, getbyname, list | User roles |
| scheduler | create, update, delete, get, list, start, stop | Job schedulers |
| user | create, update, delete, get, getbyname, list | Users |
| webauth | create, update, delete, get, list | Web auth credentials |
| webconfig | create, update, delete, get, list | Web crawl configs |

## Common Workflows

### Health Check

```bash
fessctl ping
```

### Web Crawl Setup

```bash
# 1. Create web config
fessctl webconfig create --name "My Site" --url "https://example.com" -o json

# 2. Find the default crawler scheduler
fessctl scheduler list

# 3. Start crawling
fessctl scheduler start <scheduler-id>

# 4. Monitor job logs
fessctl joblog list
```

### User Management

```bash
# Create role
fessctl role create "editor"

# Create group
fessctl group create "team-a"

# Create user with role and group
fessctl user create "john" "password123" --role "editor" --group "team-a"

# Look up user by name
fessctl user getbyname "john"
```

### File Crawl Setup

```bash
# Create file config
fessctl fileconfig create --name "Docs" --path "/data/docs"

# Add file auth if needed
fessctl fileauth create --username "user" --file-config-id <file-config-id> --password "pass"
```

## Response Structure

- `response.status` == 0 means success
- `response.id` contains the resource ID on create
- `response.setting` contains single resource data (get)
- `response.settings` contains resource list (list)
- Exception: crawlinginfo and joblog use `response.log` / `response.logs`

## Important Patterns

- **Update**: internally does GET then PUT (merges existing data)
- **List pagination**: `--page` (default 1) and `--size` (default 100)
- **Permissions**: use `--permission "{role}guest"` format
- **Multi-value fields**: repeat the option (e.g., `--url "http://a" --url "http://b"`)

## Complete Examples

```bash
# Create a web config with multiple URLs and labels
fessctl webconfig create \
  --name "Corporate Site" \
  --url "https://www.example.com" \
  --url "https://blog.example.com" \
  --excluded-url "(?i).*(css|js|jpeg|jpg|gif|png)" \
  --depth 3 \
  --max-access-count 10000 \
  --num-of-thread 3 \
  --interval-time 5000 \
  -o json

# Update a web config
fessctl webconfig update <config-id> --name "Updated Name" --depth 5

# Delete a web config
fessctl webconfig delete <config-id>

# Get details
fessctl webconfig get <config-id>

# List with pagination
fessctl webconfig list --page 1 --size 50

# Create a scheduled job
fessctl scheduler create \
  --name "Nightly Crawl" \
  --target "all" \
  --script-type "groovy" \
  --cron-expression "0 0 2 * * ?" \
  --script-data "return container.getComponent(\"crawlJob\").execute();"

# Create a boost rule
fessctl boostdoc create \
  --url-expr "https://important.example.com/.*" \
  --boost-expr "100" \
  --sort-order 1

# Create a key match
fessctl keymatch create \
  --term "FAQ" \
  --query "title:FAQ" \
  --max-size 3 \
  --boost 10.0 \
  --version-no 1
```
