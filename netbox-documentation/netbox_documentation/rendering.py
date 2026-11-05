import re
import uuid

from django.urls import reverse
from django.utils.html import format_html, format_html_join
from utilities.templatetags.builtins.filters import render_markdown


# A standalone image line can be moved freely among existing Markdown blocks.
IMAGE_LINE = re.compile(
    r"(?m)^[ \t]*\[\[(?:image:([0-9a-fA-F-]{36})|attachment:([0-9]+))\]\][ \t\r]*$"
)


def render_document(body, plugin_images=(), native_images=()):
    images = {str(item.pk): item for item in plugin_images}
    attachments = {str(item.pk): item for item in native_images}
    fragments = []
    cursor = 0
    for match in IMAGE_LINE.finditer(body):
        if match.start() > cursor:
            fragments.append(render_markdown(body[cursor:match.start()]))
        plugin_id, native_id = match.groups()
        if plugin_id:
            try:
                item = images.get(str(uuid.UUID(plugin_id)))
            except ValueError:
                item = None
            if item:
                url = reverse("plugins:netbox_documentation:image", kwargs={"image_id": item.pk})
                alt_text = item.alt_text
            else:
                url = None
        else:
            item = attachments.get(native_id)
            if item:
                url = reverse(
                    "plugins:netbox_documentation:native_image",
                    kwargs={"attachment_id": item.pk},
                )
                alt_text = item.name
            else:
                url = None
        if url:
            fragments.append(format_html(
                '<figure class="mb-4"><img class="img-fluid rounded border" '
                'loading="lazy" src="{}" alt="{}"><figcaption class="small text-muted mt-1">{}</figcaption></figure>',
                url, alt_text, alt_text,
            ))
        else:
            fragments.append(format_html("<p>Image is no longer available.</p>"))
        cursor = match.end()
    if cursor < len(body):
        fragments.append(render_markdown(body[cursor:]))
    return format_html_join("", "{}", ((fragment,) for fragment in fragments))
