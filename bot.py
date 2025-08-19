import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
import instaloader
import asyncio

# --- Загружаем .env ---
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в .env!")

IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

# --- Инициализация бота ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Настройка Instaloader ---
L = instaloader.Instaloader()
if IG_USERNAME and IG_PASSWORD:
    try:
        L.login(IG_USERNAME, IG_PASSWORD)
        print("✅ Успешный вход в Instagram")
    except Exception as e:
        print(f"Ошибка при логине в Instagram: {e}")

# --- Вспомогательная функция ---
def extract_shortcode(url: str) -> Optional[str]:
    """Извлекает shortcode из ссылки Instagram поста."""
    if "/p/" in url:
        return url.split("/p/")[1].split("/")[0]
    if "/reel/" in url:
        return url.split("/reel/")[1].split("/")[0]
    if "/tv/" in url:
        return url.split("/tv/")[1].split("/")[0]
    return None

# --- /start ---
@dp.message(F.text == "/start")
async def start_handler(message: Message):
    await message.reply(
        "Привет! 👋 Пришли ссылку на Instagram пост, фото, карусель или Reels — я загружу и отправлю их сюда."
    )

# --- обработчик Instagram ссылок ---
@dp.message(F.text.startswith("https://www.instagram.com/"))
async def download_instagram_post(message: Message):
    url = message.text.strip()
    shortcode = extract_shortcode(url)
    if not shortcode:
        await message.reply("Не удалось распознать ссылку ❌")
        return

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        sent_any = False

        # Если пост — карусель (несколько фото/видео)
        if post.typename == "GraphSidecar":
            for node in post.get_sidecar_nodes():
                if node.is_video:
                    await message.reply_video(video=node.video_url)
                else:
                    await message.reply_photo(photo=node.display_url)
                sent_any = True
        else:
            # Обычное фото или видео
            if post.is_video:
                await message.reply_video(video=post.video_url)
            else:
                await message.reply_photo(photo=post.url)
            sent_any = True

        if sent_any:
            await message.reply("✅ Контент успешно отправлен!")
        else:
            await message.reply("Не удалось получить медиафайл ❌")

    except Exception as e:
        await message.reply(f"Ошибка при скачивании: {e}")

# --- Запуск бота ---
async def main():
    print("🤖 Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
