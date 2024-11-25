from django.urls import path

from .views import (
    DrawingDetailView,
    DrawingListView,
    add_block_insertion,
    change_block_insertion,
    csv_download,
    delete_block_insertion,
    drawing_download,
)

app_name = "djeocad"
urlpatterns = [
    path("", DrawingListView.as_view(), name="drawing_list"),
    path("<pk>", DrawingDetailView.as_view(), name="drawing_detail"),
    path("<pk>/insertion", add_block_insertion, name="insertion_create"),
    path("insertion/<pk>/change", change_block_insertion, name="insertion_change"),
    path("insertion/<pk>/delete", delete_block_insertion, name="insertion_delete"),
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
