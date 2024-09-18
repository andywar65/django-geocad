from django.urls import path

from .views import DrawingDetailView, DrawingListView

app_name = "djeocad"
urlpatterns = [
    path("", DrawingListView.as_view(), name="drawing_list"),
    path("<pk>", DrawingDetailView.as_view(), name="drawing_detail"),
]
