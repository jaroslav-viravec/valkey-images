# valkey-images

Build pipeline for **our own** Valkey, Valkey Sentinel and Redis Exporter container
images, published to GitHub Container Registry (GHCR) and consumed by the
[valkey-operator](https://github.com/jaroslav-viravec/valkey-operator).

## Why this repo exists

Bitnami stopped publishing freely-updated `bitnami/*` images (they moved to the frozen
`bitnamilegacy/*` namespace and a paid "Bitnami Secure Images" offering). The valkey
sources themselves remain open in [`bitnami/containers`](https://github.com/bitnami/containers).
This repo rebuilds those sources into images we control, under our own registry, so the
operator never depends on a frozen or paywalled image.

Images produced:

| Image | Built from (upstream) |
| ----- | --------------------- |
| `ghcr.io/<owner>/valkey` | `bitnami/containers` → `bitnami/valkey` |
| `ghcr.io/<owner>/valkey-sentinel` | `bitnami/containers` → `bitnami/valkey-sentinel` |
| `ghcr.io/<owner>/redis-exporter` | `bitnami/containers` → `bitnami/redis-exporter` |

Images are tagged with the upstream version, e.g. `ghcr.io/<owner>/valkey:9.1.2`.

## How it works

### No vendored sources

The build does **not** keep Bitnami's sources committed here. Bitnami keeps only the
latest minor on its `main` branch (and has no git tags), so each build **fetches the
exact requested version's sources on demand**: it resolves the version to the commit
where Bitnami published it, sparse-fetches just that directory, builds, and discards it.
That means any version Bitnami ever released can be built, not only the current latest.

### Dockerfiles (hand-maintained, parameterized)

`Dockerfile.valkey`, `Dockerfile.valkey-sentinel` and `Dockerfile.redis-exporter` are
our own build recipes (minideb base, no BuildKit secret mount). They take everything
that varies per version as build-args, derived from each version's upstream Dockerfile,
so one Dockerfile builds every version faithfully with nothing hardcoded:

- `APP_VERSION` — the product version (e.g. `9.1.2`)
- `WAIT_FOR_PORT_VERSION` — the bundled `wait-for-port` component revision
- `PACKAGES` — the apt package list for that version

Component tarballs are downloaded from `downloads.bitnami.com` and verified against the
server-provided `.sha256` (works across all versions, old and new).

### Build workflows — `build-*.yaml`

Manually triggered (`workflow_dispatch`). Give a version, or leave it empty for the
latest:

```bash
# latest valkey
gh workflow run build-valkey.yaml -R <owner>/valkey-images

# a specific version
gh workflow run build-valkey.yaml -R <owner>/valkey-images -f valkey_version=8.1.4
```

Inputs: `valkey_version` (empty = latest), `platforms` (default `linux/amd64,linux/arm64`),
`push_latest` (also tag `:latest`). The job resolves the version, fetches its sources,
derives the build-args, builds multi-arch, and pushes `ghcr.io/<owner>/valkey:<version>`.

### Sync workflows — `sync-*.yaml`

Scheduled nightly (plus manual). Each one checks `bitnami/containers` for the product's
latest sources and, when something changed, opens a **pull request** — your "a new
upstream version was released" signal. Merging is optional; builds fetch on demand
regardless.

## Using an image in the operator

Build the version you want here, then set it on the Valkey CR:

```yaml
spec:
  version: "9.1.2"              # -> ghcr.io/<owner>/valkey:9.1.2 (+ sentinel)
  metrics:
    exporterVersion: "1.92.1"  # -> ghcr.io/<owner>/redis-exporter:1.92.1
```

## Repository layout

```text
Dockerfile.valkey            # build recipes (parameterized per version)
Dockerfile.valkey-sentinel
Dockerfile.redis-exporter
.github/workflows/
  build-valkey.yaml          # build any version on demand -> GHCR
  build-sentinel.yaml
  build-exporter.yaml
  sync-valkey.yaml           # nightly: detect new upstream version -> PR
  sync-sentinel.yaml
  sync-exporter.yaml
```

## Status

| Product | Build | Notes |
| ------- | ----- | ----- |
| valkey | ✅ on-demand, any version | 2 components (valkey + wait-for-port) |
| valkey-sentinel | ✅ on-demand, any version | single component; `major.minor` source dirs |
| redis-exporter | ✅ on-demand, any version | single component; `major`-only source dirs |

## Prerequisites (one-time)

- The build workflows push to GHCR using the built-in `GITHUB_TOKEN` (needs
  `packages: write`, already set in the workflows).
- For the sync workflows to open PRs: enable **Settings → Actions → General → Workflow
  permissions → "Allow GitHub Actions to create and approve pull requests."**
