import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers.admin import router as admin_router
from handlers.custom import router as custom_router
from handlers.chat_id import router as chat_router
from handlers.all_merchants import router as all_merchant_router
from handlers.manage_chats import router as admin_panel
from handlers.list_chat import router as list_chat
from handlers.manage_users import router as manage_users_router
from handlers.manage_templates import router as manage_templates_router
from handlers.admin_menu import router as admin_menu_router

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(custom_router)
    dp.include_router(admin_router)
    dp.include_router(chat_router)
    dp.include_router(all_merchant_router)
    dp.include_router(admin_panel)
    dp.include_router(list_chat)
    dp.include_router(manage_users_router)
    dp.include_router(manage_templates_router)
    dp.include_router(admin_menu_router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот вимкнений")