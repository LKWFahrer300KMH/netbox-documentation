from netbox.plugins import PluginMenuItem


menu_items = (
    PluginMenuItem(
        link="plugins:netbox_documentation:overview",
        link_text="Documentation",
        auth_required=True,
    ),
)
