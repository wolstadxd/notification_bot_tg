from aiogram import Router, F
from database import load_allowed_users
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

router = Router()

def get_admin_menu():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🚀 Почати розсилку", callback_data="start_broadcast"))
    kb.row(InlineKeyboardButton(text="📋 Список чатів", callback_data="list_chats_menu"))
    kb.row(InlineKeyboardButton(text="➕ Додати чат", callback_data="add_chat_menu"))
    kb.row(InlineKeyboardButton(text="👥 Керування користувачами", callback_data="manage_users"))
    kb.row(InlineKeyboardButton(text="📝 Керування шаблонами", callback_data="manage_templates"))
    return kb.as_markup()

@router.message(Command("admin_panel"))
async def admin_panel_cmd(message: Message):
    allowed_users = load_allowed_users()
    if message.from_user.id not in allowed_users:
        await message.answer("❌ У вас немає доступу до адмін-панелі.")
        return
    
    text = (
        "⚙️ **Адмін-панель**\n\n"
        "Оберіть розділ для керування:"
    )
    await message.answer(text, reply_markup=get_admin_menu(), parse_mode="HTML")

@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery):
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ У вас немає доступу", show_alert=True)
        return
    
    text = (
        "⚙️ **Адмін-панель**\n\n"
        "Оберіть розділ для керування:"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_menu(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "start_broadcast")
async def start_broadcast_callback(callback: CallbackQuery):

    await callback.message.edit_text(
        "📝 Щоб налаштувати та запустити розсилку, використайте команду /new_cast",
        parse_mode="HTML",
        reply_markup=get_admin_menu(),
    )
    await callback.answer()

@router.callback_query(F.data == "add_chat_menu")
async def add_chat_menu(callback: CallbackQuery):
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ У вас немає доступу", show_alert=True)
        return
    
    await callback.message.edit_text("📝 Використайте команду /add_chat для додавання нового чату")
    await callback.answer()

@router.callback_query(F.data == "list_chats_menu")
async def list_chats_menu(callback: CallbackQuery):
    from handlers.list_chat import get_list_data
    
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ У вас немає доступу", show_alert=True)
        return
    
    text, reply_markup = get_list_data()
    kb = InlineKeyboardBuilder()
    if reply_markup:
        # Додаємо кнопку "Назад"
        for row in reply_markup.inline_keyboard:
            kb.row(*[InlineKeyboardButton(text=btn.text, callback_data=btn.callback_data) for btn in row])
    kb.row(InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu"))
    
    await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    await callback.answer()
