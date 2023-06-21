from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from rest_framework import status

from main.utils import responseErrorMessage
from .models import UserData


@receiver(m2m_changed, sender=UserData.group.through)
def handle_user_group_change(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        # The related groups are about to be cleared
        existing_instance = UserData.objects.filter(
            role=instance.role,
            group__in=instance.group.all()
        ).exclude(id=instance.pk)

        if existing_instance.exists() and instance.status_action == instance.StatusChoices.EMPLOYEE:
            # instance.group.remove(*existing_instance.last().group.all())
            responseErrorMessage(
                message="This combination of role and group already exists.",
                status_code=status.HTTP_400_BAD_REQUEST
            )


@receiver(post_save, sender=UserData)
def handle_user_role_change(sender, instance, created, **kwargs):
    if not created:
        # The related roles are about to be cleared
        existing_instance = UserData.objects.filter(
            role=instance.role,
            group__in=instance.group.all()
        ).exclude(id=instance.pk)

        if existing_instance.exists() and instance.status_action == instance.StatusChoices.EMPLOYEE:
            # instance.group.remove(*existing_instance.last().group.all())
            responseErrorMessage(
                message="This combination of role and group already exists.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
