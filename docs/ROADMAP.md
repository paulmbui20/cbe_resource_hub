# Fixes 
1. 


# Features to add
1. adding sidebar to the custom admin dashboard on the right
2. adding custom admin logic and interface for files (Files app with File model) management just like in WordPress
3. adding custom admin logic for seo management just like in slug redirects and seo model 
4. 
5. adding custom admin pages and logics to manage CRUD for partners(Partner model from website app), also show the partners if they exist as barners if they have the (show_as_burner) flag turned on, on website showed professionally \
like ads in a minimalistic way that's non-intrusive and doesn't destroy ux, also there should be a public page lising them 
6. add validators file type based on file magic and signature not just file name for ResourceItem model and enhance existing validators 
7. A robust notification system preferably in its own app that exposes tasks (function) that can be called when events happen \
to que/send and email via **CELERY** to the admin, when important events happen like signup, contact form submission, resource item upload etc., notifications, \
notifications should be fault-tolerant with retry logic, but be safe such that they don't max out the SMTP limits
8. Initializing pytest correctly and adding comprehensive test cases 