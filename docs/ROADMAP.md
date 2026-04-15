# Fixes 
1. excelent everything is working as expected

also on that page there is an icon next to retry icon in actions column for failed task to maybe view more that does nothing when clicked, id like it to open in a modal that is professionally designed and moderdn with the details of the notification

aslo id like a way to delete notifications that are only already sent or failed the others that are pending should not be deletable untill

also ui on this page and the layout and style should match what other list pages have


# Features to add
1.  Run through all routes in all urls and their respective views and ensure queries are 100% efficient and fast eliminating any n+1 issue and \
and adding efficient caching strategies that are easy to work with or modify in future and updating documentation, eg the home page (/) route has 21 queries it may not have n+1 problem but all those queries are an issue, so optimization on all pages should be as follows:
i) reduce number of db queries as much as possible without caching
ii) after the reduced queries cache responses appropriately and efficiently and avoid bad cache policies like caching entire html page or lack of reliable invalidation strategies
2. Adding comprehensive test cases for all apps covering all existing or potential issues and edge cases