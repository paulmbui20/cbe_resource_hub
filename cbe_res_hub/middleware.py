import re
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class DisableBrowserCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"

        return response


class ForcePasswordChangeMiddleware:
    """
    Middleware to force users with must_change_password=True to change their password.
    Redirects them to the password change view unless they are already on it or logging out.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        if getattr(request.user, "must_change_password", False):
            # Allow access to password change, logout, and static paths so they are not infinitely looped
            exempt_urls = [
                reverse('account_change_password'),
                reverse('account_logout'),
            ]

            # Using raw path to handle prefix issues
            path = request.path

            # Allow static files and internal django paths just in case
            if path.startswith(settings.STATIC_URL) or path.startswith(settings.MEDIA_URL):
                return self.get_response(request)

            if path not in exempt_urls:
                # Add a message once? Django messages middleware might spam if every request redirects
                return redirect('account_change_password')

        return self.get_response(request)
