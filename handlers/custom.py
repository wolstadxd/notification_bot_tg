from aiogram import Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router, F
from handlers.states import BroadcastStates
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from database import load_chats
import config
from keyboards import get_yes_no_custom_kb, back_to_geo
from handlers.admin_menu import get_admin_menu

router = Router()

@router.callback_query(BroadcastStates.choosing_template, F.data == "b_tmpl_custom")
async def start_custom_text_input(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    await callback.message.edit_text(
        f"📝 **Режим кастомної розсилки**\n\n"
        f"📍 ГЕО: {data.get('geo').upper()}\n"
        f"🗣 Мова: {data.get('lang').upper()}\n"
        f"🛠 Метод: {data.get('method').upper()}\n\n"
        "Введіть текст повідомлення:"
    )
    # Перемикаємо стан на очікування тексту
    await state.set_state(BroadcastStates.entering_custom_text)
    await callback.answer()


@router.message(BroadcastStates.entering_custom_text)
async def preview_custom_message(message: Message, state: FSMContext):
    # Зберігаємо введений текст
    await state.update_data(user_text=message.text)
    data = await state.get_data()
    
    await message.answer(
        f"🧐 **ПРЕВ'Ю ПОВІДОМЛЕННЯ:**\n\n"
        f"{message.text}\n\n"
        f"--- \n"
        f"Відправити в усі чати {data.get('geo').upper()} | {data.get('lang').upper()} | {data.get('method').upper()}?",
        reply_markup=get_yes_no_custom_kb(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == 'yes_custom', BroadcastStates.entering_custom_text)
async def send_custom_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    geo = data.get('geo')
    lang = data.get('lang')
    method = data.get('method')
    final_text = data.get('user_text')

    chats = load_chats()
    success_count = 0
    error_count = 0
    temp_messages = []

    target_chats = []
    for chat in chats:
        tags = chat.get("tags", [])
        if len(tags) >= 2 and tags[0] == geo and tags[1] == lang:
            if method == "all" or method in tags[2:]:
                target_chats.append(chat)

    if not target_chats:
        await callback.message.edit_text(
            f"❌ Чати не знайдені для:\n"
            f"📍 ГЕО: {geo.upper()} | 🗣 Мова: {lang.upper()} | 🛠 Метод: {method.upper()} | "
        )
        await state.clear()
        return
    # Фільтруємо чати за плоскими тегами
    for chat in target_chats:
                try:
                    mentions = " ".join(chat.get("mentions", []))
                    full_text = f"{final_text}\n\n{mentions}" if mentions else final_text
                    
                    msg = await bot.send_message(
                        chat_id=chat["id"], 
                        text=full_text, 
                        parse_mode="HTML"
                    )
                    temp_messages.append((chat["id"], msg.message_id))
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    print(f"Error in {chat.get('name')}: {e}")

    # --- Логування (як ми домовлялися) ---
    broadcast_id = str(callback.id)
    config.sent_history[broadcast_id] = {
        "geo": geo.upper(), "lang": lang.upper(), "method": method.upper(),
        "type": "CUSTOM", "messages": temp_messages
    }
    config.save_history(config.sent_history)

    config.write_event_log("SEND CUSTOM", {
        "broadcast_id": broadcast_id,
        "geo": geo.upper(),
        "lang": lang.upper(),
        "method": method.upper(),
        "template": f"custom_template:{final_text}",
        "results": {
            "success": success_count,
            "errors": error_count
        }
    })

    # Кнопка видалення
    delete_kb = InlineKeyboardBuilder()
    delete_kb.row(InlineKeyboardButton(text='🗑 Видалити розсилку', callback_data=f'del_{broadcast_id}'))

    await callback.message.edit_text(
        f"✅ Відправлено успішно: {success_count} чатів.",
        reply_markup=delete_kb.as_markup()
    )
    
    await state.clear()
    await callback.answer()


# Хендлер видалення
@router.callback_query(F.data.startswith("del_"))
async def delete_broadcast_by_button(callback: CallbackQuery, bot: Bot):
    broadcast_id = callback.data.replace("del_", "")
    broadcast_data = config.sent_history.get(broadcast_id)
    
    if not broadcast_data:
        return await callback.answer("❌ Дані про розсилку не знайдені або вже видалені.", show_alert=True)

    geo = broadcast_data.get('geo', 'N/A').upper()
    lang = broadcast_data.get('lang', 'N/A').upper()
    method = broadcast_data.get("method", "ALL").upper()
    # Якщо в історії зберігався тип шаблону (напр. 'low_sr'), витягуємо його
    tmpl_type = broadcast_data.get("template_type") or broadcast_data.get("type") or broadcast_data.get("template") or "CUSTOM"

    messages_to_delete = broadcast_data.get('messages', [])
    deleted_count = 0

    for chat_id, msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            deleted_count += 1
        except Exception as e:
            print(f"Не вдалося видалити в {chat_id}: {e}")

    # 4. Логуємо видалення
    config.write_event_log("DELETE_SPECIFIC", {
        "broadcast_id": broadcast_id,
        "geo": geo,
        "lang": lang,
        "method": method,
        "template": tmpl_type,
        "deleted_messages": deleted_count
    })

    # 5. Видаляємо запис з історії та зберігаємо
    del config.sent_history[broadcast_id]
    config.save_history(config.sent_history)

    geo = broadcast_data.get('geo')
    lang = broadcast_data.get('lang')
    method = broadcast_data.get("method", "ALL")
    # 6. Оновлюємо повідомлення в адмінці
    await callback.message.edit_text(
        f"🗑 <b>Розсилку видалено з усіх чатів</b>\n\n"
        f"📍 {geo} | 🗣 {lang} | 🛠 {method}\n"
        f"📊 Видалено повідомлень: {deleted_count}",
        parse_mode="HTML"
    )
    await callback.answer("Видалено!")