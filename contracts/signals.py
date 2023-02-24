from datetime import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Contract
from .tasks import generate_contract_number


@receiver(post_save, sender=Contract)
def generate_contract_id(sender, instance, created, **kwargs):
    if created:
        today = datetime.now().date()
        obj_pk = instance.pk
        generate_contract_number.delay(today, obj_pk)
