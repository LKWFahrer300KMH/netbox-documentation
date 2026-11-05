import hashlib
import json

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from netbox_documentation.models import Document
from netbox_documentation.scope import supported_models


class Command(BaseCommand):
    help = "Copy NetBox comments to documentation; never changes or clears comments. Default is a dry run."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Create missing documents")
        parser.add_argument("--model", action="append", help="Limit to model label; repeatable")
        parser.add_argument("--object-id", type=int, help="Limit to one object (requires one --model)")

    def handle(self, *args, **options):
        supported = supported_models()
        labels = options["model"] or list(supported)
        if unknown := set(labels) - set(supported):
            raise CommandError(f"Unsupported models: {', '.join(sorted(unknown))}")
        if options["object_id"] and len(labels) != 1:
            raise CommandError("--object-id requires exactly one --model")
        totals = {"scanned": 0, "with_comments": 0, "copied": 0, "existing": 0}
        per_model = {}
        for label in labels:
            model = supported[label]
            content_type = (
                ContentType.objects.get_for_model(model)
                if options["apply"]
                else ContentType.objects.filter(
                    app_label=model._meta.app_label,
                    model=model._meta.model_name,
                ).first()
            )
            queryset = model.objects.exclude(comments__isnull=True).exclude(comments="")
            if options["object_id"]:
                queryset = queryset.filter(pk=options["object_id"])
            counts = {"with_comments": 0, "copied": 0, "existing": 0}
            for obj in queryset.iterator(chunk_size=200):
                totals["scanned"] += 1
                if not obj.comments.strip():
                    continue
                totals["with_comments"] += 1
                counts["with_comments"] += 1
                values = {
                    "object_label": str(obj)[:255],
                    "body": obj.comments,
                    "source_comments_sha256": hashlib.sha256(obj.comments.encode("utf-8")).hexdigest(),
                }
                if options["apply"]:
                    _, created = Document.objects.get_or_create(
                        content_type=content_type, object_id=obj.pk, defaults=values
                    )
                else:
                    created = content_type is None or not Document.objects.filter(
                        content_type=content_type, object_id=obj.pk
                    ).exists()
                field = "copied" if created else "existing"
                counts[field] += 1
                totals[field] += 1
            per_model[label] = counts
        self.stdout.write(json.dumps({
            **totals,
            "dry_run": not options["apply"],
            "comments_changed": 0,
            "models": per_model,
        }, ensure_ascii=False))
