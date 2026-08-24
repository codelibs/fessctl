# Installing & Invoking fessctl

`fessctl` is delivered as a Python package and a published Docker image. The skill picks one of two runners depending on what is available locally.

## Detection chain

Resolve the runner once at the start of a session. Use the first branch that succeeds:

```bash
resolve_fessctl() {
  if command -v fessctl >/dev/null 2>&1; then
    FESSCTL="fessctl"
    return
  fi
  FESSCTL="docker run --rm \
    -e FESS_ENDPOINT -e FESS_ACCESS_TOKEN -e FESS_VERSION \
    --add-host=host.docker.internal:host-gateway \
    ghcr.io/codelibs/fessctl:0.3.0"
}

resolve_fessctl
$FESSCTL ping
```

The order matters: a system-PATH `fessctl` is the fastest invocation; Docker is the universal fallback that works on any machine with a Docker daemon.

## Option A — system PATH install

Recommended for end users. Any install method that puts `fessctl` on `$PATH` is picked up by the detection chain automatically.

```bash
pipx install fessctl                 # if published to PyPI
# or
uv tool install fessctl              # if published to PyPI
# or, from a local source checkout:
git clone https://github.com/codelibs/fessctl.git
cd fessctl
uv pip install -e .
fessctl --help
```

`pipx` and `uv tool` are preferred because they isolate fessctl in its own virtualenv. Confirm the package is published to PyPI for the version you need; if not, the source install is the fallback.

After install, `command -v fessctl` should print a path on `$PATH` and the detection chain will pick this branch.

## Option B — Docker

Use this when a PATH install is not possible or desired.

```bash
docker run --rm \
  -e FESS_ENDPOINT="$FESS_ENDPOINT" \
  -e FESS_ACCESS_TOKEN="$FESS_ACCESS_TOKEN" \
  -e FESS_VERSION="$FESS_VERSION" \
  --add-host=host.docker.internal:host-gateway \
  ghcr.io/codelibs/fessctl:0.3.0 \
  ping
```

Two networking notes for reaching a Fess server running on the **host**:

- macOS / Windows Docker Desktop: the `--add-host=host.docker.internal:host-gateway` flag lets the container resolve `host.docker.internal`. Set `FESS_ENDPOINT=http://host.docker.internal:8080` for a host-mode Fess.
- Linux: prefer `--network host` and keep `FESS_ENDPOINT=http://localhost:8080`.

## Choosing the Docker tag

The Docker image is published at `ghcr.io/codelibs/fessctl`. **Image tags are fessctl release versions** — `0.1.0`, `0.2.0`, `0.3.0`, and so on — plus a `snapshot` tag, which is not a release and should not be pinned to. There is no `latest` tag, so an untagged `ghcr.io/codelibs/fessctl` fails to pull with `manifest unknown`; always name a release tag. The tag says nothing about which Fess server you are talking to — that is selected at runtime by `FESS_VERSION`, so the same image works against every supported Fess version. Inspect available tags at <https://github.com/codelibs/fessctl/pkgs/container/fessctl> if unsure.

## Verifying the install

Regardless of the branch chosen, the canonical smoke test is:

```bash
$FESSCTL ping
```

Expected: a success message indicating the endpoint is reachable. If this fails, see `references/troubleshooting.md` — the most common causes are an unset `FESS_ENDPOINT`, an unreachable Fess server, or (for Docker) the host-network gotchas above.

`ping` does not require `FESS_ACCESS_TOKEN`; the next test, `$FESSCTL user list --size 1`, does. Once both succeed you are wired up end-to-end.
