# Fixes 
1. fix `populate_menus` command in resources app to correctly populate two main menu `primary_menu` and `footer` menus, \
in the primary_menu add a menu item of `Categories` with sub menu items(its dropdown items) of the resource_types \
and also meke it that these nested menus can even show on the footer with clear indication of nesting
2. fix the search suggestion in search bar on home page to actually search based on name or description/details of resource\
currently any test returns all results showing that the q is not being appended correctly in the get request also \
upon inspection of browser xhr requests and server logs i find that the request hitting the server from htmx get is \ 
`HTTP GET /resources/?suggestions=1` without the ?q=.....

# Features to add
1.  Adding comprehensive test cases 