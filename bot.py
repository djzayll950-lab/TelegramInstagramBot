import os
import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.utils import executor
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
INSTAGRAM_LOGIN = os.getenv("INSTAGRAM_LOGIN")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
HTTP_PROXY = os.getenv("HTTP_PROXY")
HTTPS_PROXY = os.getenv("HTTPS_PROXY")

if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в .env!")

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаём бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Настройки прокси для requests
proxies = {}
if HTTP_PROXY:
    proxies["http"] = HTTP_PROXY
if HTTPS_PROXY:
    proxies["https"] = HTTPS_PROXY

# Функция для скачивания фото по ссылке
def download_instagram_photo(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
        response.raise_for_status()

        filename = url.split("/")[-1] + ".jpg"
        with open(filename, "wb") as f:
            f.write(response.content)

        return filename
    except Exception as e:
        logging.error(f"Ошибка при скачивании: {e}")
        return None

# Команда /start
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply("Привет! Отправь ссылку на пост в Instagram, и я скачаю фото.")

# Обработка сообщений с ссылкой
@dp.message_handler()
async def handle_instagram_link(message: types.Message):
    url = message.text.strip()
    await message.reply("Скачиваю фото...")
    filename = download_instagram_photo(url)
    if filename:
        try:
            await message.reply_photo(photo=InputFile(filename))
        except Exception as e:
            await message.reply(f"Ошибка при отправке фото: {e}")
        finally:
            os.remove(filename)
    else:
        await message.reply("Не удалось скачать фото.")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
