# fessctl

CLI tool to manage Fess search engine via the admin API.

## Commands

```bash
# Setup
uv sync                          # Install dependencies
uv sync --extra dev              # Install with dev dependencies

# Development
uv run fessctl --help            # Run CLI
uv run pytest tests/unit/        # Run unit tests
uv run pytest tests/commands/    # Run integration tests (requires Docker)
```

## Architecture

```
src/fessctl/
├── cli.py              # Entry point, Typer app
├── utils.py            # Shared utilities
├── api/
│   └── client.py       # HTTP client (httpx) for Fess admin API
├── config/
│   └── settings.py     # Configuration management
└── commands/           # One module per resource type (~22 modules)
    ├── webconfig.py    # Web crawling configs
    ├── fileconfig.py   # File crawling configs
    ├── dataconfig.py   # Data store configs
    ├── scheduler.py    # Scheduler jobs
    ├── user.py         # User management
    ├── role.py         # Role management
    ├── group.py        # Group management
    └── ...
```

## Testing

- **Unit tests**: `tests/unit/` — no external dependencies
- **Integration tests**: `tests/commands/` — use testcontainers (Docker Compose) to spin up Fess
- Set `FESS_VERSION` env var to control which Fess version to test against

## Code Patterns

- Uses Typer for CLI framework with subcommands per resource
- Uses httpx for HTTP calls to Fess admin API
- YAML/JSON input/output support
- Python 3.13+ required
