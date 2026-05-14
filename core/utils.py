from django.core.cache import cache
import re
from django.urls import get_resolver, URLPattern, URLResolver
from datetime import datetime
import csv
from django.http import StreamingHttpResponse

current_year = datetime.now().year


def clear_object_cache(model, slug):
    cache_base_key = f"{model._meta.app_label}:{model._meta.model_name}:{slug}"

    object_instance_cache = cache.get(cache_base_key)
    if object_instance_cache:
        cache.delete(cache_base_key)


class Echo:
    """An object that implements just the write method of the file-like interface."""

    def write(self, value):
        return value


def stream_queryset_as_csv(queryset, fields=None, exclude=None, filename="export.csv"):
    """
    Returns a highly optimized StreamingHttpResponse that exports a QuerySet to CSV.
    Uses queryset.iterator() to keep memory usage near-zero.
    """
    opts = queryset.model._meta

    if fields:
        field_names = fields
    else:
        field_names = [
            field.name
            for field in opts.fields
            if not exclude or field.name not in exclude
        ]

    def stream_csv():
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)

        # Yield headers
        yield writer.writerow(field_names)

        # Yield data in chunks
        for obj in queryset.iterator(chunk_size=2000):
            row = []
            for field in field_names:
                value = getattr(obj, field)
                if callable(value):
                    try:
                        value = value()
                    except Exception:
                        value = str(value)

                if value is None:
                    row.append("")
                else:
                    row.append(str(value))
            yield writer.writerow(row)

    response = StreamingHttpResponse(stream_csv(), content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# Compile regex outside the generator for maximum loop efficiency
REGEX_CLEANUP = re.compile(r"[\^\$\?\(\):|]|\?P<.*?>")


def get_all_urls(resolver=None, prefix=""):
    if resolver is None:
        resolver = get_resolver()

    for pattern in resolver.url_patterns:
        pattern_str = str(pattern.pattern)

        if isinstance(pattern, URLResolver):
            yield from get_all_urls(pattern, prefix + pattern_str)
        elif isinstance(pattern, URLPattern):
            full_path = prefix + pattern_str

            # 1. Faster Exclusions via Membership Testing
            if any(
                x in full_path
                for x in (
                    "<",
                    ">",
                    "admin/",
                    "wagtail-admin/",
                    "__debug__/",
                    "tinymce/",
                    "_util/",
                    "documents/",
                    "media/",
                    "static/",
                )
            ):
                continue

            # Exclude backend-only authenticators
            if "3rdparty/" in full_path or "social/" in full_path:
                continue

            # 2. Strip Regex syntax from legacy/complex patterns (like your blog URL)
            clean_path = REGEX_CLEANUP.sub("", full_path)

            # 3. Ensure a clean leading slash for frontend palette usage
            if not clean_path.startswith("/"):
                clean_path = "/" + clean_path

            yield clean_path


def get_cached_urls():
    # Cache permanently; clear it only when you redeploy or change code
    return cache.get_or_set("all_urls", lambda: list(get_all_urls()), timeout=None)
