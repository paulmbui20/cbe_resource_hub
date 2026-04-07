# files/migrations/0002_alter_file_file.py
# Replace the entire content of this file with:

from django.db import migrations, models
import files.models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0002_alter_file_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='file',
            field=models.FileField(
                storage=files.models.PublicFilesStorageCallable(),
                upload_to=files.models.file_upload_path
            ),
        ),
    ]