from django.urls import path

from .views import (
    DrawingDetailView,
    DrawingListView,
    EntityDataListView,
    add_block_insertion,
    change_block_insertion,
    create_entity_data,
    csv_download,
    delete_block_insertion,
    delete_entity_data,
    drawing_download,
)

app_name = "djeocad"
urlpatterns = [
    path("", DrawingListView.as_view(), name="drawing_list"),
    path("<pk>", DrawingDetailView.as_view(), name="drawing_detail"),
    path("<pk>/insertion", add_block_insertion, name="insertion_create"),
    path("insertion/<pk>/change", change_block_insertion, name="insertion_change"),
    path("insertion/<pk>/delete", delete_block_insertion, name="insertion_delete"),
    path("insertion/<pk>/data-list", EntityDataListView.as_view(), name="data_list"),
    path("insertion/<pk>/data-create", create_entity_data, name="data_create"),
    path("entity-data/<pk>/delete", delete_entity_data, name="data_delete"),
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
