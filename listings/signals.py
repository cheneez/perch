from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import ListingImage


@receiver(pre_delete, sender=ListingImage)
def delete_listing_image_file(sender, instance, **kwargs):
    """
    Remove the physical file when a ListingImage row is deleted.
    This keeps DB records and media storage in sync.
    """
    if instance.image:
        instance.image.delete(save=False)
