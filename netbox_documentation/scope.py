from django.apps import apps
from django.core.exceptions import FieldDoesNotExist, PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404
from netbox.plugins import get_plugin_config


def supported_models():
    labels = get_plugin_config("netbox_documentation", "models")
    result = {}
    for label in labels:
        try:
            model = apps.get_model(label)
            model._meta.get_field("comments")
        except (LookupError, ValueError, FieldDoesNotExist):
            continue
        if model._meta.app_label == "netbox_documentation":
            continue
        result[model._meta.label_lower] = model
    return result


def object_for_user(user, label, pk, action="view"):
    model = supported_models().get(label.lower())
    if model is None:
        raise Http404("Unsupported NetBox object")
    queryset = model.objects.restrict(user, action)
    return get_object_or_404(queryset, pk=pk)


def can_edit(user, obj):
    if not user.has_perm("netbox_documentation.change_document"):
        return False
    return obj.__class__.objects.restrict(user, "change").filter(pk=obj.pk).exists()


def require_edit(user, obj):
    if not can_edit(user, obj):
        raise PermissionDenied
