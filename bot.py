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
PROXY = os.getenv("PROXY")  # http://IP:PORT

if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в .env!")

# Логирование
logging.basicConfig(level=logging.INFO)

# Настройка прокси для aiogram через requests
proxies = {"http": PROXY, "https": PROXY}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

def download_instagram_photo(url: str) -> str:
    """Скачивает фото из Instagram по URL через прокси."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        response.raise_for_status()
        filename = url.split("/")[-1].split("?")[0] + ".jpg"
        with open(filename, "wb") as f:
            f.write(response.content)
        return filename
    except Exception as e:
        return f"Ошибка при скачивании: {e}"

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Привет! Пришли мне ссылку на фото в Instagram, и я его скачаю.")

@dp.message_handler()
async def handle_message(message: types.Message):
    url = message.text.strip()
    if not url.startswith("http"):
        await message.reply("Пожалуйста, пришли корректную ссылку на Instagram.")
        return

    await message.reply("Скачиваю фото... ⏳")
    result = download_instagram_photo(url)

    if result.endswith(".jpg"):
        photo = InputFile(result)
        await message.reply_photo(photo)
        os.remove(result)  # удаляем файл после отправки
    else:
        await message.reply(result)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
