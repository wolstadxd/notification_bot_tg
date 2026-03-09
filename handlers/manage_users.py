from aiogram import Router, F
from database import load_allowed_users, save_allowed_users
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

router = Router()

class AddUser(StatesGroup):
    user_id = State()

class RemoveUser(StatesGroup):
    user_id = State()

def get_users_list_data():
    users = load_allowed_users()
    if not users:
        return "📭 Список дозволених користувачів порожній", None
    
    text = "👥 **Дозволені користувачі:**\n\n"
    for user_id in users:
        text += f"• `{user_id}`\n"
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ Додати користувача", callback_data="add_user"))
    kb.row(InlineKeyboardButton(text="➖ Видалити користувача", callback_data="remove_user"))
    kb.row(InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu"))
    
    return text, kb.as_markup()

@router.message(Command("manage_users"))
async def manage_users_cmd(message: Message):
    allowed_users = load_allowed_users()
    if message.from_user.id not in allowed_users:
        await message.answer("❌ У вас немає доступу")
        return
    text, reply_markup = get_users_list_data()
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")

@router.callback_query(F.data == "manage_users")
async def manage_users_callback(callback: CallbackQuery):
    current_users = load_allowed_users()
    if callback.from_user.id not in current_users:
        await callback.answer("❌ У вас немає доступу", show_alert=True)
        return
    
    text, reply_markup = get_users_list_data()
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "add_user")
async def add_user_start(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_action"))
    
    await callback.message.edit_text("📝 Введіть Telegram ID користувача, якого потрібно додати:", reply_markup=kb.as_markup())
    await state.set_state(AddUser.user_id)
    await callback.answer()

@router.message(AddUser.user_id)
async def process_add_user(message: Message, state: FSMContext):
    current_users = load_allowed_users()
    if message.from_user.id not in current_users:
        await message.answer("❌ У вас немає доступу до цієї команди.")
        await state.clear()
        return
    
    try:
        user_id = int(message.text.strip())
        
        if user_id in current_users:
            await message.answer(f"⚠️ Користувач `{user_id}` вже є в списку дозволених.", parse_mode="HTML")
            await state.clear()
            return
        
        current_users.append(user_id)
        save_allowed_users(current_users)
        
        await message.answer(f"✅ Користувач `{user_id}` успішно додано до списку дозволених!", parse_mode="HTML")
        
        # Показуємо оновлений список
        text, reply_markup = get_users_list_data()
        await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
        
    except ValueError:
        await message.answer("❌ Помилка! Введіть коректний числовий ID користувача.")
        await state.clear()

@router.callback_query(F.data == "remove_user")
async def remove_user_start(callback: CallbackQuery, state: FSMContext):
    current_users = load_allowed_users()
    
    if not current_users:
        await callback.answer("📭 Список порожній", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_action"))
    
    await callback.message.edit_text("📝 Введіть Telegram ID користувача, якого потрібно видалити:", reply_markup=kb.as_markup())
    await state.set_state(RemoveUser.user_id)
    await callback.answer()

@router.message(RemoveUser.user_id)
async def process_remove_user(message: Message, state: FSMContext):
    current_users = load_allowed_users()
    if message.from_user.id not in current_users:
        await message.answer("❌ У вас немає доступу до цієї команди.")
        await state.clear()
        return
    
    try:
        user_id = int(message.text.strip())
        
        if user_id not in current_users:
            await message.answer(f"⚠️ Користувач `{user_id}` не знайдений у списку.", parse_mode="HTML")
            await state.clear()
            return
        
        # Захист від видалення останнього користувача
        if len(current_users) == 1:
            await message.answer("⚠️ Неможливо видалити останнього користувача зі списку!")
            await state.clear()
            return
        
        current_users.remove(user_id)
        save_allowed_users(current_users)
        
        await message.answer(f"✅ Користувач `{user_id}` успішно видалено зі списку!", parse_mode="HTML")
        
        # Показуємо оновлений список
        text, reply_markup = get_users_list_data()
        await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
        
        await state.clear()
    except ValueError:
        await message.answer("❌ Помилка! Введіть коректний числовий ID користувача.")
