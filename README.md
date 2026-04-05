# 📚 CBE Resource Hub

> A high-performance, open-source educational CMS built for Kenya's Competency-Based Education (CBC) curriculum. Enables educators, vendors, and administrators to share, discover, and manage curriculum-aligned learning materials.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Django](https://img.shields.io/badge/Django-6.0-green)](https://djangoproject.com)

---

## ✨ Features

- **Multi-vendor Marketplace** — Educators can register as Content Creators and upload resources
- **CBC Curriculum Aligned** — Pre-Primary through Senior School (Grade 12), all standard learning areas
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

---

## 🗂 Project Structure

```
cbe_resource_hub/
├── accounts/           # Custom user model, adapters, signals
├── cms/                # Pages, Menus, SiteSettings models
├── resources/          # EducationLevel, Grade, LearningArea, ResourceItem
│   └── management/
│       └── commands/
│           └── prepopulate_cbe.py   # Seed Kenyan CBC curriculum
├── website/            # Public views, admin views, admin URLs
│   ├── admin_views.py
│   ├── admin_dependency_views.py
│   └── templates/
│       ├── base.html
│       ├── admin/          # Custom management panel templates
│       └── resources/      # Public-facing resource templates
├── cbe_res_hub/        # Project settings, URLs, middleware, WSGI/ASGI
│   ├── settings.py
│   ├── middleware.py   # ForcePasswordChangeMiddleware
│   └── urls.py
├── .env                # Secret keys and credentials (NOT committed)
├── manage.py
└── pyproject.toml      # Dependencies managed by uv
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- **PostgreSQL** (recommended) or SQLite for development
- **Redis** (optional, for Celery task queue)

### 1. Clone the repository

```bash
git clone https://github.com/yourorg/cbe_resource_hub.git
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

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
# ── Django Core ──────────────────────────────────────────────
SECRET_KEY=your-very-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# ── Database ─────────────────────────────────────────────────
# SQLite (development — default if DATABASE_URL not set)
# DATABASE_URL=sqlite:///db.sqlite3

# PostgreSQL (recommended for production)
DATABASE_URL=postgres://user:password@localhost:5432/cbe_resource_hub

# ── Email ─────────────────────────────────────────────────────
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# For production:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your@email.com
# EMAIL_HOST_PASSWORD=your-app-password

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

# ── Redis / Celery (optional) ─────────────────────────────────
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
```

### 4. Apply migrations

```bash
uv run python manage.py migrate
```

### 5. Seed the Kenyan CBC curriculum

This is a one-time idempotent command. Safe to run multiple times.

```bash
uv run python manage.py prepopulate_cbe
```

This seeds:
- **5 Education Levels**: Pre-Primary, Lower Primary, Upper Primary, Junior School, Senior School
- **14 Grades**: PP1–PP2, Grade 1–12
- **30+ Learning Areas**: aligned to each education level per CBC 2026 framework

### 6. Create a superuser (Admin)

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

| URL | Description |
|-----|-------------|
| `/` | Public homepage with resource browser |
| `/resources/` | Searchable resource catalogue |
| `/management/` | Custom admin panel (Admin/Superuser only) |
| `/accounts/login/` | Email login page |
| `/accounts/signup/` | Registration |
| `/accounts/social/login/google/` | Google OAuth entry |
| `/account/password/change/` | Password change (forced on first admin-created login) |

---

## 👤 User Roles

| Role | Permissions |
|------|------------|
| **Standard User** | Browse & download resources, manage favourites |
| **Vendor/Creator** | All of the above + upload and manage own resources |
| **Admin** | Full management panel access: CRUD for users, pages, resources, menus, settings, curriculum |
| **Superuser** | All Admin permissions + Django internals access |

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

---

## 🎨 Frontend Stack

| Technology | Purpose |
|-----------|---------|
| **Tailwind CSS v4** | Utility-first styling |
| **Alpine.js** | Reactive UI (modals, bulk actions, dropdowns) |
| **HTMX** | Server-driven interactivity (favourites, partial updates) |
| **TinyMCE** (local) | Rich text editor, served from static files — no CDN |
| **simple-datatables** (local) | Client-side sort/search/paginate — no CDN |

---

## ⚙️ Management Commands

```bash
# Seed Kenyan CBC curriculum (idempotent)
uv run python manage.py prepopulate_cbe

# Standard Django commands
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py collectstatic

# Run tests
uv run python manage.py test
```

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
