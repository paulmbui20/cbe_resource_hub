# seo/middleware.py

import logging

from django.core.cache import cache
from django.http import HttpResponsePermanentRedirect
from django.urls import resolve, Resolver404

from cbe_res_hub.settings import CACHE_TIMEOUT
from seo.models import SlugRedirect

logger = logging.getLogger(__name__)


class SlugRedirectMiddleware:
    """
    Middleware to handle slug redirects with caching for performance.

    - Checks BOTH 404 responses AND successful responses with old slugs
    - Returns 301 permanent redirect if slug has changed
    - Caches redirect lookups for blazingly fast performance
    """

    # Views that use slug-based URLs
    SLUG_VIEWS = {
        'resources:resource_detail',
        'resources:learning_area_details',
        'resources:grade_details',
        'resources:education_level_details',
        'cms:page_detail',

    }

    # Cache timeout: 28 days (redirects rarely change once created)
    CACHE_TIMEOUT = CACHE_TIMEOUT

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # IMPORTANT: Check for redirects BEFORE processing the request
        # This prevents cached data from being returned for old slugs
        redirect_url = self._check_for_redirect(request)
        if redirect_url:
            logger.info(f"Slug redirect (pre-request): {request.path} → {redirect_url}")
            return HttpResponsePermanentRedirect(redirect_url)

        response = self.get_response(request)

        # Also handle 404 responses (fallback)
        if response.status_code == 404:
            redirect_url = self._check_for_redirect(request)
            if redirect_url:
                logger.info(f"Slug redirect (404): {request.path} → {redirect_url}")
                return HttpResponsePermanentRedirect(redirect_url)

        return response

    def _check_for_redirect(self, request):
        """
        Check if this request should be redirected.
        Returns new URL or None.
        """
        try:
            # Try to resolve the URL pattern
            match = resolve(request.path_info)
            view_name = match.view_name

            # Only process slug-based views
            if view_name not in self.SLUG_VIEWS:
                return None

            # Extract slug from URL
            old_slug = match.kwargs.get('slug')
            if not old_slug:
                return None

            # Check cache first
            cache_key = f'slug_redirect_{old_slug}'
            new_slug = cache.get(cache_key)

            if new_slug is None:
                # Cache miss - check database
                new_slug = SlugRedirect.get_redirect(old_slug)

                if new_slug:
                    # Cache the redirect
                    cache.set(cache_key, new_slug, self.CACHE_TIMEOUT)
                else:
                    # Cache the miss to avoid repeated DB queries
                    cache.set(cache_key, '', 60 * 5)  # 5 minutes
                    return None
            elif new_slug == '':
                # Cached miss
                return None

            # We have a redirect - build new URL
            from django.urls import reverse
            new_url = reverse(view_name, kwargs={'slug': new_slug})

            # Preserve query string
            if request.GET:
                query_string = request.GET.urlencode()
                new_url = f"{new_url}?{query_string}"

            return new_url

        except Resolver404:
            # URL pattern doesn't match at all
            return None
        except Exception as e:
            # Log errors but don't break the site
            logger.error(f"Error in SlugRedirectMiddleware: {e}", exc_info=True)
            return None
