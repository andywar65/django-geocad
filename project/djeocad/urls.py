from django.urls import path

from .views import DrawingDetailView, DrawingListView, csv_download, drawing_download

app_name = "djeocad"
urlpatterns = [
    path("", DrawingListView.as_view(), name="drawing_list"),
    path("<pk>", DrawingDetailView.as_view(), name="drawing_detail"),
    path(
        "<pk>/csv",
        csv_download,
        name="drawing_csv",
    ),
    path(
        "<pk>/download",
        drawing_download,
        name="drawing_download",
    ),
]
