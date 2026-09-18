from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path


def home(request):
    return render(request, "index.html")


urlpatterns = [
    path("admin/", admin.site.urls),

    path("accounts/", include("accounts.urls")),
    path("donors/", include("donors.urls")),
    path("requests/", include("blood_requests.urls")),
    path("matching/", include("matching.urls")),
    path("notifications/", include("notifications.urls")),

    path("", home, name="home"),
]