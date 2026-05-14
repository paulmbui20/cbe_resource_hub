import csv
from django.http import StreamingHttpResponse

class Echo:
    """An object that implements just the write method of the file-like interface."""

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

def export_as_csv_action(description="Export selected to CSV", fields=None, exclude=None):
    """
    Returns a highly optimized Django admin action that exports a QuerySet to CSV.
    Uses StreamingHttpResponse and queryset.iterator() to keep memory usage 
    constant and near-zero, even when exporting millions of records.
    """

    def export_as_csv(modeladmin, request, queryset):
        opts = modeladmin.model._meta

        # Determine which fields to export
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

            # Yield headers first
            yield writer.writerow(field_names)

            # Yield data in chunks, avoiding loading everything into RAM at once
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
                        # Convert robustly to string to handle dates, uuids, custom types
                        row.append(str(value))
                yield writer.writerow(row)

        response = StreamingHttpResponse(stream_csv(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{opts.verbose_name_plural}.csv"'
        return response

    export_as_csv.short_description = description
    return export_as_csv
