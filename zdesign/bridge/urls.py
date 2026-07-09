from django.urls import path

from . import views

urlpatterns = [
    path("__zdesign__/resolve", views.resolve),
    path("__zdesign__/edit/class", views.edit_class),
    path("__zdesign__/undo", views.undo),
    path("__zdesign__/select", views.select),
    path("__zdesign__/selection", views.selection),
]
