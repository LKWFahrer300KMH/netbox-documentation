import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("contenttypes", "0002_remove_content_type_name")]
    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("object_id", models.PositiveBigIntegerField()),
                ("object_label", models.CharField(max_length=255)),
                ("body", models.TextField(blank=True)),
                ("source_comments_sha256", models.CharField(max_length=64, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("content_type", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="contenttypes.contenttype")),
            ],
            options={"ordering": ("-updated_at", "-pk")},
        ),
        migrations.CreateModel(
            name="DocumentImage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("data", models.BinaryField()),
                ("alt_text", models.CharField(blank=True, max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="netbox_documentation.document")),
            ],
        ),
        migrations.AddConstraint(
            model_name="document",
            constraint=models.UniqueConstraint(fields=("content_type", "object_id"), name="documentation_unique_object"),
        ),
    ]
