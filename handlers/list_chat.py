from aiogram import Router, F
from database import load_chats
from aiogram.types import Message
from aiogram.filters import Command
from database import load_allowed_users
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from database import load_chats, save_chats
import html

router = Router()

def get_list_data():
    chats = load_chats()
    if not chats:
        return "Список чатів порожній 📭", None
    
    kb = InlineKeyboardBuilder()
    for chat in chats:
        kb.row(InlineKeyboardButton(
            text=f"📁 {chat['name']}", 
            callback_data=f"manage_chat_{chat['id']}")
        )
    return "📋 **Оберіть чат для керування:**", kb.as_markup()

@router.message(Command("list_chats"))
async def list_chats_cmd(message: Message):
    allowed_users = load_allowed_users()
    if message.from_user.id not in allowed_users:
        await message.answer("❌ У вас немає доступу")
        return
    text, reply_markup = get_list_data()
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")

# Для кнопки "Назад" (редагування існуючого повідомлення)
@router.callback_query(F.data == "back_to_list")
async def back_to_list(callback: CallbackQuery):
    text, reply_markup = get_list_data()
    await callback.message.edit_text(
        text=text, 
        reply_markup=reply_markup, 
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("manage_chat_"))
async def manage_chat_menu(callback: CallbackQuery):
    chat_id = int(callback.data.split("_")[2])
    all_chats = load_chats()
    
    # Шукаємо потрібний чат у списку
    chat = next((c for c in all_chats if c['id'] == chat_id), None)
    
    if not chat:
        await callback.answer("❌ Чат не знайдено", show_alert=True)
        return
    
    safe_name = html.escape(chat['name'])
    text = (f"⚙️ **Керування чатом:** {safe_name}\n\n"
        f"🆔 `{chat['id']}`\n"
        f"🏷 Теги: {', '.join(chat['tags'])}\n"
        f"👤 Меншини: {', '.join(chat['mentions']) if chat['mentions'] else 'немає'}\n"
        f"📊 Статус: `{chat.get('status', 'не визначено')}`\n")

    kb = InlineKeyboardBuilder()
    # Кнопка редагування
    kb.row(InlineKeyboardButton(text="✏️ Редагувати чат", callback_data=f"edit_chat_{chat_id}"))
    # Кнопка видалення (веде на підтвердження)
    kb.row(InlineKeyboardButton(text="🗑 Видалити чат", callback_data=f"confirm_drop_{chat_id}"))
    # Кнопка повернення назад до списку
    kb.row(InlineKeyboardButton(text="⬅️ Назад до списку", callback_data="back_to_list"))
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")

@router.callback_query(F.data.startswith("confirm_drop_"))
async def confirm_drop(callback: CallbackQuery):
    chat_id = callback.data.split("_")[2]
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="✅ ТАК, ВИДАЛИТИ", callback_data=f"real_drop_{chat_id}"))
    kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data=f"manage_chat_{chat_id}"))
    
    await callback.message.edit_text(
        f"⚠️ Ви впевнені, що хочете видалити чат `{chat_id}`? Цю дію неможливо скасувати.",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("real_drop_"))
async def real_drop_chat(callback: CallbackQuery):
    chat_id_to_delete = int(callback.data.split("_")[2])
    all_chats = load_chats()
    
    updated_chats = [c for c in all_chats if c['id'] != chat_id_to_delete]
    save_chats(updated_chats)
    
    await callback.message.edit_text("✅ Чат остаточно видалено з бази.")
    await callback.answer("Видалено")

@router.callback_query(F.data == "cancel_drop")
async def cancel_drop(callback: CallbackQuery):
    await callback.message.edit_text("🔄 Видалення скасовано.")
    await callback.answer()

@router.callback_query(F.data == "back_to_list")
async def back_to_list(callback: CallbackQuery):
    text, reply_markup = get_list_data()
    await callback.message.edit_text(
        text=text, 
        reply_markup=reply_markup, 
        parse_mode="HTML"
    )