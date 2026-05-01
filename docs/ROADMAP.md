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
1. id like fully fledged blog features  like Wordpresses to be added to the project using the waigtail latest version and ensure to follw the esisting coding standards and style of the project, media resources for waigtail should be stored in the "public_files" storage. use the waigtail documentation to implement the blog features and ensure that the blog features are well documented. and add afew recent blogs cards on the home page, add/customize a page for all blogs that will be acessible by all users, and an admin page for managing blogs. and a single blog page for reading blogs. all should be in the website, all these should be consistent with the overall theme and design of the website.

# Completed Features

