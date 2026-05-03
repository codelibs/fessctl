# Installing & Invoking fessctl

`fessctl` is delivered as a Python package and a published Docker image. The skill picks one of three runners depending on what is available locally.

## Detection chain

Resolve the runner once at the start of a session. Use the first branch that succeeds:

```bash
resolve_fessctl() {
  if command -v fessctl >/dev/null 2>&1; then
    FESSCTL="fessctl"
    return
  fi
  if [[ -d "${FESS_WORKSPACE:-$PWD}/repos/fessctl" ]] && command -v uv >/dev/null 2>&1; then
    FESSCTL="uv --directory ${FESS_WORKSPACE:-$PWD}/repos/fessctl run fessctl"
    return
  fi
  FESSCTL="docker run --rm \
    -e FESS_ENDPOINT -e FESS_ACCESS_TOKEN -e FESS_VERSION \
    --add-host=host.docker.internal:host-gateway \
    ghcr.io/codelibs/fessctl:${FESS_VERSION:-latest}"
}

resolve_fessctl
$FESSCTL ping
```

The order matters: a system-PATH `fessctl` (e.g. installed via `pipx` or any future package manager) is the fastest invocation, followed by an in-tree `uv run` against `repos/fessctl`, with the published Docker image as the universal fallback.

## Option A — system PATH install

Recommended for end users who do not have a `fess-workspace` checkout.

```bash
pipx install fessctl
fessctl --help
```

`pipx` is preferred because it isolates fessctl in its own virtualenv. (Confirm the package is published to PyPI for the version you need; if not, fall back to a source install.) The project is also installable from source:

```bash
git clone https://github.com/codelibs/fessctl.git
cd fessctl
uv pip install -e .
```

After either install, `command -v fessctl` should print a path on `$PATH` and the detection chain will pick this branch.

## Option B — fess-workspace dev mode

Use this when you are actively editing fessctl source inside a `fess-workspace` clone. Local edits are picked up on the next invocation.

```bash
cd $FESS_WORKSPACE/repos/fessctl
uv sync
uv run fessctl --help
```

`uv sync` only needs to run when `pyproject.toml` or `uv.lock` changes; subsequent calls reuse the cached environment. This branch is what the detection chain selects when `repos/fessctl` exists and `uv` is on `$PATH`.

## Option C — Docker

Use this when neither a PATH install nor a fess-workspace clone is available.

```bash
docker run --rm \
  -e FESS_ENDPOINT="$FESS_ENDPOINT" \
  -e FESS_ACCESS_TOKEN="$FESS_ACCESS_TOKEN" \
  -e FESS_VERSION="$FESS_VERSION" \
  --add-host=host.docker.internal:host-gateway \
  ghcr.io/codelibs/fessctl:0.1.0 \
  ping
```

Two networking notes for reaching a Fess server running on the **host**:

- macOS / Windows Docker Desktop: the `--add-host=host.docker.internal:host-gateway` flag lets the container resolve `host.docker.internal`. Set `FESS_ENDPOINT=http://host.docker.internal:8080` for a host-mode Fess.
- Linux: prefer `--network host` and keep `FESS_ENDPOINT=http://localhost:8080`.

## Choosing the Docker tag

The Docker image is published at `ghcr.io/codelibs/fessctl`. Pin a tag rather than `latest` for reproducible runs. The convention is to keep the image tag close to the Fess version it has been validated against — if you are talking to a Fess 15.6 server, prefer the tag whose `FESS_VERSION` default matches. Inspect available tags at <https://github.com/codelibs/fessctl/pkgs/container/fessctl> if unsure.

## Verifying the install

Regardless of the branch chosen, the canonical smoke test is:

```bash
$FESSCTL ping
```

Expected: a success message indicating the endpoint is reachable. If this fails, see `references/troubleshooting.md` — the most common causes are an unset `FESS_ENDPOINT`, an unreachable Fess server, or (for Docker) the host-network gotchas above.

`ping` does not require `FESS_ACCESS_TOKEN`; the next test, `$FESSCTL user list --size 1`, does. Once both succeed you are wired up end-to-end.
