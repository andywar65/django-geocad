from django.contrib import admin

from .models import Drawing

@admin.register(Drawing)
class DrawingAdmin(admin.ModelAdmin):
    list_display = ("title",)
