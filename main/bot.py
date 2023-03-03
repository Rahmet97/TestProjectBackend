import logging
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = '6085846941:AAGurWnnH-iEvBZU70txeVlfHlj76yMpTdY'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)
