# Fixes 
1. 


# Features to add
1. adding sidebar to the custom admin dashboard on the right
2. adding custom admin logic and interface for files (Files app with File model) management just like in WordPress
3. adding custom admin logic for seo management from (seo app SlugRedirect and SEO model) like in slug redirects and seo model 
4. 
5. adding custom admin pages and logics to manage CRUD for partners(Partner model from website app), also show the partners if they exist as barners if they have the (show_as_burner) flag turned on, on website showed professionally \
like ads in a minimalistic way that's non-intrusive and doesn't destroy ux, also there should be a public page lising them 
6. add validators file type based on file magic and signature not just file name for ResourceItem model and enhance existing validators 
7. A robust notification system preferably in its own app that exposes tasks (function) that can be called (function should be very easy to  work with and be well documented) when events happen \
to que/send and email via **CELERY** to the admin, when important events happen like signup, attempted bruteforce(axes timeout), contact form submission, resource item upload etc., notifications, \
notifications should be fault-tolerant with idempotency retry logic, but be safe such that they don't max out the SMTP limits, with  custom admin ui to visualize and trigger retry etc.
8. ✅ enhance the homepage to make it more informative and professional and modern — implemented live search (HTMX), resource type cards with SEO detail pages, compact level pills, tabbed recent/popular resources, IntersectionObserver animated stats, why-us section, subtle partners section, and scroll-to-top FAB.
9.  make it easy to add menus and menu types with existing hardcoded on html form in select input fields containing specific values as accepted by the db and template system for footer and main navbar etc, that can be edited, without messing with current logic, and also make it easy to add settings a breeze as well eg sitename, contact email and phone and social media links, and google_oauth_client_id that are all used by the web app or its templates.. it should also be easy to add on to this hardcoded values(when i say easy i mean like in wordpress admin panel settings), and add a setting in select input with hardcoded valued to enable toggling site indexing by search engines wich is actually implemeted in base.html metatags and robots.txt

10.  Adding comprehensive test cases 