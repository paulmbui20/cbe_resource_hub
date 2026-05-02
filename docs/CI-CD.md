# CI/CD Pipelines

This project uses three GitHub Actions workflows with clearly separated responsibilities:
a reusable test workflow, a continuous integration & delivery pipeline, and a versioned
release pipeline.

---

## `_test.yml` — Reusable Test Workflow

**File:** `.github/workflows/_test.yml`

This is not triggered directly. It is called by both `ci-cd.yml` and `release.yml` via
`uses:`, making it the single source of truth for the entire test suite. Any change to
test environment variables, the Redis service, or the test command only needs to happen
in one place.

### What it does

Spins up a Redis service container, builds the Docker test image from `test/Dockerfile`,
then runs the full test suite inside it using `pytest-xdist` (parallel workers).

All environment variables required by the settings module are passed directly via `-e`
flags so no secrets file is needed in CI.

### Inputs

| Input | Type | Default | Purpose |
|-------|------|---------|---------|
| `python-version` | `string` | `3.12` | Python version forwarded to the test image build arg |

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

Delegates entirely to `_test.yml` via `uses: ./.github/workflows/_test.yml`.

If any test fails the pipeline stops here — the `build` job never starts.

#### 2. `build` — Build & Push Image

Runs **only** when:
- Tests passed ✓
- The event is a direct push to `main` (not a PR)

Pushes the production image to Docker Hub tagged with:

| Tag | Meaning |
|-----|---------|
| `<git-sha>` | Exact, immutable commit reference |
| `edge` | The latest unversioned build from `main` — signals "unreleased dev build" |

> **Why not `:latest` here?** Ownership of the `latest` tag is reserved exclusively for
> versioned releases pushed by `release.yml`. This guarantees that `latest` always points
> to a deliberate, tagged release — never an intermediate dev build. Watchtower on your
> compose stack should therefore track `latest` to only auto-update on real releases.

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

**Only** when a semantic-version tag is pushed:

```bash
git tag v1.2.3
git push origin v1.2.3
```

Supported tag formats:

| Format | Example | Use case |
|--------|---------|----------|
| `vMAJOR.MINOR.PATCH` | `v1.2.3` | Standard release |
| `vMAJOR.MINOR.PATCH-SUFFIX` | `v1.2.3-rc1`, `v1.2.3-hotfix.1` | Pre-releases & hotfixes |

### Jobs

#### 1. `tests` — Required gate

Delegates to `_test.yml` via `uses: ./.github/workflows/_test.yml`, identical to
`ci-cd.yml`. A release is blocked if tests fail. There is no duplication — both workflows
share the exact same test definition.

#### 2. `release` — Promote & Push Release Image

Runs only after tests pass.

Rather than rebuilding from source, this job **promotes the `:edge` image** that was
already built and validated by `ci-cd.yml` on the last merge to `main`. It pulls `:edge`,
retags it, and pushes all release tags — ensuring the artifact that was tested is
identical to the one that ships.

Pushes to Docker Hub with **four tags** simultaneously:

| Tag | Meaning |
|-----|---------|
| `1.2.3` | Exact semver — permanent, never moves |
| `1.2` | Minor float — moves forward when `1.2.4` etc. is released |
| `1` | Major float — moves forward with every `1.x.x` release |
| `latest` | Always points to the newest versioned release |

Also builds for both `linux/amd64` and `linux/arm64` platforms via QEMU.

Prints a markdown summary table to the Actions run page showing all pushed tags and the
git SHA.

**Required GitHub secrets:** same as `ci-cd.yml` — `REGISTRY_USERNAME` and
`REGISTRY_PASSWORD`.

### Promotion flow

```
merge to main
    │
    ▼
ci-cd.yml builds image → pushes :sha + :edge
    │
    │   (some time later)
    ▼
git tag v1.2.3 && git push origin v1.2.3
    │
    ▼
release.yml pulls :edge → retags → pushes :1.2.3, :1.2, :1, :latest
```

No second build. No second test run on a different artifact. The exact image that
passed CI is the one that gets the release tags.

---

## Trigger Matrix

| Event | `ci-cd.yml` | `release.yml` |
|-------|-------------|---------------|
| Push to `main` | ✅ tests + push `:sha` / `:edge` | ⛔ not triggered |
| PR → `main` | ✅ tests only | ⛔ not triggered |
| `git push origin v1.2.3` | ⛔ not triggered | ✅ tests + promote `:edge` → `:1.2.3`, `:1.2`, `:1`, `:latest` |

The two pipelines never overlap — zero duplicate resource usage.

---

## Watchtower Integration

Your compose stack uses Watchtower for automatic deployment. The tag strategy is designed
around this:

| Tag | Tracked by Watchtower? | When it updates |
|-----|------------------------|-----------------|
| `latest` | ✅ recommended | Only on a versioned `git tag` push |
| `edge` | ⚠️ optional | Every merge to `main` |
| `1.2.3` / `1.2` / `1` | ⛔ not useful | Pinned — Watchtower can't move them |

Tracking `latest` gives you automatic deploys on every real release with no manual
intervention, while keeping dev merges from reaching production unintentionally.

---

## Variables & Secrets Reference

| Name | Type | Where set | Purpose |
|------|------|-----------|---------|
| `PYTHON_VERSION` | Variable | GitHub → Settings → Actions → Variables | Python version used across all build stages; defaults to `3.12` if unset |
| `REGISTRY_USERNAME` | Secret | GitHub → Settings → Actions → Secrets | Docker Hub login username |
| `REGISTRY_PASSWORD` | Secret | GitHub → Settings → Actions → Secrets | Docker Hub access token (not your account password) |

---

## Updating the Python Version

Change the `PYTHON_VERSION` repository variable in **GitHub → Settings → Actions →
Variables**. All three workflows read it via `${{ vars.PYTHON_VERSION || '3.12' }}` —
no YAML edits needed.


The main additions and changes from the previous version are the new `_test.yml` section explaining the reusable workflow pattern, the updated `build` job explanation covering why `:edge` replaced `:latest` and what that means for Watchtower, the promotion flow diagram in `release.yml` making the build-once principle concrete and visual, a dedicated Watchtower integration section explaining which tag to track and why, and the removal of the now-incorrect note about `base_ref` guarding the release job.