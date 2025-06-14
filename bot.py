import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import TOKEN
from app.database.models import init_db
from app.handlers import start, menu, profile, search

from dotenv import load_dotenv

load_dotenv()

os.makedirs("media/photos", exist_ok=True)

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_routers(
        start.router,
        menu.router,
        profile.router,
        search.router
    )

    init_db()

    await dp.start_polling(bot)
    logging.info("Бот запущен")

if __name__ == "__main__":
    asyncio.run(main())

