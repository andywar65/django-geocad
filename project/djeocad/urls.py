from django.urls import path

from .views import DrawingListView

app_name = "djeocad"
urlpatterns = [
    path("", DrawingListView.as_view(), name="drawing_list"),
]
