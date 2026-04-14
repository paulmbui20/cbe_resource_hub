# Fixes 
1. fix issues with tables in lists pages of custom admin pages where datatables seems to be broken, \
and ensure they are responsive while showing a bit more important info, by making them be responsive (scrollable horizontally)
2. fix layout and other ui bugs issues in notifications list page
3. fix the `ResourceTypeSitemap` class in `website/sitamamp.py` to ensure no n+1 queries while maintaining the initial desired output
4. fix the tinymce5 field to be responsive (scrollable horizontally) in (page, resource(both for vendors and admins), and partner) add and edit 

# Features to add
1.  Run through all routes in all urls and their respective views and ensure queries are 100% efficient and fast eliminating any n+1 issue and \
and adding efficient caching strategies that are easy to work with or modify in future and updating documentation
2. Adding comprehensive test cases for all apps covering all existing or potential issues and edge cases