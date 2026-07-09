from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import render
from django.urls import include, path


def home(request):
    return render(request, "demo/home.html")


urlpatterns = [
    path("", home),
    path("", include("djust_designer.urls")),
]
urlpatterns += staticfiles_urlpatterns()
