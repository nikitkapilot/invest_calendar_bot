import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(message: types.Message):
    await message.answer(
        "✅ Бот запущен!\n\n"
        "Следующий шаг — добавим инвест-календарь 📊"
    )

async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()
    dp.message.register(start, Command("start"))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())