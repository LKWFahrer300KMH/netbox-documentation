from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from netbox.plugins import PluginTemplateExtension

from .models import Document
from .scope import supported_models


class DocumentationButton(PluginTemplateExtension):
    def buttons(self):
        obj = self.context.get("object")
        if not obj or obj._meta.label_lower not in supported_models():
            return ""
        user = self.context["request"].user
        if not obj.__class__.objects.restrict(user, "view").filter(pk=obj.pk).exists():
            return ""
        has_doc = Document.objects.filter(
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
        ).exists()
        url = reverse(
            "plugins:netbox_documentation:detail",
            kwargs={"model": obj._meta.label_lower, "pk": obj.pk},
        )
        return self.render(
            "netbox_documentation/button.html",
            extra_context={"documentation_url": url, "documentation_exists": has_doc},
        )


template_extensions = [DocumentationButton]
