"""Keep the media folder tidy when publications are replaced or deleted."""
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import Publication


@receiver(post_delete, sender=Publication)
def delete_attachment_on_delete(sender, instance, **kwargs):
    if instance.attachment:
        instance.attachment.delete(save=False)


@receiver(pre_save, sender=Publication)
def delete_old_attachment_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = Publication.objects.get(pk=instance.pk)
    except Publication.DoesNotExist:
        return
    if old.attachment and old.attachment.name != instance.attachment.name:
        old.attachment.delete(save=False)
