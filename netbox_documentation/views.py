import mimetypes
from collections import Counter
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from PIL import Image, ImageOps, UnidentifiedImageError
from extras.models import ImageAttachment

from .locations import plain_excerpt, site_for_object
from .models import Document, DocumentImage
from .rendering import render_document
from .scope import can_edit, object_for_user, require_edit, supported_models


def _document(obj):
    content_type = ContentType.objects.get_for_model(obj)
    return Document.objects.filter(content_type=content_type, object_id=obj.pk).first()


def _context(obj, doc):
    kwargs = {"model": obj._meta.label_lower, "pk": obj.pk}
    return {
        "target": obj,
        "target_type": obj._meta.verbose_name.title(),
        "target_model": obj._meta.label_lower,
        "document": doc,
        "doc_url": reverse("plugins:netbox_documentation:detail", kwargs=kwargs),
        "edit_url": reverse("plugins:netbox_documentation:edit", kwargs=kwargs),
        "upload_url": reverse("plugins:netbox_documentation:upload", kwargs=kwargs),
        "preview_url": reverse("plugins:netbox_documentation:preview", kwargs=kwargs),
    }


def _native_images(obj):
    relation = getattr(obj, "images", None)
    if relation is None:
        return []
    return list(relation.only("id", "name").order_by("name", "id"))


def _native_image_rows(images):
    return [{
        "image": item,
        "token": f"[[attachment:{item.pk}]]",
        "url": reverse(
            "plugins:netbox_documentation:native_image",
            kwargs={"attachment_id": item.pk},
        ),
    } for item in images]


def _plugin_images(doc):
    return (
        doc.images.only("id", "document_id", "alt_text", "created_at").order_by("created_at")
        if doc else ()
    )


@login_required
@require_GET
def overview(request):
    options = supported_models()
    selected = request.GET.get("type", "")
    if selected not in options:
        selected = ""
    condition = Q(pk__in=[])
    for label, model in options.items():
        if selected and label != selected:
            continue
        visible_ids = model.objects.restrict(request.user, "view").values("pk")
        condition |= Q(
            content_type=ContentType.objects.get_for_model(model),
            object_id__in=visible_ids,
        )
    documents = Document.objects.filter(condition).select_related("content_type")
    query = request.GET.get("q", "").strip()[:150]
    if query:
        documents = documents.filter(
            Q(object_label__icontains=query) | Q(body__icontains=query)
        )
    rows = []
    for doc in documents.prefetch_related("content_object"):
        obj = doc.content_object
        if obj is None:
            continue
        site = site_for_object(obj)
        rows.append({
            "doc": doc,
            "object": obj,
            "type": obj._meta.verbose_name.title(),
            "site": site,
            "site_key": str(site.pk) if site else "none",
            "site_name": str(site) if site else "No site",
            "excerpt": plain_excerpt(doc.body),
            "url": reverse(
                "plugins:netbox_documentation:detail",
                kwargs={"model": obj._meta.label_lower, "pk": obj.pk},
            ),
        })
    site_counts = Counter(row["site_key"] for row in rows)
    site_names = {row["site_key"]: row["site_name"] for row in rows}
    choices = sorted(
        [{"key": key, "name": name, "count": site_counts[key]} for key, name in site_names.items()],
        key=lambda item: (item["key"] == "none", item["name"].casefold()),
    )
    selected_site = request.GET.get("site", "")
    if selected_site not in site_names:
        selected_site = ""
    if selected_site:
        rows = [row for row in rows if row["site_key"] == selected_site]
    rows.sort(key=lambda row: (
        row["site_key"] == "none", row["site_name"].casefold(),
        row["type"].casefold(), str(row["object"]).casefold(),
    ))
    page = Paginator(rows, 24).get_page(request.GET.get("page"))
    groups = []
    for row in page.object_list:
        if not groups or groups[-1]["key"] != row["site_key"]:
            groups.append({
                "key": row["site_key"],
                "name": row["site_name"],
                "total": site_counts[row["site_key"]],
                "rows": [],
            })
        groups[-1]["rows"].append(row)
    return render(request, "netbox_documentation/overview.html", {
        "groups": groups, "page": page, "query": query, "selected": selected,
        "selected_site": selected_site, "site_choices": choices,
        "types": [(label, model._meta.verbose_name.title()) for label, model in options.items()],
    })


@login_required
@require_GET
def detail(request, model, pk):
    obj = object_for_user(request.user, model, pk)
    doc = _document(obj)
    context = _context(obj, doc)
    context["can_edit"] = can_edit(request.user, obj)
    native_images = _native_images(obj)
    if doc:
        context["body_html"] = render_document(
            doc.body, plugin_images=_plugin_images(doc), native_images=native_images
        )
    context["native_images"] = [
        row for row in _native_image_rows(native_images)
        if doc is None or row["token"] not in doc.body
    ]
    return render(request, "netbox_documentation/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, model, pk):
    obj = object_for_user(request.user, model, pk)
    require_edit(request.user, obj)
    doc = _document(obj)
    context = _context(obj, doc)
    if request.method == "POST":
        body = request.POST.get("body", "")
        if len(body) > 1_000_000:
            context["error"] = "Documentation cannot exceed one million characters."
        elif not body.strip() and doc is None:
            context["error"] = "Save some text first, then upload images."
        else:
            with transaction.atomic():
                doc, _ = Document.objects.update_or_create(
                    content_type=ContentType.objects.get_for_model(obj),
                    object_id=obj.pk,
                    defaults={"object_label": str(obj)[:255], "body": body},
                )
            return redirect(_context(obj, doc)["doc_url"])
        context["body"] = body
    else:
        context["body"] = doc.body if doc else ""
    context["images"] = _plugin_images(doc)
    context["native_images"] = _native_image_rows(_native_images(obj))
    return render(request, "netbox_documentation/edit.html", context)


@login_required
@require_POST
def preview(request, model, pk):
    obj = object_for_user(request.user, model, pk)
    require_edit(request.user, obj)
    body = request.POST.get("body", "")
    if len(body) > 1_000_000:
        return JsonResponse({"error": "Documentation is too long."}, status=400)
    doc = _document(obj)
    html = render_document(
        body, plugin_images=_plugin_images(doc), native_images=_native_images(obj)
    )
    return JsonResponse({"html": str(html)})


def _process_image(upload):
    if upload.size > 8 * 1024 * 1024:
        raise ValueError("Images must be 8 MB or smaller.")
    try:
        source = Image.open(upload)
        if source.format not in {"PNG", "JPEG", "WEBP"}:
            raise ValueError("Only PNG, JPEG, and WebP are supported.")
        if source.width * source.height > 12_000_000:
            raise ValueError("Images must be 12 megapixels or smaller.")
        source.load()
        image = ImageOps.exif_transpose(source)
        image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
        result = BytesIO()
        image.save(result, "PNG", optimize=True)
        data = result.getvalue()
        if len(data) > 16 * 1024 * 1024:
            raise ValueError("The converted image is too large.")
        return data
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValueError("Invalid or oversized image.") from None


@login_required
@require_POST
def upload(request, model, pk):
    obj = object_for_user(request.user, model, pk)
    require_edit(request.user, obj)
    doc = _document(obj)
    if doc is None:
        raise Http404("Save documentation before uploading images")
    file = request.FILES.get("image")
    if not file:
        return JsonResponse({"error": "Choose an image first."}, status=400)
    try:
        image_bytes = _process_image(file)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    item = DocumentImage.objects.create(
        document=doc,
        alt_text=request.POST.get("alt_text", "").strip()[:200],
        data=image_bytes,
    )
    return JsonResponse({
        "token": f"[[image:{item.pk}]]",
        "url": reverse("plugins:netbox_documentation:image", kwargs={"image_id": item.pk}),
    })


@login_required
@require_GET
def image(request, image_id):
    item = get_object_or_404(DocumentImage.objects.select_related("document__content_type"), pk=image_id)
    doc = item.document
    model = doc.content_type.model_class()
    if model is None:
        raise Http404("Object no longer exists")
    object_for_user(request.user, model._meta.label_lower, doc.object_id)
    response = HttpResponse(bytes(item.data), content_type="image/png")
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
@require_GET
def native_image(request, attachment_id):
    item = get_object_or_404(
        ImageAttachment.objects.select_related("object_type"), pk=attachment_id
    )
    model = item.object_type.model_class()
    if model is None:
        raise Http404("Object no longer exists")
    object_for_user(request.user, model._meta.label_lower, item.object_id)
    media_type, _ = mimetypes.guess_type(item.image.name)
    if media_type not in {"image/png", "image/jpeg", "image/webp", "image/gif", "image/avif"}:
        raise Http404("Unsupported image type")
    try:
        response = FileResponse(item.image.open("rb"), content_type=media_type)
    except OSError:
        raise Http404("Image file missing") from None
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


@login_required
@require_POST
def delete_image(request, model, pk, image_id):
    obj = object_for_user(request.user, model, pk)
    require_edit(request.user, obj)
    doc = _document(obj)
    item = get_object_or_404(DocumentImage, pk=image_id, document=doc)
    item.delete()
    return redirect(_context(obj, doc)["edit_url"])
