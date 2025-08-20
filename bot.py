import os
import asyncio
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types.input_file import InputFile
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")
HTTP_PROXY = os.getenv("HTTP_PROXY")  # пример: http://username:password@proxy:port
HTTPS_PROXY = os.getenv("HTTPS_PROXY")  # пример: http://username:password@proxy:port

if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в .env!")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Используем aiohttp с прокси
async def fetch(session, url):
    try:
        async with session.get(url, proxy=HTTPS_PROXY or HTTP_PROXY) as response:
            return await response.read()
    except Exception as e:
        logging.error(f"Ошибка при скачивании: {e}")
        return None

async def download_instagram_image(url: str) -> str | None:
    """
    Скачивает изображение с поста Instagram через прокси.
    Возвращает имя сохранённого файла или None при ошибке.
    """
    shortcode = url.strip("/").split("/")[-1]
    json_url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
    
    async with aiohttp.ClientSession() as session:
        content = await fetch(session, json_url)
        if not content:
            return None
        try:
            import json
            data = json.loads(content)
            image_url = data["graphql"]["shortcode_media"]["display_url"]
        except Exception as e:
            logging.error(f"Ошибка при парсинге JSON: {e}")
            return None

        # Скачиваем изображение
        image_data = await fetch(session, image_url)
        if not image_data:
            return None

        filename = f"{shortcode}.jpg"
        with open(filename, "wb") as f:
            f.write(image_data)
        return filename

@dp.message_handler()
async def handle_message(message: types.Message):
    url = message.text.strip()
    logging.info(f"Получено сообщение: {url}")
    await message.reply("Скачиваю изображение...")
    filename = await download_instagram_image(url)
    if filename:
        try:
            await message.answer_photo(InputFile(filename))
            os.remove(filename)
        except Exception as e:
            await message.reply(f"Ошибка при отправке фото: {e}")
    else:
        await message.reply("Не удалось скачать изображение. Возможно, прокси нужен или пост недоступен.")

async def main():
    logging.info("Бот запущен...")
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
