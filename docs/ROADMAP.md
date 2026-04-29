# Points to note

* Most of the views related to the custom admin are in the `admin_views.py` file of each application,
  with their corresponding URLs available in the `admin_urls.py`
* Most public facing views for public routes like `/`, `/resources` etc. are found in the `views.py` file of each app
  and their URLs in the regular `urls.py` file -> this is the general case, but it's not 100%
* Nearly all templates are found the directory `website/templates` and are grouped into sub folders based on respective
  apps they belong to this was an architectural mistake, but it's fine since what matters is that they reside in a
  `templates` directory, I plan to untangle this in future not now
* The current CI-CD pipelines and actions can be found in the `.github/workflows/ci-cd.yml`

# Fixes


# Completed Features

1. **Implemented robust test suite** covering integration, settings, and full CRUD.
2. **Setup production-grade CI/CD pipelines** (`ci-cd.yml`, `release.yml`) separating branch tests from tag releases.
3. **Query Optimization & Caching**
   * Performed a route-by-route audit eliminating all N+1 queries.
   * Reduced homepage queries from 16 to 4 (cold cache) / 1 (warm cache) via aggregation and cache invalidation signals.
   * Centralised and optimized reference caching (`resources/cache.py`) to reduce memory and eliminate stale lazy querysets.
