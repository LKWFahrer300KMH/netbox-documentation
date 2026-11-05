# NetBox Documentation

Markdown documentation with inline images for NetBox objects. A **Documentation** button opens a dedicated page, keeping long procedures off the object's main page. A plugin overview lists documented objects, searchable by name/content and grouped by NetBox site.

Test with a staging NetBox instance before using it in production.

## Compatibility

- NetBox 4.5.2–4.5.x and Python 3.12. Other versions have not been verified.
- Supported by default: devices, virtual machines, services, sites, racks, locations, clusters, IP addresses, prefixes, VLANs, and circuits. Only configured models with a NetBox `comments` field are enabled.
- NetBox's Python environment needs Pillow for image processing.

## Features

- Markdown editor with formatting toolbar and live preview.
- Drag and drop, paste, or upload PNG/JPEG/WebP images (8 MB input limit); newly uploaded images are stored as PNG in the NetBox database.
- Insert existing NetBox image attachments without copying or deleting them.
- Image links require an authenticated NetBox user with view access to the parent object. Editing requires both `netbox_documentation.change_document` and change access to that object.
- Site grouping follows NetBox relationships. Objects without a known site appear under **No site**.
- Optional, explicit import copies existing comments into missing documentation entries. It does not clear or modify comments.

## Install

Install the package into the **same Python environment** as NetBox. This source repository has not been published to PyPI.

```sh
git clone https://github.com/LKWFahrer300KMH/netbox-documentation.git
/opt/netbox/venv/bin/python -m pip install ./netbox-documentation
```

For netbox-docker, add this repository to the image build context and install it in the image, for example:

```dockerfile
COPY ./netbox-documentation /opt/netbox-documentation
RUN /usr/local/bin/uv pip install --python /opt/netbox/venv/bin/python /opt/netbox-documentation
```

Enable the plugin in your NetBox configuration (for netbox-docker, commonly `configuration/plugins.py`):

```python
PLUGINS = ["netbox_documentation"]
```

If you already have other plugins, add `netbox_documentation` to the existing list. Rebuild the image or reinstall the package, then run `manage.py migrate`, restart the NetBox services, and check the **Plugins → Documentation** page. Keep the same plugin installed in all NetBox application and worker images.

The NetBox administrator chooses which **object types** get the Documentation button using `PLUGINS_CONFIG`. The default list is shown above. To limit it, set `models` to the NetBox model labels you want:

```python
PLUGINS_CONFIG = {
    "netbox_documentation": {
        "models": ("dcim.device", "virtualization.virtualmachine", "ipam.service"),
    },
}
```

This example enables documentation for devices, VMs, and services only. Other supported models can be added to the tuple; a model needs a NetBox `comments` field. A change to this setting takes effect after a restart. It does not delete existing documents, but documents for disabled models will no longer be available through this plugin until the model is enabled again. Regular users cannot change this administrator setting in the UI; their ability to view or edit a document is governed by NetBox object permissions.

## Copy existing comments

In the NetBox environment, after migrations:

```sh
/opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py import_documentation
/opt/netbox/venv/bin/python /opt/netbox/netbox/manage.py import_documentation --apply
```

The first command is a dry run. `--apply` creates documents only for objects that have comments and no existing document; **it never deletes or clears NetBox comments**. Repeatable `--model dcim.device` and optional `--object-id 123` can narrow the import.

The editor stores Markdown. Click an attached image to insert its `[[attachment:123]]` marker, or upload an image to insert `[[image:UUID]]`. Place each marker on its own line to render it inline. Existing attachments remain managed by NetBox.

## Access and limitations

Documentation visibility follows the linked object's NetBox view permission. Editing additionally needs `netbox_documentation.change_document` and change permission for the linked object. The overview searches bodies visible to the user. Image uploads are held in the NetBox database; plan database backups and storage accordingly.

The supplied unit tests cover image marker recognition. A staging installation and manual UI checks are still required to verify integration with your NetBox version and configuration.

```sh
python -m unittest discover -s tests -v
```

## Maintainer notes

The public author name `LKWFahrer_300KMH` is a display name; it need not match the GitHub account name. Review the Apache-2.0 license choice and ensure you have the right to publish all included code. Do not commit local NetBox configuration, database dumps, image uploads, or secrets.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
