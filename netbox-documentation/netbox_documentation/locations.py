import re

from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import strip_tags


def site_for_object(obj, depth=0):
    """Use NetBox relationships, never infer a site from a hostname."""
    if obj is None or depth > 3:
        return None
    if obj._meta.label_lower == "dcim.site":
        return obj
    try:
        site = getattr(obj, "site", None)
        if site:
            return site

        # Application Services have one parent: a device, VM or FHRP group.
        if obj._meta.label_lower == "ipam.service":
            return site_for_object(getattr(obj, "parent_object", None), depth + 1)

        # A VM can inherit its site from its host device or cluster.
        if obj._meta.label_lower == "virtualization.virtualmachine":
            for field in ("device", "cluster"):
                site = site_for_object(getattr(obj, field, None), depth + 1)
                if site:
                    return site

        # Prefixes, VLANs and clusters may be scoped directly to a site.
        if obj._meta.label_lower in {"ipam.prefix", "ipam.vlan", "virtualization.cluster"}:
            scope = getattr(obj, "scope", None)
            if scope is not None:
                return site_for_object(scope, depth + 1)

        if obj._meta.label_lower == "ipam.ipaddress":
            assigned = getattr(obj, "assigned_object", None)
            for field in ("device", "virtual_machine"):
                site = site_for_object(getattr(assigned, field, None), depth + 1) if assigned else None
                if site:
                    return site
    except (ObjectDoesNotExist, AttributeError):
        return None
    return None


def plain_excerpt(markdown_text, limit=190):
    text = re.sub(r"\[\[(?:image|attachment):[^\]]+\]\]", "", markdown_text)
    text = strip_tags(text)
    text = re.sub(r"(?m)^\s*(?:#{1,6}\s+|[-*+]\s+|>\s+)", "", text)
    text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[*_`|]+", " ", text)
    text = " ".join(text.split())
    return text[:limit].rstrip() + ("…" if len(text) > limit else "")
