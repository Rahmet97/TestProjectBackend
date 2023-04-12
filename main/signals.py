import asyncio
import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver

from main.models import Application
from accounts.models import FizUser, YurUser
from main.telegram import send_message
from main.models import TelegramBotChatIDs

chat_ids = TelegramBotChatIDs.objects.all()
# chat_ids = [-666909530, 826582690]


# @receiver(post_save, sender=Application)
def send_application_using_telegram_bot(sender, instance, created, **kwargs):
    if created:
        t = instance.created_at + datetime.timedelta(hours=5)

        if instance.user.type == 1:  # fizik shaxs
            fiz = FizUser.objects.get(userdata=instance.user)
            initial_info = f"<b>Arizachi: </b> Jismoniy shaxs\n" \
                           f"<b>Arizachining passport seriyasi va raqami: </b>{fiz.pport_no}\n" \
                           f"<b>Arizachining jshshir: </b>{fiz.pin}"
        else:  # yuridik shaxs
            yu = YurUser.objects.get(userdata=instance.user)
            initial_info = f"<b>Arizachi: </b> Yuridik shaxs\n" \
                           f"<b>Tashkilot stiri: </b>{yu.tin}"

        pined_user = instance.service.pinned_user
        if pined_user.type == 1:  # fizik shaxs
            pined_user = FizUser.objects.get(userdata=pined_user)
        else:  # yuridik shaxs
            pined_user = YurUser.objects.get(userdata=pined_user)

        message_text = f"<b>Bo'lim: </b> {instance.service.group.name}\n" \
                       f"<b>Xizmat: </b> {instance.service.name}\n" \
                       f"<b>Masul shaxsga tegishli email: </b> {pined_user.email}\n\n"\
                       f"<b>FISH/Tashkilot nomi: </b> {instance.name}\n" \
                       f"<b>E-mail: </b>{instance.email}\n" \
                       f"<b>Tel: </b>{instance.phone}\n" \
                       f"<b>Xabbar: </b>{instance.message}\n" \
                       f"<b>Yuborilgan vaqti: </b>{t.strftime('%d.%m.%Y %H:%M')}" \
                       f"\n\n{initial_info}"

        if instance.file:
            file_instance = instance.file.path
        else:
            file_instance = None

        if chat_ids:
            for obj_id in chat_ids:
                asyncio.run(send_message(chat_id=obj_id.chat_id, message_text=message_text, file=file_instance))
                # asyncio.run(send_message(chat_id=obj_id, message_text=message_text, file=file_instance))

