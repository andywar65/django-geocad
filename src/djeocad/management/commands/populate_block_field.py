from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from djeocad.models import Entity, EntityData


class Command(BaseCommand):
    help = """
        This command has to be executed when passing from version 0.4.0 to 0.5.0
        of django-geocad. The command populates:
        - 'block' field from the data['block'] key
        - 'xscale' field from the data['xscale'] key
        ...
        It also generates EntityData entries with attribute key/values
    """

    def handle(self, *args, **options):
        if settings.DEBUG is False:
            raise CommandError("This command cannot be run when DEBUG is False.")
        self.stdout.write(
            "Moving Data from Entity JSONField to corresponding fields / models"
        )
        populate_fields()

        self.stdout.write("Done.")


def populate_fields():
    for ent in Entity.objects.all():
        if ent.data:
            if "processed" in ent.data:
                continue
            elif "Block" in ent.data:
                continue
            for key, value in ent.data.items():
                EntityData.objects.create(
                    entity=ent,
                    key=key,
                    value=value,
                )
        else:
            ent.data = {}
        ent.data["processed"] = "true"
        ent.save()
