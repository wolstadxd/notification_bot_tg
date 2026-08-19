from aiogram import Router, F
from database import load_allowed_users, TEMPLATES_FILE, MAIN_TEMPLATES_FILE, CHATS_FILE, ALLOWED_USERS_FILE, METHOD_HISTORY_FILE
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from config import LOG_FILE, HISTORY_FILE
import os
import config
from aiogram.fsm.context import FSMContext
from handlers.states import BroadcastStates
from handlers.new_cast import get_active_tags
router = Router()

def get_admin_menu():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🚀 Почати розсилку", callback_data="start_broadcast"))
    kb.row(InlineKeyboardButton(text="📢 Mass Cast", callback_data="mass_cast_start"))
    kb.row(InlineKeyboardButton(text="📋 Список чатів", callback_data="list_chats_menu"))
    kb.row(InlineKeyboardButton(text="➕ Додати чат", callback_data="add_chat_menu"))
    kb.row(InlineKeyboardButton(text="👥 Керування користувачами", callback_data="manage_users"))
    kb.row(InlineKeyboardButton(text="📝 Керування шаблонами", callback_data="manage_templates"))
    kb.row(InlineKeyboardButton(text="🗂 Головні шаблони", callback_data="manage_main"))
    kb.row(InlineKeyboardButton(text="📁 Завантажити логи", callback_data="download_logs"))
    kb.row(InlineKeyboardButton(text="📊 Methods status", callback_data="methods_status_menu"))
    return kb.as_markup()

@router.message(Command("admin_panel"))
async def admin_panel_cmd(message: Message, state: FSMContext):
    await state.clear()
    allowed_users = load_allowed_users()
    if message.from_user.id not in allowed_users:
        await message.answer("❌ You don't have access")
        return
    
    text = (
        "⚙️ **Адмін-панель**\n\n"
        "Оберіть розділ для керування:"
    )
    await message.answer(text, reply_markup=get_admin_menu(), parse_mode="HTML")

@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery, state: FSMContext):
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return

    await state.clear()
    # Відповідаємо ПЕРШИМ, щоб Loading зник миттєво
    await callback.answer()

    text = (
        "⚙️ **Адмін-панель**\n\n"
        "Оберіть розділ для керування:"
    )
    try:
        await callback.message.edit_text(text, reply_markup=get_admin_menu(), parse_mode="HTML")
    except Exception:
        # Якщо повідомлення старе або не можна відредагувати — надсилаємо нове
        await callback.message.answer(text, reply_markup=get_admin_menu(), parse_mode="HTML")


@router.callback_query(F.data == "start_broadcast")
async def start_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return
        
    await state.clear()
    geos = get_active_tags(step="geo")
    if not geos:
        await callback.message.edit_text("В базі немає чатів.", reply_markup=get_admin_menu())
        await callback.answer()
        return

    kb = InlineKeyboardBuilder()
    for geo in geos:
        kb.row(InlineKeyboardButton(text=f"📍 {geo.upper()}", callback_data=f"b_geo_{geo}"))
    
    if config.sent_history:
        kb.row(InlineKeyboardButton(text="🗑 Видалити останню розсилку", callback_data="delete_last_broadcast"))

    kb.row(InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu"))

    await state.set_state(BroadcastStates.choosing_geo)
    await callback.message.edit_text("Виберіть ГЕО для розсилки:", reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(F.data == "add_chat_menu")
async def add_chat_menu(callback: CallbackQuery):
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return
    
    await callback.message.edit_text("📝 Використайте команду /add_chat для додавання нового чату")
    await callback.answer()

@router.callback_query(F.data == "list_chats_menu")
async def list_chats_menu(callback: CallbackQuery):
    from handlers.list_chat import get_list_data
    
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ You don't have access", show_alert=True)
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

@router.callback_query(F.data == "download_logs")
async def download_logs_callback(callback: CallbackQuery):
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return

    await callback.answer("Завантаження файлів...", show_alert=False)
    
    if os.path.exists(LOG_FILE):
        await callback.message.answer_document(FSInputFile(LOG_FILE))
    else:
        await callback.message.answer("Файл activity_log.json не знайдено.")

    if os.path.exists(HISTORY_FILE):
        await callback.message.answer_document(FSInputFile(HISTORY_FILE))
    else:
        await callback.message.answer("Файл sent_history.json не знайдено.")

    if os.path.exists(TEMPLATES_FILE):
        await callback.message.answer_document(FSInputFile(TEMPLATES_FILE))
    else:
        await callback.message.answer("Файл templates.json не знайдено.")

    if os.path.exists(MAIN_TEMPLATES_FILE):
        await callback.message.answer_document(FSInputFile(MAIN_TEMPLATES_FILE))
    else:
        await callback.message.answer("Файл main_templates.json не знайдено.")

    if os.path.exists(CHATS_FILE):
        await callback.message.answer_document(FSInputFile(CHATS_FILE))
    else:
        await callback.message.answer("Файл chats.json не знайдено.")

    if os.path.exists(ALLOWED_USERS_FILE):
        await callback.message.answer_document(FSInputFile(ALLOWED_USERS_FILE))
    else:
        await callback.message.answer("Файл allowed_users.json не знайдено.")

    if os.path.exists(METHOD_HISTORY_FILE):
        await callback.message.answer_document(FSInputFile(METHOD_HISTORY_FILE))
    else:
        await callback.message.answer("Файл method_status_history.json не знайдено.")

