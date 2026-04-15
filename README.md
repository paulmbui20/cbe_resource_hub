# 📚 CBE Resource Hub

> A high-performance, open-source educational CMS built for Kenya's Competency-Based Education (CBC) curriculum. Enables educators, vendors, and administrators to share, discover, and manage curriculum-aligned learning materials.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.0-green)](https://djangoproject.com)

---

## ✨ Features

- **Multivendor Marketplace** — Educators can register as Content Creators and upload resources
- **CBC Curriculum Aligned** — From Pre-Primary level through Senior School (Grade 12) level, all standard learning areas
- **Custom Admin Panel** — Fully branded management UI (no Django Admin dependency)
- **Rich Text Editing** — TinyMCE (served locally, no CDN) for page and resource descriptions
- **Secure Auth** — email-only login via `django-allauth` with Google OAuth support
- **Forced Password Reset** — Admin-created users are auto-prompted to change password on first login
- **Favorites System** — HTMX-powered bookmarking without page reloads
- **Interactive DataTables** — Client-side search, sort, and pagination across all admin lists
- **Bulk User Management** — Multi-select enable/disable users with self-protection guard
- **File Storage** — Cloudflare R2 (S3-compatible) in production; local filesystem in development
- **Built-in Rate Limiting** — `django-smart-ratelimit` + `django-axes` brute-force protection
- **Performance** — Query profiling via Silk, async-ready with Django 6 ASGI
- **Global Toast Notifications** — Alpine.js system auto-fires Django messages; also JS-dispatchable from any page
- **Robust Notification System** — Async Celery-powered email delivery with retries, idempotency, and SMTP-safe rate limiting
- **Notification Dashboard** — Visualize email history, delivery status, and manual retry triggers
- **Dynamic Menus** — CMS-driven header & footer navigation, zero code changes needed
- **Contact Page** — Full form with email delivery, honeypot anti-spam, and animated responsive UI
- **Enhanced Homepage** — Live HTMX search bar with debounced suggestions dropdown, resource type card grid, compact level pills, tabbed recent/popular sections, animated intersection stats counter, and scroll-to-top FAB
- **SEO Optimization** — Pre-configured Open Graph (OG), Twitter Cards, JSON-LD structured data, and dynamic meta descriptions across all public pages
- **SEO Landing Pages** — Per resource-type detail pages (`/resources/type/<type>/`) with JSON-LD `CollectionPage` schema, breadcrumbs, pagination, and sidebar navigation
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
│   ├── apps.py
│   ├── migrations/           # folder with accounts app migration files
│   ├── models.py             # accounts models for users 
│   ├── signals.py            # signals 
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── build.sh
├── cbe_res_hub
│   ├── __init__.py
│   ├── asgi.py
│   ├── celery.py
│   ├── middleware.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── cms
│   ├── __init__.py
│   ├── admin.py
│   ├── admin_urls.py
│   ├── admin_views.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── forms.py
│   ├── management
│   │   ├── __init__.py
│   │   └── commands
│   │       ├── __init__.py
│   │       ├── populate_menus.py
│   │       └── populate_site_settings.py
│   ├── migrations/
│   ├── models.py
│   ├── signals.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── compose.yaml
├── conftest.py
├── docker-health-check.py
├── Dockerfile
├── docs
│   ├── HOMEPAGE.md
│   ├── MENUS.md
│   ├── NOTIFICATIONS.md
│   └── ROADMAP.md
├── files
│   ├── __init__.py
│   ├── admin.py
│   ├── admin_urls.py
│   ├── admin_views.py
│   ├── apps.py
│   ├── management
│   │   ├── __init__.py
│   │   └── commands
│   │       ├── __init__.py
│   │       ├── calculate_file_hashes.py
│   │       ├── check_orphaned_files.py
│   │       └── regenerate_metadata.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   ├── 0002_alter_file_file.py
│   │   ├── 0003_alter_file_file.py
│   │   └── __init__.py
│   ├── models.py
│   ├── signals.py
│   ├── tests
│   │   ├── __init__.py
│   │   ├── fixtures.py
│   │   ├── README.md
│   │   ├── test_admin.py
│   │   ├── test_integration.py
│   │   ├── test_management_commands.py
│   │   ├── test_models.py
│   │   ├── test_performance.py
│   │   └── test_validators.py
│   ├── urls.py
│   └── views.py
├── helpers
│   ├── __init__.py
│   ├── cloudflare
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── storages.py
│   └── storages
│       ├── __init__.py
│       └── mixins.py
├── LICENSE
├── manage.py
├── notifications
│   ├── __init__.py
│   ├── admin.py
│   ├── admin_views.py
│   ├── apps.py
│   ├── migrations/
│   ├── models.py
│   ├── notifier.py
│   ├── signals.py
│   ├── tasks.py
│   ├── templates
│   │   └── notifications
│   │       ├── admin
│   │       │   └── notification_list.html
│   │       ├── contact_form.html
│   │       ├── contact_form.txt
│   │       ├── email_base.html
│   │       ├── generic_message.html
│   │       ├── generic_message.txt
│   │       ├── resource_upload.html
│   │       ├── resource_upload.txt
│   │       ├── security_alert.html
│   │       ├── security_alert.txt
│   │       ├── signup_admin.html
│   │       └── signup_admin.txt
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── pyproject.toml
├── README.md
├── requirements.txt
├── resources
│   ├── __init__.py
│   ├── admin.py
│   ├── admin_dependency_views.py
│   ├── admin_urls.py
│   ├── admin_views.py
│   ├── apps.py
│   ├── forms.py
│   ├── management
│   │   ├── __init__.py
│   │   └── commands
│   │       ├── __init__.py
│   │       └── prepopulate_cbe.py
│   ├── migrations/
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── validators.py
│   └── views.py
├── seo
│   ├── __init__.py
│   ├── admin.py
│   ├── admin_views.py
│   ├── apps.py
│   ├── management
│   │   ├── __init__.py
│   │   └── commands
│   │       ├── __init__.py
│   │       ├── clean_slug_redirects.py
│   │       └── fix_circular_redirects.py
│   ├── middleware.py
│   ├── migrations/
│   │   └── __init__.py
│   ├── models.py
│   ├── static
│   │   └── admin
│   │       ├── css
│   │       │   └── seo-admin.css
│   │       └── js
│   │           └── seo-counter.js
│   ├── tests.py
│   ├── urls.py
│   ├── utils.py
│   └── views.py
├── test
│   ├── compose.yaml
│   ├── Dockerfile
│   └── test.sh
├── uv.lock
└── website
    ├── __init__.py
    ├── admin.py
    ├── admin_views.py
    ├── apps.py
    ├── bun.lock
    ├── context_processors.py
    ├── forms
    │   ├── __init__.py
    │   └── contact.py
    ├── health_checks.py
    ├── management
    │   ├── __init__.py
    │   └── commands
    │       ├── __init__.py
    │       ├── check_health.py
    │       ├── clear_all_cache.py
    │       ├── debug_backup_storage.py
    │       ├── manual_backup.py
    │       └── restore_backup.py
    ├── migrations/
    ├── models.py
    ├── package.json
    ├── sitemaps.py
    ├── static
    │   ├── css
    │   │   ├── simple-datatables.min.css
    │   │   └── src
    │   │       ├── input.css
    │   │       └── output.css
    │   ├── images
    │   │   ├── logo.svg
    │   │   └── og-default.png
    │   └── js
    │       ├── alpine-collapse.min.js
    │       ├── alpine-intersect.min.js
    │       ├── alpine.min.js
    │       ├── htmx.min.js
    │       └── simple-datatables.min.js
    ├── tasks.py
    ├── templates
    │   ├── accounts
    │   │   ├── dashboard.html
    │   │   └── profile.html
    │   ├── admin
    │   │   ├── base_admin.html
    │   │   ├── basic_list.html
    │   │   ├── contact_message_detail.html
    │   │   ├── contact_message_list.html
    │   │   ├── dashboard.html
    │   │   ├── files
    │   │   │   ├── file_list.html
    │   │   │   └── partials
    │   │   │       └── grid.html
    │   │   ├── generic_form.html
    │   │   ├── menu_list.html
    │   │   ├── page_list.html
    │   │   ├── partials
    │   │   │   ├── _delete_modal.html
    │   │   │   └── seo_panel.html
    │   │   ├── partner_list.html
    │   │   ├── resource_list.html
    │   │   ├── seo
    │   │   │   ├── audit.html
    │   │   │   ├── redirect_form.html
    │   │   │   └── redirect_list.html
    │   │   ├── seo_form.html
    │   │   ├── settings_list.html
    │   │   └── user_list.html
    │   ├── allauth
    │   │   └── layouts
    │   │       ├── base.html
    │   │       └── entrance.html
    │   ├── axes
    │   │   └── lockout.html
    │   ├── base.html
    │   ├── cms
    │   │   └── page_detail.html
    │   ├── components
    │   │   ├── container.html
    │   │   └── form.html
    │   ├── partials
    │   │   ├── _notifications.html
    │   │   └── partner_banners.html
    │   ├── resources
    │   │   ├── partials
    │   │   │   ├── basic_resource_card.html
    │   │   │   ├── favorite_button.html
    │   │   │   ├── resource_cards.html
    │   │   │   └── search_suggestions.html
    │   │   ├── resource_confirm_delete.html
    │   │   ├── resource_detail.html
    │   │   ├── resource_form.html
    │   │   ├── resource_list.html
    │   │   └── resource_type_detail.html
    │   ├── robots.txt
    │   ├── socialaccount
    │   │   └── snippets
    │   │       └── provider_list.html
    │   └── website
    │       ├── contact.html
    │       ├── home.html
    │       └── partners.html
    ├── templatetags
    │   ├── __init__.py
    │   └── model_tags.py
    ├── tests.py
    ├── urls
    │   ├── admin_urls.py
    │   └── website_urls.py
    └── views.py
```

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

```

### 4. Apply migrations

```bash
uv run python manage.py migrate
```
### 5. Prepopulate some important default settings

```bash
uv run python manage.py populate_site_settings

```
This seeds settings idempotently like: site_name, contact_phone, contact_email, google_oauth_client_id, site_indexing, meta_description.
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

> Enter your **email** when prompted (username is auto-generated). The `auto_set_admin_role` signal automatically promotesto `Role.ADMIN`.

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
| `/resources/type/<type>/`        | SEO-optimised resource type landing page                            |
| `/contact/`                      | Contact form                                                        |
| `/management/`                   | Custom admin panel (Admin/Superuser only)                           |
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

3. **Dropdown support**: Set a parent item's URL to `#`, then point child items to it. The header auto-renders them as an animated dropdown.

> Full examples and field reference: [docs/MENUS.md](./docs/MENUS.md)

---

## 🔔 Global Notification System

All `django.contrib.messages` notifications automatically display as animated toast popups on every page — no extra template code needed.

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

> **Security Note:** Users cannot self-promote to Admin. Only superusers or existing Admins can assign the Admin role via the management panel.

---

## 🛡 Authentication & Security

### Email-only Login
All authentication uses **email** as the primary identifier. Usernames are auto-generated internally and never shown to users.

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
- The `ForcePasswordChangeMiddleware` intercepts all requests for that user and redirects them to `/account/password/change/` until they comply

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

## 🖼 Template Patterns & Gotchas

### FileField / ImageField `.url` safety

Django's `ImageField` and `FileField` raise `ValueError` if you call `.url` when no file is associated (even if the field is not `None`). Always guard with `.name`:

```html
{# ❌ Wrong — raises ValueError if field is empty #}
{% if resource.featured_image %}{{ resource.featured_image.url }}{% endif %}

{# ✅ Correct #}
{% if resource.featured_image and resource.featured_image.name %}
  {{ resource.featured_image.url }}
{% endif %}
```

### HTMX live search

The homepage search bar uses HTMX partial responses. The view returns `resources/partials/search_suggestions.html` (max 6 results) when `?suggestions=1` is in the query string:

```python
# resources/views.py — ResourceListView
if self.request.GET.get('suggestions') == '1':
    self.template_name = 'resources/partials/search_suggestions.html'
```

### Animated stats counter

The stats section uses a vanilla `IntersectionObserver` (no Alpine plugin dependency) that dispatches a `animate-stats` CustomEvent on the section when it enters the viewport. Alpine listens with `@animate-stats.window` and runs the counter animation. This is more reliable than `x-intersect` because it doesn't depend on Alpine plugin loading order.


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
- [TinyMCE](https://tiny.cloud) — rich text editor
- [Alpine.js](https://alpinejs.dev) — reactive frontend
- [HTMX](https://htmx.org) — server-driven interactivity
- [Tailwind CSS](https://tailwindcss.com) — styling
- Kenya's [CBC Curriculum Framework](https://kicd.ac.ke) — curriculum structure reference
