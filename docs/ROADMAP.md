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


# Features to add


1. Finally on the CI-CD pipelines id like another pipeline/action that is triggered on any tagged releases
   to build and push the image to docker hub with that release's tag
2. Run through all routes in all URLs and their respective views and ensure queries are 100% efficient and fast
   eliminating any n+1 issue that I may have missed for both public facing routes and the custom admin views,
   and adding efficient caching strategies that are easy to work with or modify in future and updating documentation,
   e.g.
   the home page (/) route has 16 queries it may not have n+1 problem but all those queries are an issue, so
   optimization on all pages should be as follows:
   i) reduce number of db queries as much as possible without caching first then
   ii) after the reduced queries cache responses appropriately and efficiently and avoid bad cache policies like caching
   entire HTML page or lack of reliable invalidation strategies, I already have some caching in place for public facing
   pages like those in the `/resources/....` routes where the side objects like grades, education level are cached..
   build based on that, but you are free to **suggest** any corrections

