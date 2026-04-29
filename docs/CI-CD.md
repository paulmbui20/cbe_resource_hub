# CI/CD Pipelines

This project has two GitHub Actions workflows, each with a distinct responsibility.

---

## `ci-cd.yml` — Continuous Integration & Delivery

**File:** `.github/workflows/ci-cd.yml`

### When it runs

| Event | Runs? |
|-------|-------|
| Push to `main` | ✅ |
| Pull request targeting `main` | ✅ |
| Tag push | ⛔ |

### Jobs

#### 1. `tests` — Run Django Tests in Parallel

Spins up a Redis service container, builds the Docker test image from `test/Dockerfile`, then
runs the full test suite inside it using `pytest-xdist` (parallel workers).

All environment variables required by the settings module are passed directly via `-e` flags so
no secrets file is needed in CI.

If any test fails the pipeline stops here — the `build` job never starts.

#### 2. `build` — Build & Push Image

Runs **only** when:
- Tests passed ✓
- The event is a direct push to `main` (not a PR)

Pushes the production image to Docker Hub tagged with:
- `docker.io/paulmbui/cbe_resource_hub:<git-sha>` — exact, immutable commit reference
- `docker.io/paulmbui/cbe_resource_hub:latest` — always the most recent main build

Uses BuildKit layer caching against a `buildcache` registry tag to keep build times short.

**Required GitHub secrets:**

| Secret | Value |
|--------|-------|
| `REGISTRY_USERNAME` | Docker Hub username |
| `REGISTRY_PASSWORD` | Docker Hub access token (not your password) |

---

## `release.yml` — Versioned Release

**File:** `.github/workflows/release.yml`

### When it runs

**Only** when a semantic-version tag is pushed **from the `main` branch**:

```bash
git tag v1.2.3
git push origin v1.2.3
```

Tags pushed from any other branch are silently ignored — no runner minutes consumed.

> **Why main-only?** `github.event.base_ref == 'refs/heads/main'` is checked in both job `if:`
> guards. `main` is the single source of truth for all releases.

### Jobs

#### 1. `tests` — Required gate

Same test suite as `ci-cd.yml`. A release is blocked if tests fail.

Skipped entirely if the tag was not cut from `main`.

#### 2. `release` — Build & Push Release Image

Runs only after tests pass AND the tag is from `main`.

Pushes to Docker Hub with **four tags** simultaneously:

| Tag | Meaning |
|-----|---------|
| `1.2.3` | Exact semver — permanent, never moves |
| `1.2` | Minor float — moves forward when `1.2.4` etc. is released |
| `1` | Major float — moves forward with every `1.x.x` release |
| `latest` | Always points to the newest release |

Also builds for both `linux/amd64` and `linux/arm64` platforms via QEMU.

Embeds OCI standard labels so every image is traceable back to the exact git tag and commit SHA.

Prints a markdown summary table to the Actions run page showing all pushed tags and the image digest.

**Required GitHub secrets:** same as `ci-cd.yml` — `REGISTRY_USERNAME` and `REGISTRY_PASSWORD`.

---

## Trigger Matrix

| Event | `ci-cd.yml` | `release.yml` |
|-------|-------------|---------------|
| Push to `main` | ✅ tests + push `sha`/`latest` | ⛔ not triggered |
| PR → `main` | ✅ tests only | ⛔ not triggered |
| `git push origin v1.2.3` from `main` | ⛔ not triggered | ✅ tests + push `1.2.3`, `1.2`, `1`, `latest` |
| `git push origin v1.2.3` from any other branch | ⛔ not triggered | ⛔ jobs skipped |

The two pipelines never overlap — zero duplicate resource usage.

---

## Variables & Secrets Reference

| Name | Where set | Purpose |
|------|-----------|---------|
| `PYTHON_VERSION` | GitHub Actions Variables (`vars.*`) | Python version used in both build stages; defaults to `3.12` if unset |
| `REGISTRY_USERNAME` | GitHub Actions Secrets | Docker Hub login username |
| `REGISTRY_PASSWORD` | GitHub Actions Secrets | Docker Hub access token |

---

## Updating the Python Version

Change the `PYTHON_VERSION` repository variable in **GitHub → Settings → Actions → Variables**.
Both workflows read it via `${{ vars.PYTHON_VERSION || '3.12' }}` — no YAML edits needed.
