from django.db import models
from django.utils.translation import gettext_lazy as _

class Drawing(models.Model):

    title = models.CharField(
        _("Name"),
        help_text=_("Name of the drawing"),
        max_length=50,
    )
