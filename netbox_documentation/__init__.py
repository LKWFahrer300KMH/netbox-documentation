from netbox.plugins import PluginConfig


class DocumentationConfig(PluginConfig):
    name = "netbox_documentation"
    verbose_name = "Documentation"
    description = "Markdown documentation with inline images for NetBox objects"
    author = "LKWFahrer_300KMH"
    version = "0.3.0"
    base_url = "documentation"
    min_version = "4.5.2"
    max_version = "4.5.99"
    default_auto_field = "django.db.models.BigAutoField"
    default_settings = {
        "models": (
            "dcim.device",
            "virtualization.virtualmachine",
            "ipam.service",
            "dcim.site",
            "dcim.rack",
            "dcim.location",
            "virtualization.cluster",
            "ipam.ipaddress",
            "ipam.prefix",
            "ipam.vlan",
            "circuits.circuit",
        ),
    }


config = DocumentationConfig
