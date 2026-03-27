from aiogram import Router, F
from database import load_chats, save_chats, load_allowed_users
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.filters import Command
from typing import Union
from handlers.admin_menu import get_admin_menu
import html
router = Router()

class AddChat(StatesGroup):
    name = State()
    chat_id = State()
    tags = State()
    mentions = State()


class EditChat(StatesGroup):
    name = State()
    chat_id = State()
    tags = State()
    mentions = State()

@router.message(Command("cancel_action"))
@router.callback_query(F.data == "cancel_action")
async def cancel_handler(event: Union[Message, CallbackQuery], state: FSMContext):
    # 1. Визначаємо, хто пише (event може бути і Message, і CallbackQuery)
    user_id = event.from_user.id
    allowed_users = load_allowed_users()
    if user_id not in allowed_users:
        if isinstance(event, Message):
            await event.answer("❌ You don't have access")
        else:
            await event.answer("❌ You don't have access")
        return

    await state.clear()
    
    # 3. Логіка відповіді
    if isinstance(event, CallbackQuery):
        await event.answer("Дію скасовано")
        # Використовуємо event.message, бо в CallbackQuery текст лежить там
        await event.message.edit_text(
            "⚙️ <b>Адмін-панель</b>\n\nОберіть розділ для керування:",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )
    else:
        # Якщо це була команда /cancel_action текстом
        await event.answer(
            "⚙️ <b>Адмін-панель</b>\n\nОберіть розділ для керування:",
            reply_markup=get_admin_menu(),
            parse_mode="HTML"
        )

@router.message(Command("add_chat"))
async def start_add_chat(message: Message, state: FSMContext):
    allowed_users = load_allowed_users()
    if message.from_user.id not in allowed_users:
        await message.answer("❌ You don't have access")
        return
    await state.set_state(AddChat.name)
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_action"))
    
    await message.answer(
        "Введіть назву чату:",   
        reply_markup=kb.as_markup()
    )
    
@router.message(AddChat.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name = message.text)
    await message.answer('Введіть chat_id мерчанта:')
    await state.set_state(AddChat.chat_id)

@router.message(AddChat.chat_id)
async def process_id(message: Message, state: FSMContext):
    await state.update_data(chat_id = int(message.text))
    await message.answer('Введіть теги мерчанта через пробіл (гео, мова, напрямок, важливість) - peru ua khipu vip:')
    await state.set_state(AddChat.tags)

@router.message(AddChat.tags)
async def process_tags(message: Message, state: FSMContext):
    # Розбиваємо рядок "peru en etpay" -> ["peru", "en", "etpay"]
    tags_list = message.text.lower().split()
    
    await state.update_data(tags=tags_list)
    await message.answer(f"✅ Теги збережено\nВведіть меншини через пробіл (@test1 @test2) або 'ні':")
    await state.set_state(AddChat.mentions)


@router.message(AddChat.mentions)
async def process_mentions(message: Message, state: FSMContext):
    mentions = [] if message.text.lower() == 'ні' else message.text.split()
    user_data = await state.get_data()
    
    # Створюємо новий об'єкт чату
    new_chat = {
        "name": user_data['name'],
        "id": user_data['chat_id'],
        "tags": user_data['tags'],
        "mentions": mentions,
        "status": "merchant"
    }

    # 1. Завантажуємо поточний список
    all_chats = load_chats()
    
    # 2. Перевіряємо, чи немає вже такого ID (захист від дублів)
    if any(chat['id'] == new_chat['id'] for chat in all_chats):
        await message.answer("❌ Чат з таким ID вже існує у списку!")
        await state.clear()
        return

    # 3. Додаємо і зберігаємо
    all_chats.append(new_chat)
    save_chats(all_chats)

    await message.answer(
        f"✅ Чат '{user_data['name']}' успішно додано до загального списку!\n\n"
        "Повернутися до адмін-панелі: /admin_panel"
    )
    await state.clear()


@router.callback_query(F.data.startswith("edit_chat_"))
async def start_edit_chat(callback: CallbackQuery, state: FSMContext):

    chat_id = int(callback.data.split("_")[2])
    all_chats = load_chats()
    chat = next((c for c in all_chats if c["id"] == chat_id), None)

    if not chat:
        await callback.answer("❌ Чат не знайдено", show_alert=True)
        return

    await state.update_data(
        original_id=chat["id"],
        name=chat["name"],
        chat_id=chat["id"],
        tags=chat.get("tags", []),
        mentions=chat.get("mentions", []),
    )
    await state.set_state(EditChat.name)

    current_tags = ", ".join(chat.get("tags", [])) if chat.get("tags") else "немає"
    current_mentions = (
        ", ".join(chat.get("mentions", [])) if chat.get("mentions") else "немає"
    )

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_action"))
    
    safe_name = html.escape(chat["name"])
    
    await callback.message.edit_text(
        "✏️ Редагування чату:\n\n"
        f"Поточна назва: {safe_name}\n"
        "Введіть нову назву чату (або надішліть ту ж саму):",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.message(EditChat.name)
async def edit_chat_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    await message.answer(
        f"Поточний chat_id: `{data['chat_id']}`\n"
        "Введіть новий chat_id мерчанта (або надішліть той самий):",
        parse_mode="HTML",
    )
    await state.set_state(EditChat.chat_id)


@router.message(EditChat.chat_id)
async def edit_chat_id(message: Message, state: FSMContext):
    try:
        chat_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Помилка! Введіть коректний числовий chat_id.")
        return

    await state.update_data(chat_id=chat_id)
    data = await state.get_data()
    current_tags = " ".join(data.get("tags", [])) if data.get("tags") else "немає"
    await message.answer(
        f"Поточні теги: {current_tags}\n"
        "Введіть нові теги мерчанта через пробіл:"
    )
    await state.set_state(EditChat.tags)


@router.message(EditChat.tags)
async def edit_chat_tags(message: Message, state: FSMContext):
    tags_list = message.text.lower().split()
    await state.update_data(tags=tags_list)
    data = await state.get_data()
    current_mentions = (
        ", ".join(data.get("mentions", [])) if data.get("mentions") else "немає"
    )
    await message.answer(
        "✅ Теги збережено\n"
        f"Поточні меншини: {current_mentions}\n"
        "Введіть нові меншини через пробіл (@test1 @test2) або 'ні':",
    )
    await state.set_state(EditChat.mentions)


@router.message(EditChat.mentions)
async def edit_chat_mentions(message: Message, state: FSMContext):
    mentions = [] if message.text.lower() == "ні" else message.text.split()
    data = await state.get_data()

    all_chats = load_chats()
    original_id = data["original_id"]

    # Перевіряємо, чи існує чат з оригінальним ID
    index = next((i for i, c in enumerate(all_chats) if c["id"] == original_id), None)
    if index is None:
        await message.answer("❌ Не вдалося знайти чат для редагування.")
        await state.clear()
        return

    # Перевірка на дубль chat_id (дозволяємо, якщо це той самий чат)
    new_id = data["chat_id"]
    if any(c["id"] == new_id and c["id"] != original_id for c in all_chats):
        await message.answer("❌ Чат з таким chat_id вже існує у списку!")
        await state.clear()
        return

    updated_chat = {
        "name": data["name"],
        "id": new_id,
        "tags": data["tags"],
        "mentions": mentions,
        "status": all_chats[index].get("status", "merchant"),
    }

    all_chats[index] = updated_chat
    save_chats(all_chats)

    await message.answer(
        f"✅ Чат '{updated_chat['name']}' успішно оновлено в загальному списку!\n\n"
        "Повернутися до адмін-панелі: /admin_panel"
    )
    await state.clear()