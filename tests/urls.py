from django.urls import include, path

urlpatterns = [
    path("geocad/", include("djeocad.urls", namespace="djeocad")),
]
