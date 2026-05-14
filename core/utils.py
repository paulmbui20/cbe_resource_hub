from datetime import datetime
import csv
from django.core.cache import cache
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
