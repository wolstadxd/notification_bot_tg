from aiogram.types import Message
from aiogram import Router
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(f"Привіт! Твій Chat ID: {message.chat.id}")