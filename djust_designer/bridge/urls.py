from django.urls import path

from . import views

urlpatterns = [
    path("__djust_designer__/resolve", views.resolve),
    path("__djust_designer__/edit/class", views.edit_class),
    path("__djust_designer__/undo", views.undo),
    path("__djust_designer__/select", views.select),
    path("__djust_designer__/selection", views.selection),
]
