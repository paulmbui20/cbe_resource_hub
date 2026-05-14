# Points to note

* Settings for the project are in the `settings/` package and are grouped into different environments based on the `ENVIRONMENT` environment variable.
* Currently local development uses the `settings/development.py` and production uses the `settings/production.py`, testing uses the `settings/testing.py`. 
* Most of the views related to the custom admin are in the `admin_views.py` file of each application,
  with their corresponding URLs available in the `admin_urls.py`
* Most public facing views for public routes like `/`, `/resources` etc. are found in the `views.py` file of each app
  and their URLs in the regular `urls.py` file -> this is the general case, but it's not 100%
* Nearly all templates are found the directory `website/templates` and are grouped into sub folders based on respective
  apps they belong to this was an architectural mistake, but it's fine since what matters is that they reside in a
  `templates` directory, I plan to untangle this in future not now
* The current CI-CD pipelines and actions can be found in the `.github/workflows/ci-cd.yml`, and the `.github/workflows/release.yml`

# Fixes

1.

# Completed Features

1. Dynamic Comment System (HTMX + Alpine.js) for Blog
   * Secure SPA-like interactive comments.
   * Built-in honeypot spam protection.
   * Fully decoupled components logic for future reuse on resource details pages.
