import json
from django.db import migrations
import wagtail.fields
import wagtail.blocks


def convert_to_streamfield(apps, schema_editor):
    BlogPage = apps.get_model("website", "BlogPage")
    for page in BlogPage.objects.all():
        if page.body_old:
            # We must set the value as a list of dicts for StreamField
            page.body = [{"type": "paragraph", "value": page.body_old}]
            page.save()


def convert_to_richtext(apps, schema_editor):
    BlogPage = apps.get_model("website", "BlogPage")
    for page in BlogPage.objects.all():
        if page.body:
            # Extract content from paragraph blocks
            content = ""
            # Note: page.body might be a string (JSON) or list depending on state
            body_data = page.body
            if isinstance(body_data, str):
                try:
                    body_data = json.loads(body_data)
                except Exception:
                    body_data = []

            for block in body_data:
                if block.get("type") == "paragraph":
                    content += block.get("value", "")
            page.body_old = content
            page.save()


class Migration(migrations.Migration):
    dependencies = [
        (
            "website",
            "0021_blogauthor_slug_blogpage_main_image_alt_blogcategory_and_more",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="blogpage",
            old_name="body",
            new_name="body_old",
        ),
        migrations.AddField(
            model_name="blogpage",
            name="body",
            field=wagtail.fields.StreamField(
                [("paragraph", 0), ("table", 1)],
                blank=True,
                block_lookup={
                    0: (
                        "wagtail.blocks.RichTextBlock",
                        (),
                        {
                            "features": [
                                "h1",
                                "h2",
                                "h3",
                                "h4",
                                "h5",
                                "h6",
                                "bold",
                                "italic",
                                "blockquote",
                                "ol",
                                "ul",
                                "hr",
                                "link",
                                "image",
                                "embed",
                            ]
                        },
                    ),
                    1: ("wagtail.contrib.table_block.blocks.TableBlock", (), {}),
                },
                null=True,
                use_json_field=True,
            ),
        ),
        migrations.RunPython(convert_to_streamfield, convert_to_richtext),
        migrations.RemoveField(
            model_name="blogpage",
            name="body_old",
        ),
    ]
