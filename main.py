import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers.admin import router as admin_router
from handlers.custom import router as custom_router
from handlers.chat_id import router as chat_router
from handlers.all_merchants import router as merchant_router

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(custom_router)
    dp.include_router(admin_router)
    dp.include_router(chat_router)
    dp.include_router(merchant_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот вимкнений")