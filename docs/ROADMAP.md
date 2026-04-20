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

1. Excellent everything is working as expected, also on the notifications list page `AdminNotificationListView`
   there is an icon next to retry icon in actions column for failed task
   to maybe view more that does nothing when clicked, id like it to open in a modal that is professionally designed and
   modern with the details of the notification, not just for failed task but for all tasks also id like a way to delete
   notifications that are only already sent or failed the others that are pending should not be deletable also ui on
   this page and the layout and style should match what other list pages have
2. On the `AdminFileListView` page the delete modal doesn't hide even after successful deletion id like it to hide
   notification toast to show normally e.g. by doing a full page reload or redirecting back to the list page after
   action so as messages toast can show and page refreshes/ re-renders with delete modal hidden
3. You'll notice that I have a seo app with some models and django admin classes that can be inherited in other models,
   e.g. `cms.models.Page`, all models in `resources.models`, `website.models.Partner`, ensure that all models that
   inherit it utilize these fields to the maximum in forms, list pages and details pages for both the custom admin
   and the default django admin interfaces and the public rendered pages for actual maximum seo value

# Features to add

1. Switch(not replace) the python environment dependencies manager from pip to uv in Dockerfiles in root `Dockerfile`,
   `test/Dockerfile` for faster CI-CD pipelines build and final image build
2. Also on that note I'd like another check added on the CI-CD pipeline for pip-audit where pipeline fails
   even before tests run if pip-audit finds any known CVEs with fix versions on the dependencies list
3. Finally on the CI-CD pipelines id like another pipeline/action that is triggered on any tagged releases
   to build and push the image to docker hub with that release's tag
4. Run through all routes in all URLs and their respective views and ensure queries are 100% efficient and fast
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
5. Adding comprehensive test cases for all apps covering all existing or potential issues and edge cases, in views,
   models, forms integration etc. in the `test/` package of each app at a time and confirming all tests are
   comprehensive and pass 100%
