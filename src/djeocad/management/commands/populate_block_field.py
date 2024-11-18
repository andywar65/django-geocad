from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from djeocad.models import Entity, EntityData, Layer


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
                try:
                    block = Layer.objects.get(
                        name=ent.data["Block"], drawing=ent.layer.drawing
                    )
                    ent.block = block
                    if "X scale" in ent.data:
                        ent.xscale = ent.data["X scale"]
                    if "Y scale" in ent.data:
                        ent.yscale = ent.data["Y scale"]
                    if "Rotation" in ent.data:
                        ent.rotation = ent.data["Rotation"]
                    ent.data["processed"] = "true"
                    ent.save()
                    if "attributes" in ent.data:
                        for key, value in ent.data["attributes"].items():
                            EntityData.objects.create(
                                entity=ent,
                                key=key,
                                value=value,
                            )
                    continue
                except ObjectDoesNotExist:
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
