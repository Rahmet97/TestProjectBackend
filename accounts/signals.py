from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserData


@receiver(post_save, sender=UserData)
def generate_contract_id(sender, instance, created, **kwargs):
    if not created:
        existing_instance = UserData.objects.filter(
            role=instance.role, group__in=instance.group.all()
        ).exclude(id=instance.pk)
        print("update section >> ", existing_instance)

        if existing_instance.exists() and instance.status_action == instance.StatusChoices.EMPLOYEE:
            print("2 >> ", existing_instance)
            instance.group.clear()
            instance.save()
