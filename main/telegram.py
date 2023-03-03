from aiogram import types
from aiogram.utils.exceptions import BotKicked

from main.bot import bot, dp


async def send_message(chat_id, message_text, file=None):
    try:
        # Send a message to the chat using the `send_message` method of the bot object.
        # The `chat_id` argument specifies the chat to send the message to, and the `text` argument
        # specifies the text of the message. The `parse_mode` argument specifies the parse mode
        # to use when sending the message. In this case, it is set to `types.ParseMode.HTML`.
        sent_message = await bot.send_message(
            chat_id=chat_id, text=message_text,
            parse_mode=types.ParseMode.HTML
        )
        if file is not None:
            # Send a document to the chat using the `send_document` method of the bot object.
            # The `chat_id` argument specifies the chat to send the document to, and the `document`
            # argument specifies the file to be sent. The `reply_to_message_id` argument specifies the
            # message that the document should be sent in reply to, in this case the message sent earlier.
            await bot.send_document(
                chat_id=chat_id, document=open(file, 'rb'),
                reply_to_message_id=sent_message.message_id
            )

    # Catch the BotKicked exception and print an error message
    # except BotKicked as e:
    except BotKicked as e:
        # Handle the exception here
        print("The bot was kicked from the group chat due to the following error:")
        print(e)
