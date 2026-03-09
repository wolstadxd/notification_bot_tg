from aiogram import Bot
from aiogram import Router, F
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from handlers.states import BroadcastStates
from config import sent_history, write_event_log
from database import load_chats, load_allowed_users, load_templates
import config
from keyboards import get_yes_no_custom_kb, get_template_kb, get_lang_kb, get_lang_kb_all

router = Router()

def get_active_tags(filter_list=None, step="geo"):
    chats = load_chats()
    tags_to_show = set()

    for chat in chats:
        chat_tags = chat.get("tags", [])
        if not chat_tags:
            continue
        # Крок 1: Збираємо всі ГЕО (завжди перший тег)
        if step == "geo":
            tags_to_show.add(chat_tags[0])
        # Крок 2: Збираємо мови (тільки для обраного ГЕО)
        elif step == "lang":
            if filter_list[0] == chat_tags[0]:
                tags_to_show.add(chat_tags[1])
        # Крок 3: Збираємо методи (тільки для ГЕО + Мова)
        elif step == "method":
            if filter_list[0] == chat_tags[0] and filter_list[1] == chat_tags[1]:
                # Всі теги після ГЕО та мови — це методи
                for m in chat_tags[2:]:
                    tags_to_show.add(m)
                    
    return sorted(list(tags_to_show))


@router.message(Command("new_cast"))
async def start_broadcast(message: Message, state: FSMContext):
    allowed_users = load_allowed_users()
    if message.from_user.id not in allowed_users:
        await message.answer("❌ У вас немає доступу")
        return
    await state.clear()
    
    geos = get_active_tags(step="geo")
    if not geos:
        return await message.answer("В базі немає чатів.")

    kb = InlineKeyboardBuilder()
    for geo in geos:
        kb.row(InlineKeyboardButton(text=f"📍 {geo.upper()}", callback_data=f"b_geo_{geo}"))
    
    if config.sent_history:
        kb.row(InlineKeyboardButton(text="🗑 Видалити останню розсилку", callback_data="delete_last_broadcast"))

    await state.set_state(BroadcastStates.choosing_geo)
    await message.answer("Виберіть ГЕО для розсилки:", reply_markup=kb.as_markup())

@router.callback_query(BroadcastStates.choosing_geo, F.data.startswith("b_geo_"))
async def choose_lang_step(callback: CallbackQuery, state: FSMContext):
    selected_geo = callback.data.split("_")[2]
    await state.update_data(geo=selected_geo)
    langs = get_active_tags(filter_list=[selected_geo], step="lang")
    # 4. Будуємо кнопки з мовами
    kb = InlineKeyboardBuilder()
    for lang in langs:
        kb.row(InlineKeyboardButton(text=f"🗣 {lang.upper()}", callback_data=f"b_lang_{lang}"))

    kb.row(InlineKeyboardButton(text="⬅️ Назад до ГЕО", callback_data="back_to_admin_start"))

    await state.set_state(BroadcastStates.choosing_lang)
    await callback.message.edit_text(
        f"📍 Обрано ГЕО: {selected_geo.upper()}\nТепер виберіть мову:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_admin_start")
async def back_to_admin_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    geos = get_active_tags(step="geo")
    kb = InlineKeyboardBuilder()
    for geo in geos:
        kb.row(InlineKeyboardButton(text=f"📍 {geo.upper()}", callback_data=f"b_geo_{geo}"))
    
    await state.set_state(BroadcastStates.choosing_geo)
    await callback.message.edit_text("Виберіть ГЕО для розсилки:", reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(BroadcastStates.choosing_lang, F.data.startswith("b_lang_"))
async def choose_method_step(callback: CallbackQuery, state: FSMContext):
    # 1. Витягуємо мову з кнопки
    selected_lang = callback.data.split("_")[2]
    user_data = await state.get_data()
    selected_geo = user_data.get('geo')
    await state.update_data(lang=selected_lang)
    methods = get_active_tags(filter_list=[selected_geo, selected_lang], step="method")
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="📢 ВСІ НАПРЯМКИ", callback_data="b_method_all"))
    
    for m in methods:
        kb.row(InlineKeyboardButton(text=f"⚙️ {m.upper()}", callback_data=f"b_method_{m}"))

    kb.row(InlineKeyboardButton(text="⬅️ Назад до ГЕО", callback_data="back_to_admin_start"))

    await state.set_state(BroadcastStates.choosing_method)
    await callback.message.edit_text(
        f"📍 ГЕО: {selected_geo.upper()} | 🗣 Мова: {selected_lang.upper()}\n"
        f"Виберіть технічний напрямок:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(BroadcastStates.choosing_method, F.data.startswith("b_method_"))
async def choose_template_step(callback: CallbackQuery, state: FSMContext):
    selected_method = callback.data.replace("b_method_", "")
    await state.update_data(method=selected_method)

    user_data = await state.get_data()
    geo = user_data.get('geo')
    lang = user_data.get('lang')
    
    templates = load_templates()
 
    available_templates = templates.get(lang, {})
    
    # 5. Будуємо кнопки
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="✍️ Кастомна розсилка", callback_data="b_tmpl_custom"))
    for tmpl_name in available_templates.keys():
        display_name = tmpl_name.replace("_", " ").capitalize()
        kb.row(InlineKeyboardButton(
            text=f"📝 {display_name}", 
            callback_data=f"b_tmpl_{tmpl_name}"
        ))
    
    kb.row(InlineKeyboardButton(text="⬅️ Назад до ГЕО", callback_data="back_to_admin_start"))

    await state.set_state(BroadcastStates.choosing_template)
    
    # 7. Виводимо фінальний вибір
    method_display = "УСІ" if selected_method == "all" else selected_method.upper()
    await callback.message.edit_text(
        f"⚙️ **Конфігурація розсилки:**\n"
        f"📍 ГЕО: {geo.upper()}\n"
        f"🗣 Мова: {lang.upper()}\n"
        f"🛠 Напрямок: {method_display}\n\n"
        f"Яке повідомлення відправити?",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(BroadcastStates.choosing_template, F.data.startswith("b_tmpl_"))
async def execute_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    tmpl_type = callback.data.replace("b_tmpl_", "")

    data = await state.get_data()
    geo = data.get('geo')
    lang = data.get('lang')
    method = data.get('method')

    chats = load_chats()
    templates = load_templates()
    
    try:
        template_text = templates[lang][tmpl_type].format(geo=geo.upper())
    except Exception as e:
        await callback.answer(f"Помилка в шаблоні: {e}", show_alert=True)
        return

    # 5. Фільтруємо чати за плоскими тегами
    target_chats = []
    for chat in chats:
        tags = chat.get("tags", [])
        if len(tags) >= 2 and tags[0] == geo and tags[1] == lang:
            if method == "all" or method in tags[2:]:
                target_chats.append(chat)

    if not target_chats:
        await callback.message.edit_text(
            f"❌ Чати не знайдені для:\n"
            f"📍 ГЕО: {geo.upper()} | 🗣 Мова: {lang.upper()} | 🛠 Метод: {method.upper()}"
        )
        await state.clear()
        return

    # 6. Сама розсилка
    success = 0
    errors = 0
    temp_messages = [] # Для історії та видалення

    for chat in target_chats:
        try:
            # Додаємо меншини, якщо вони є
            mentions = " ".join(chat.get("mentions", []))
            full_text = f"{template_text}\n\n{mentions}" if mentions else template_text
            
            msg = await bot.send_message(chat_id=chat["id"], text=full_text, parse_mode="HTML")
            temp_messages.append((chat["id"], msg.message_id))
            success += 1
        except Exception as e:
            print(f"Помилка відправки в {chat['name']}: {e}")
            errors += 1

    # 7. Зберігаємо в історію (щоб можна було видалити)
    broadcast_id = str(callback.id)
    config.sent_history[broadcast_id] = {
        "geo": geo.upper(),
        "lang": lang.upper(),
        "method": method,
        "type": tmpl_type,
        "messages": temp_messages
    }
    config.save_history(config.sent_history)

    config.write_event_log("SEND", {
        "broadcast_id": broadcast_id,
        "geo": geo.upper(),
        "lang": lang.upper(),
        "method": method,
        "template": tmpl_type,
        "results": {
            "success": success,
            "errors": errors
        }
    })
    
    # Кнопка видалення
    delete_kb = InlineKeyboardBuilder()
    delete_kb.row(InlineKeyboardButton(text='🗑 Видалити розсилку', callback_data=f'del_{broadcast_id}'))

    # 8. Фінальний звіт
    await callback.message.edit_text(
        f"🚀 **Розсилка завершена!**\n\n"
        f"📊 Результати:\n"
        f"✅ Успішно: {success}\n"
        f"❌ Помилок: {errors}\n\n"
        f"Фільтр: {geo.upper()} | {lang.upper()} | {method.upper()}",
        parse_mode="HTML",
        reply_markup=delete_kb.as_markup()

    )
    
    await state.clear()
    await callback.answer("Готово!")


@router.callback_query(F.data == "delete_last_broadcast")
async def delete_last_execution(callback: CallbackQuery, bot: Bot, state: FSMContext):
    if not config.sent_history:
        await callback.answer("Історія розсилок порожня", show_alert=True)
        return

    # Беремо останній ID розсилки
    last_id = list(config.sent_history.keys())[-1]
    broadcast_data = config.sent_history[last_id]
    
    messages_to_delete = broadcast_data.get('messages', [])
    geo = broadcast_data.get("geo", "Невідомо")
    lang = broadcast_data.get("lang", "Невідомо")
    tmpl_type = broadcast_data.get("type", "Невідомо")
    method = broadcast_data.get("method", "Невідомо")

    deleted_count = 0
    # Проходимо по всіх чатах, куди полетіла ця розсилка
    for chat_id, msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            deleted_count += 1
        except Exception as e:
            print(f"Не вдалося видалити в {chat_id}: {e}")

    # Логуємо видалення у "Вічну книгу"
    config.write_event_log('DELETE_LAST', {
        "broadcast_id": last_id,
        "geo": geo,
        "lang": lang,
        "method": method,
        "template": tmpl_type,
        "deleted_messages": deleted_count
    })

    # Видаляємо з пам'яті та зберігаємо файл історії
    del config.sent_history[last_id]
    config.save_history(config.sent_history)
    
    await callback.answer("Розсилку видалено всюди!")
    await callback.message.edit_text(
        f"🗑 **Останню розсилку видалено:**\n\n"
        f"📍 ГЕО: {geo}\n"
        f"⚙️ Метод: {method}\n"
        f"📨 Видалено повідомлень: {deleted_count}"
    )
    
    await start_broadcast(callback.message, state)