from django.urls import path

from . import views


urlpatterns = [
    path("", views.overview, name="overview"),
    path("image/<uuid:image_id>/", views.image, name="image"),
    path("native-image/<int:attachment_id>/", views.native_image, name="native_image"),
    path("<str:model>/<int:pk>/", views.detail, name="detail"),
    path("<str:model>/<int:pk>/edit/", views.edit, name="edit"),
    path("<str:model>/<int:pk>/upload/", views.upload, name="upload"),
    path("<str:model>/<int:pk>/preview/", views.preview, name="preview"),
    path("<str:model>/<int:pk>/image/<uuid:image_id>/delete/", views.delete_image, name="delete_image"),
]
