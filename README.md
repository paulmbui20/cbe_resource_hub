# 📚 CBE Resource Hub

> A high-performance, open-source educational CMS built for Kenya's Competency-Based Education (CBC) curriculum. Enables
> educators, vendors, and administrators to share, discover, and manage curriculum-aligned learning materials.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.0-green)](https://djangoproject.com)
[![CI](https://github.com/paulmbui20/cbe_resource_hub/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/paulmbui20/cbe_resource_hub/actions/workflows/ci-cd.yml)

---

## ✨ Features

- **Multivendor Marketplace** — Educators can register as Content Creators and upload resources
- **Wagtail CMS Blog** — Integrated powerful blogging engine with `/wagtail-admin/` panel and seamlessly styled front-end
- **CBC Curriculum Aligned** — From Pre-Primary level through Senior School (Grade 12) level, all standard learning
  areas
- **Custom Admin Panel** — Fully branded management UI (no Django Admin dependency)
- **Rich Text Editing** — TinyMCE (served locally, no CDN) for page and resource descriptions
- **Secure Auth** — email-only login via `django-allauth` with Google OAuth support
- **Forced Password Reset** — Admin-created users are auto-prompted to change password on first login
- **Favorites System** — HTMX-powered bookmarking without page reloads
- **Interactive DataTables** — Client-side search, sort, and pagination across all admin lists
- **Bulk User Management** — Multi-select enable/disable users with self-protection guard
- **File Storage** — Cloudflare R2 (S3-compatible) in production; local filesystem in development
- **Deep File Validation** — Magic/mimetype signature scanning via the `validators` package to rigorously enforce uploaded file integrity
- **Built-in Rate Limiting** — `django-smart-ratelimit` + `django-axes` brute-force protection
- **Performance** — Query profiling via Silk, async-ready with Django 6 ASGI
- **Global Toast Notifications** — Alpine.js system auto-fires Django messages; also JS-dispatchable from any page
- **Robust Notification System** — Async Celery-powered email delivery with retries, idempotency, and SMTP-safe rate
  limiting
- **Notification Dashboard** — Visualize email history, delivery status, and manual retry triggers
- **Dynamic Menus** — CMS-driven header & footer navigation, zero code changes needed
- **Contact Page** — Full form with email delivery, honeypot anti-spam, and animated responsive UI
- **Enhanced Homepage** — Live HTMX search bar with debounced suggestions dropdown, resource type card grid, compact
  level pills, tabbed recent/popular sections, animated intersection stats counter, and scroll-to-top FAB
- **SEO Optimization** — Pre-configured Open Graph (OG), Twitter Cards, JSON-LD structured data, and dynamic meta
  descriptions across all public pages
- **SEO Landing Pages** — Per resource-type detail pages (`/resources/type/<type>/`) with JSON-LD `CollectionPage`
  schema, breadcrumbs, pagination, and sidebar navigation
- **Sitemap & robots.txt** — Auto-generated `sitemap.xml` and configurable `robots.txt` for Search Console
- **Custom Branding** — Fully integrated SVG logo support for high-DPI scaling across the platform and favicons

---

## 🗂 Project Structure

```
.
├── accounts                   # accounts app
│   ├── __init__.py           
│   ├── adapters.py            # adapters to work with allauth
│   ├── admin.py               # admin registration of models
│   ├── admin_urls.py          # custom admin urls
│   ├── admin_views.py         # custom admin views
│   ├── apps.py                # accounts app apps config
│   ├── migrations/           # folder with accounts app migration files
│   ├── models.py             # accounts models for users 
│   ├── signals.py            # signals 
│   ├── tests/                # accounts app tests
│   ├── urls.py               # accounts app urls
│   └── views.py              # accounts app views
├── build.sh                  # build script for the project
├── cbe_res_hub
│   ├── __init__.py           # cbe_res_hub app init
│   ├── asgi.py               # cbe_res_hub app asgi
│   ├── celery.py             # cbe_res_hub app celery
│   ├── middleware.py         # cbe_res_hub app middleware
│   ├── settings/
│   │   ├── base.py          # shared settings loaded by every environment
│   │   ├── development.py   # DEBUG=True, SQLite option, debug toolbar
│   │   ├── production.py    # PostgreSQL, Cloudflare R2, Sentry
│   │   └── testing.py       # SQLite, Celery eager, filesystem storage
│   ├── urls.py              # cbe_res_hub app urls
│   └── wsgi.py              # cbe_res_hub app wsgi
├── cms
│   ├── __init__.py          # cms app init
│   ├── admin.py             # admin registration of models
│   ├── admin_urls.py        # custom admin urls
│   ├── admin_views.py       # custom admin views
│   ├── apps.py              # cms app apps config
│   ├── context_processors.py # cms app context processors
│   ├── forms.py             # cms app forms
│   ├── management
│   │   ├── __init__.py      # cms app management init
│   │   └── commands
│   │       ├── __init__.py  # cms app commands init
│   │       ├── populate_menus.py # cms app commands populate menus
│   │       └── populate_site_settings.py # cms app commands populate site settings
│   ├── migrations/           # folder with cms app migration files
│   ├── models.py             # cms app models
│   ├── signals.py            # cms app signals
│   ├── tests.py              # cms app tests
│   ├── urls.py               # cms app urls
│   └── views.py              # cms app views
├── compose.yaml              # docker compose file
├── conftest.py               # conftest for pytest
├── docker-health-check.py    # docker health check script
├── Dockerfile                # dockerfile for the project
├── docs                      # documentation folder
│   ├── CI-CD.md              # CI/CD pipeline reference
│   ├── HOMEPAGE.md           # Homepage reference
│   ├── MENUS.md              # Menus reference
│   ├── NOTIFICATIONS.md      # Notifications reference
│   └── ROADMAP.md            # Roadmap reference
├── files                     # folder with files app files
│   ├── __init__.py           # files app init
│   ├── admin.py              # admin registration of models
│   ├── admin_urls.py         # custom admin urls
│   ├── admin_views.py        # custom admin views
│   ├── apps.py               # files app apps config
│   ├── management
│   │   ├── __init__.py       # files app management init
│   │   └── commands
│   │       ├── __init__.py   # files app commands init
│   │       ├── calculate_file_hashes.py # files app commands calculate file hashes
│   │       ├── check_orphaned_files.py # files app commands check orphaned files
│   │       └── regenerate_metadata.py # files app commands regenerate metadata
│   ├── migrations/           # folder with files app migration files
│   ├── models.py             # files app models
│   ├── signals.py            # files app signals
│   ├── tests                 # folder with files app tests
│   │   ├── __init__.py       # files app tests init
│   │   ├── fixtures.py       # files app tests fixtures
│   │   ├── README.md         # files app tests README
│   │   ├── test_admin.py     # files app tests admin
│   │   ├── test_integration.py # files app tests integration
│   │   ├── test_management_commands.py # files app tests management commands
│   │   ├── test_models.py    # files app tests models
│   │   ├── test_performance.py # files app tests performance
│   │   └── test_validators.py # files app tests validators
│   ├── urls.py               # files app urls
│   └── views.py              # files app views
├── helpers                   # folder with helpers files
│   ├── __init__.py           # helpers app init
│   ├── cloudflare            # folder with cloudflare files
│   │   ├── __init__.py       # cloudflare app init
│   │   ├── settings.py       # cloudflare app settings
│   │   └── storages.py       # cloudflare app storages
│   └── storages
│       ├── __init__.py       # storages app init
│       └── mixins.py         # storages app mixins
├── LICENSE                   # license file
├── manage.py                 # manage.py file
├── notifications             # folder with notifications files
│   ├── __init__.py           # notifications app init
│   ├── admin.py              # notifications app admin
│   ├── admin_views.py        # notifications app admin views
│   ├── apps.py               # notifications app apps config
│   ├── migrations/           # folder with notifications app migration files
│   ├── models.py             # notifications app models
│   ├── notifier.py           # notifications app notifier
│   ├── signals.py            # notifications app signals
│   ├── tasks.py              # notifications app tasks
│   ├── templates/            # folder with notifications app templates
│   ├── tests/                # pytest package
│   │   ├── __init__.py       # notifications app tests init
│   │   ├── base.py           # notifications app tests base
│   │   └── test_*.py         # notifications app tests test_*.py
│   ├── urls.py               # notifications app urls
│   └── views.py              # notifications app views
├── pyproject.toml              # pyproject.toml file
├── README.md                 # README.md file
├── requirements.txt          # requirements.txt file
├── resources                 # folder with resources files
│   ├── __init__.py           # resources app init
│   ├── admin.py              # resources app admin
│   ├── admin_dependency_views.py # resources app admin dependency views
│   ├── admin_urls.py         # resources app admin urls
│   ├── admin_views.py        # resources app admin views
│   ├── apps.py               # resources app apps config
│   ├── forms.py              # resources app forms
│   ├── management/           # folder with resources app management files
│   ├── migrations/           # folder with resources app migration files
│   ├── models.py             # resources app models
│   ├── tests/                # pytest package
│   │   ├── __init__.py       # resources app tests init
│   │   ├── base.py           # resources app tests base
│   │   └── test_*.py         # resources app tests test_*.py
│   ├── urls.py               # resources app urls
│   ├── validators.py         # resources app validators
│   └── views.py              # resources app views
├── seo                         # folder with seo files
│   ├── __init__.py           # seo app init
│   ├── admin.py              # seo app admin
│   ├── admin_views.py        # seo app admin views
│   ├── apps.py               # seo app apps config
│   ├── management/           # folder with seo app management files
│   ├── middleware.py         # seo app middleware
│   ├── migrations/           # folder with seo app migration files
│   ├── models.py             # seo app models
│   ├── static/               # folder with seo app static files
│   ├── tests/                # pytest package
│   │   ├── __init__.py       # seo app tests init
│   │   ├── base.py           # seo app tests base
│   │   └── test_*.py         # seo app tests test_*.py
│   ├── urls.py               # seo app urls
│   ├── utils.py              # seo app utils
│   └── views.py              # seo app views
├── test                       # Docker test harness
│   ├── compose.yaml          # Docker compose file
│   ├── Dockerfile            # Dockerfile for test
│   └── test.sh               # test script
├── tests                      # Project-level tests
│   ├── __init__.py           # project-level tests init
│   ├── test_integration.py    # Cross-app end-to-end flows
│   └── test_settings.py       # Django settings validation
├── uv.lock                   # uv.lock file
├── website                   # folder with website files
│   ├── __init__.py           # website app init
│   ├── admin.py              # website app admin
│   ├── admin_views.py        # website app admin views
│   ├── apps.py               # website app apps config
│   ├── forms/                # folder with website app forms
│   ├── health_checks.py      # website app health checks
│   ├── management/           # folder with website app management files
│   ├── migrations/           # folder with website app migration files
│   ├── models.py             # website app models
│   ├── sitemaps.py           # website app sitemaps
│   ├── static/               # folder with website app static files
│   ├── templates/            # folder with website app templates
│   ├── templatetags/         # folder with website app templatetags
│   ├── tests/                # pytest package
│   │   ├── __init__.py       # website app tests init
│   │   ├── base.py           # website app tests base
│   │   └── test_*.py         # website app tests test_*.py
│   ├── urls/                 # folder with website app urls
│   └── views.py              # website app views
```

> **Note:** All templates live under `website/templates/` grouped by app sub-folder — a known
> architectural quirk documented in [docs/ROADMAP.md](./docs/ROADMAP.md).

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **PostgreSQL** default db
- **Redis** required for cache, and celery broker and task queue

### 1. Clone the repository

```bash
git clone https://github.com/paulmbui20/cbe_resource_hub.git
cd cbe_resource_hub
```

### 2. Install dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtualenv and install all deps
uv sync
```

### 3. Configure environment variables

Create the env file on the project root directory and fill in your values:

```bash
touch .env && nano .env
```

Edit `.env`:

```.dotenv
# ── Django Core ──────────────────────────────────────────────
SECRET_KEY=your-very-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://cberesources.localhost,

ENVIRONMENT=development

# ── Email ─────────────────────────────────────────────────────
# For production / or dev (in dev i use mailpit):
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=admin@localhost


# ── Google OAuth (django-allauth) ─────────────────────────────
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret

# ── Cloudflare R2 (Production File Storage) ───────────────────
# Leave blank in development — files will use local media/ folder
CLOUDFLARE_R2_BUCKET=
CLOUDFLARE_R2_BUCKET_ENDPOINT=
CLOUDFLARE_R2_ACCESS_KEY=
CLOUDFLARE_R2_SECRET_KEY=

CLOUDFLARE_R2_PUBLIC_BUCKET=
CLOUDFLARE_R2_PUBLIC_BUCKET_ENDPOINT=
CLOUDFLARE_R2_PUBLIC_ACCESS_KEY=
CLOUDFLARE_R2_PUBLIC_SECRET_KEY=

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PASSWORD=
REDIS_PORT=6379

# ACCOUNT_EMAIL_VERIFICATION: "none" | "optional" | "mandatory"
ACCOUNT_EMAIL_VERIFICATION=optional

# ── Site Identity ─────────────────────────────────────────────────────────────
SITE_ID=1
SITE_URL=http://localhost:8000
SITE_NAME='CBE Resource Hub'
ADMIN_NAME=admin
ADMIN_EMAIL=admin@localhost

# ── PostgreSQL ────────────────────────────────────────────────────────────────
# Local  (used when ENVIRONMENT != production)
DATABASE_URL_LOCAL=postgresql://user:pass@host:port/db
# Production (used when ENVIRONMENT=production)
DATABASE_URL=postgresql://user:pass@host:port/db

# ── Sentry ────────────────────────────────────────────────────────────────────
SENTRY_DSN=

# ── Cache Timeout ─────────────────────────────────────────────────────────────
CACHE_TIMEOUT=2419200

# ── Contact Details ─────────────────────────────────────────────────────────────
CONTACT_EMAIL=info@localhost
CONTACT_PHONE=+254712345678

# Dev env vars
ENABLE_DEBUG_TOOLBAR=True
ENABLE_SILK=False

USE_SQLITE=False

POSTGRES_USER=postgres
POSTGRES_PASSWORD=pass
POSTGRES_DB=cbe_resource_hub
PGUSER=postgres


```

### 4. Apply migrations

```bash
uv run python manage.py migrate
```

### 5. Prepopulate some important default settings

```bash
uv run python manage.py populate_site_settings

```

This seeds settings idempotently like: site_name, contact_phone, contact_email, google_oauth_client_id, site_indexing,
meta_description.
Some of these need to come from the .env variables set above

### 6. Prepopulate Primary Header and Footer Menus and their menu items

```bash
uv run python manage.py populate_menus
```

### 7. Seed the Kenyan CBC curriculum

This is a one-time idempotent command. Safe to run multiple times.

```bash
uv run python manage.py prepopulate_cbe
```

This seeds:

- **5 Education Levels**: Pre-Primary, Lower Primary, Upper Primary, Junior School, Senior School
- **14 Grades**: PP1–PP2, Grade 1–12
- **30+ Learning Areas**: aligned to each education level per CBC 2026 framework

### 8. Create a superuser (Admin)

```bash
uv run python manage.py createsuperuser
```

> Enter your **email** when prompted (username is auto-generated). The `auto_set_admin_role` signal automatically
> promotesto `Role.ADMIN`.

### 7. Run the development server

```bash
uv run python manage.py runserver
```

Visit: http://localhost:8000

---

## 🔑 Key URLs

| URL                              | Description                                                         |
| -------------------------------- | ------------------------------------------------------------------- |
| `/`                              | Public homepage — live search, resource type cards, stats, partners |
| `/resources/`                    | Searchable & filterable resource catalogue                          |
| `/blog/`                         | Public blog page powered by Wagtail                                 |
| `/resources/type/<type>/`        | SEO-optimised resource type landing page                            |
| `/contact/`                      | Contact form                                                        |
| `/management/`                   | Custom admin panel (Admin/Superuser only)                           |
| `/wagtail-admin/`                | Wagtail CMS administrative dashboard                                |
| `/accounts/login/`               | Email login page                                                    |
| `/accounts/signup/`              | Registration                                                        |
| `/accounts/social/login/google/` | Google OAuth entry                                                  |
| `/account/password/change/`      | Password change (forced on first admin-created login)               |
| `/pages/<slug>/`                 | CMS static pages                                                    |
| `/sitemap.xml`                   | Auto-generated sitemap                                              |
| `/robots.txt`                    | Search engine crawl directives                                      |

---

## 🍽️ Menu System

Navigation menus are **100% database-driven** — no code changes needed.

### Setup in 3 steps

1. **Admin Panel → Menus → + Add Menu** — use one of the reserved slot names:

   | Menu Name        | Where it renders                   |
   | ---------------- | ---------------------------------- |
   | `primary_header` | Desktop & mobile header navigation |
   | `footer`         | Footer quick-links column          |

2. **Admin Panel → Menu Items → + Add Menu Item** — fill in Title, URL, and Order

3. **Dropdown support**: Set a parent item's URL to `#`, then point child items to it. The header auto-renders them as
   an animated dropdown.

> Full examples and field reference: [docs/MENUS.md](./docs/MENUS.md)

---

## 🔔 Global Notification System

All `django.contrib.messages` notifications automatically display as animated toast popups on every page — no extra
template code needed.

**Trigger from JavaScript anywhere:**

```js
window.dispatchEvent(new CustomEvent('notify', {
    detail: {
        type: 'success',   // 'success' | 'error' | 'warning' | 'info'
        message: 'Done! Your changes have been saved.'
    }
}))
```

Toasts auto-dismiss after 5 seconds with an animated progress bar. Users can also dismiss them manually.

---

## 👤 User Roles

| Role               | Permissions                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------------- |
| **Standard User**  | Browse & download resources, manage favourites                                              |
| **Vendor/Creator** | All of the above + upload and manage own resources                                          |
| **Admin**          | Full management panel access: CRUD for users, pages, resources, menus, settings, curriculum |
| **Superuser**      | All Admin permissions + Django internals access                                             |

> **Security Note:** Users cannot self-promote to Admin. Only superusers or existing Admins can assign the Admin role
> via the management panel.

---

## 🛡 Authentication & Security

### Email-only Login

All authentication uses **email** as the primary identifier. Usernames are auto-generated internally and never shown to
users.

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create an OAuth 2.0 Client ID (Web application)
3. Set Authorized redirect URI: `http://localhost:8000/accounts/google/login/callback/`
4. Add your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to `.env`
5. In the Django admin or shell, add a `SocialApp` for Google:
   ```python
   from allauth.socialaccount.models import SocialApp
   from django.contrib.sites.models import Site
   app = SocialApp.objects.create(provider='google', name='Google', client_id='...', secret='...')
   app.sites.add(Site.objects.get_current())
   ```

### Force Password Change

When an admin creates a new user through the management panel:

- A secure 12-character password is auto-generated
- The password is shown **once** in the success message (copy and share securely)
- The `must_change_password` flag is set on the user account
- The `ForcePasswordChangeMiddleware` intercepts all requests for that user and redirects them to
  `/account/password/change/` until they comply

---

## 📁 File Storage

### Development

Files are stored in the `media/` directory locally.

### Production (Cloudflare R2)

Configure your R2 credentials in `.env`. The system uses two buckets:

- **Private bucket** — for paid/restricted resources
- **Public bucket** — for free resources (publicly accessible URLs)

Set up R2 in the Cloudflare dashboard:

1. Create two R2 buckets (e.g. `cbe-private` and `cbe-public`)
2. Create an API token with R2 read/write permissions
3. For the public bucket, enable "Public Access" in R2 settings
4. Fill in all `CLOUDFLARE_R2_*` variables in `.env`

### Mock R2/S3 compatible storage in dev with Minio

It's possible to use r2/s3 compatible storage in development by installing Minio with docker and creating the buckets

to run minio locally run the following command

```bash
docker run -d \
--name minio \
-p 9000:9000 \
-p 9001:9001 \
-v minio_data:/data \
-e MINIO_ROOT_USER=minio \
-e MINIO_ROOT_PASSWORD=minio123 \
quay.io/minio/minio server /data --console-address ":9001"
```

> visit minio webaddress on browser at http://localhost:9001

Create the three buckets, by default they are all private to change one to public that exec into minio
container and use `mc` to adjust policy

### Run an email server smtp on localhost to test email sending

To test email sending locally and offline with an smpt server use mailpit

---

## 🎨 Frontend Stack

| Technology                    | Purpose                                                   |
| ----------------------------- | --------------------------------------------------------- |
| **Tailwind CSS v4**           | Utility-first styling                                     |
| **Alpine.js**                 | Reactive UI (modals, bulk actions, dropdowns)             |
| **HTMX**                      | Server-driven interactivity (favourites, partial updates) |
| **TinyMCE** (local)           | Rich text editor, served from static files — no CDN       |
| **simple-datatables** (local) | Client-side sort/search/paginate — no CDN                 |

---

## ⚙️ Management Commands

```bash
# Seed important site settings
uv run python manage.py python manage.py populate_site_settings

# Seed Kenyan CBC curriculum (idempotent)
uv run python manage.py prepopulate_cbe

# Seed default navigation menus (Header & Footer)
uv run python manage.py populate_menus

# Standard Django commands
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py collectstatic

# Run tests with pytest (recommended)
uv run pytest


# Legacy test runner (also works)
uv run python manage.py test
```

---

## 🧪 Testing

The project uses **pytest** with **pytest-xdist** for parallel test execution.
All app-level tests live in `<app>/tests/` packages. Project-level tests (settings
validation and cross-app integration flows) are in the top-level `tests/` package.

```bash
# Run the full suite (sequential)
uv run pytest

# Run in parallel (recommended — matches CI)
uv run pytest -n auto

# Run with DB reuse and no migrations (fastest for dev iteration)
uv run pytest --reuse-db --nomigrations

# Run only a specific app
uv run pytest website/tests/

# Run settings and integration tests
uv run pytest tests/

# Run with coverage
uv run pytest --cov=. --cov-report=html
```

> **1 395 tests across all apps** — settings validation, unit tests, integration
> flows, file upload concurrency, performance baselines, and admin CRUD all run
> at 100% pass rate in CI.

---

## 🚀 CI/CD

Two GitHub Actions workflows handle automated testing and Docker image publishing.
See [docs/CI-CD.md](./docs/CI-CD.md) for the full reference.

**Quick summary:**

| Trigger                              | What happens                                                    |
| ------------------------------------ | --------------------------------------------------------------- |
| Push / PR → `main`                   | Full test suite runs; image pushed as `sha` + `latest` on merge |
| `git push origin v1.2.3` from `main` | Tests run, then image pushed as `1.2.3`, `1.2`, `1`, `latest`   |

**Required GitHub Secrets:** `REGISTRY_USERNAME`, `REGISTRY_PASSWORD`

### FileField / ImageField `.url` safety

Django's `ImageField` and `FileField` raise `ValueError` if you call `.url` when no file is associated (even if the
field is not `None`). Always guard with `.name`:

```html
{# ❌ Wrong — raises ValueError if field is empty #}
{% if resource.featured_image %}{{ resource.featured_image.url }}{% endif %}

{# ✅ Correct #}
{% if resource.featured_image and resource.featured_image.name %}
{{ resource.featured_image.url }}
{% endif %}
```

### HTMX live search

The homepage search bar uses HTMX partial responses. The view returns `resources/partials/search_suggestions.html` (max
6 results) when `?suggestions=1` is in the query string:

```python
# resources/views.py — ResourceListView
if self.request.GET.get('suggestions') == '1':
    self.template_name = 'resources/partials/search_suggestions.html'
```

### Animated stats counter

The stats section uses a vanilla `IntersectionObserver` (no Alpine plugin dependency) that dispatches a `animate-stats`
CustomEvent on the section when it enters the viewport. Alpine listens with `@animate-stats.window` and runs the counter
animation. This is more reliable than `x-intersect` because it doesn't depend on Alpine plugin loading order.


---

## 🏗 Production Deployment

### Environment

1. Set `DEBUG=False` in `.env`
2. Set `ALLOWED_HOSTS=yourdomain.com`
3. Configure a proper `DATABASE_URL` (PostgreSQL)
4. Set `SECRET_KEY` to a long random string
5. Run `uv run python manage.py collectstatic`

### Recommended Stack

- **Web server**: Nginx + Gunicorn (ASGI: uvicorn)
- **Database**: PostgreSQL 16+
- **Cache/Queue**: Redis
- **Process manager**: systemd or Supervisor
- **TLS**: Let's Encrypt via Certbot

### Example Gunicorn command

```bash
gunicorn cbe_res_hub.asgi:application -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:8000
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

---

## 🙏 Acknowledgements

- [Django](https://djangoproject.com) — the web framework
- [django-allauth](https://allauth.org) — authentication
- [Wagtail CMS](https://wagtail.org) — blog and content management
- [validators](https://pypi.org/project/validators/) & [python-magic](https://pypi.org/project/python-magic/) — file validation
- [TinyMCE](https://tiny.cloud) — rich text editor
- [Alpine.js](https://alpinejs.dev) — reactive frontend
- [HTMX](https://htmx.org) — server-driven interactivity
- [Tailwind CSS](https://tailwindcss.com) — styling
- Kenya's [CBC Curriculum Framework](https://kicd.ac.ke) — curriculum structure reference
