from aiogram.types import Message
from aiogram import Router
from aiogram.filters import Command
from database import load_allowed_users

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    allowed_users = load_allowed_users()
    if message.from_user.id not in allowed_users:
        await message.answer("❌ У вас немає доступу до боту")
        return
    await message.answer(f"Chat ID: {message.chat.id}")