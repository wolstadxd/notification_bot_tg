from aiogram import Bot
from aiogram import Router, F
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from config import ALLOWED_USERS, TEMPLATES, CHATS, sent_history, write_event_log
import config
from keyboards import get_geo_kb, get_template_kb, get_lang_kb, get_lang_kb_all

router = Router()

@router.message(Command("admin"))
async def open_admin(message: Message):
    if message.from_user.id in ALLOWED_USERS:
        await message.answer("Виберіть напрямок для інформування:", reply_markup=get_geo_kb())
    else:
        await message.answer("Вибачте, у вас немає доступу до керування розсилкою.")

@router.callback_query(F.data.startswith("geo_"))
async def choose_language(callback: CallbackQuery):
    geo = callback.data.split("_")[1]
    await callback.message.edit_text(
        f"Вибрано ГЕО: {geo.upper()}\nВиберіть мову розсилки:", 
        reply_markup=get_lang_kb(geo)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("lang_"))
async def choose_template(callback: CallbackQuery):
    parts = callback.data.split("_")
    lang = parts[1]
    geo = parts[2]

    chats_exist = any(geo in chat["tags"] and lang in chat["tags"] for chat in CHATS)

    if not chats_exist:
        await callback.message.edit_text(
            f"⚠️ **Чати не знайдені!**\n\nДля напрямку **{geo.upper()}** з мовою **{lang.upper()}** в конфігу немає жодного чату.\nПеревірте теги в `config.py`.",
            reply_markup=get_geo_kb()
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"ГЕО: {geo.upper()} | Мова: {lang.upper()}\nЯкий шаблон відправити?",
        reply_markup=get_template_kb(lang, geo)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("tmpl_"))
async def send_broadcast(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    lang = parts[1]
    geo = parts[-1]
    tmpl_type = "_".join(parts[2:-1])

    success_count = 0
    error_count = 0

    try:
        template_text = config.TEMPLATES[lang][tmpl_type].format(geo=geo.upper())
    except KeyError:
        await callback.answer("Помилка: Шаблон не знайдено", show_alert=True)
        return

    temp_messages = []

    for chat in CHATS:
        if geo in chat["tags"] and lang in chat["tags"]:
            try:
                mentions_list = chat.get("mentions", [])
                mentions_text = "\n\n" + " ".join(mentions_list) if mentions_list else ""
                full_message_text = template_text + mentions_text
                msg = await bot.send_message(chat_id=chat["id"], text=full_message_text, parse_mode="Markdown")
                temp_messages.append((chat["id"], msg.message_id))
                success_count += 1
            except Exception as e:
                print(f"Помилка в {chat['name']}: {e}")
                error_count += 1

    broadcast_id = str(callback.id)
    config.sent_history[broadcast_id] = {
        "geo": geo.upper(),
        "lang": lang.upper(),
        "type": tmpl_type,
        "messages": temp_messages  # Тут наші [(chat_id, msg_id)]
    }
    config.save_history(config.sent_history)

    # 2. Пишемо у "Вічну книгу" для СТО (Пункт 1 твого плану)
    config.write_event_log("SEND", {
        "broadcast_id": broadcast_id,
        "geo": geo.upper(),
        "lang": lang.upper(),
        "template": tmpl_type,
        "results": {
            "success": success_count,
            "errors": error_count
        }
    })

    delete_cb=InlineKeyboardBuilder()
    delete_cb.row(InlineKeyboardButton(text='Видалити цю розсилку', callback_data=f'del_{broadcast_id}'))

    await callback.answer("Відправлено!")
    await callback.message.edit_text(f"✅ Розсилка завершена!\nНапрямок: {geo.upper()} | Мова: {lang.upper()}\nТип: {tmpl_type}\n\n Успішно відправлено: {success_count}, Невдач: {error_count}", reply_markup=delete_cb.as_markup())
    await callback.message.answer("Виберіть наступний напрямок:", reply_markup=get_geo_kb())


@router.callback_query(F.data == "delete_last")
async def delete_last_broadcast(callback: CallbackQuery, bot: Bot):
    if not config.sent_history:
        await callback.answer("Немає розсилок для видалення", show_alert=True)
        return

    last_id = list(config.sent_history.keys())[-1]
    broadcast_data = config.sent_history[last_id]

    messages_to_delete = broadcast_data.get('messages', [])
    geo = broadcast_data.get("geo", "Невідомо")
    lang = broadcast_data.get("lang", "Невідомо")

    deleted_count = 0

    for chat_id, msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
            deleted_count += 1
        except Exception as e:
            print(f"Не вдалося видалити в {chat_id}: {e}")

    if geo == "all merchants":
        next_kb = get_lang_kb_all()
        text_suffix = "вибору мови для всіх мерчантів"
    else:
        next_kb = get_geo_kb()
        text_suffix = "вибору ГЕО"

    config.write_event_log('DELETE_LAST', {
        "broadcast_id": last_id,
        "geo": geo,
        "deleted_count": deleted_count
    })

    del config.sent_history[last_id]
    config.save_history(config.sent_history)
    
    await callback.answer("Видалено!")
    await callback.message.edit_text(f"🗑 Видалено останню розсилку:\n\nПовідомлень:{deleted_count}\nГЕО: {geo}\nМова: {lang}")
    await callback.message.answer(f'Повертаємось до {text_suffix}:', reply_markup=next_kb)
    

@router.callback_query(F.data.startswith('del_'))
async def delete_specific_broadcast(callback: CallbackQuery, bot: Bot):
    broadcast_id = callback.data.split('_')[1]
    if broadcast_id not in config.sent_history:
        await callback.answer("Дані не знайдені або розсилка вже видалена.", show_alert=True)
        return
        
    broadcast_data = config.sent_history[broadcast_id]
    messages_to_delete = broadcast_data.get('messages', [])
    geo = broadcast_data.get("geo", "Невідомо") 
    lang = broadcast_data.get('lang', 'Невідомо')   
    type = broadcast_data.get('type', 'Невідомо')   

    deleted_count = 0
    for c_id, m_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=c_id, message_id=m_id)
            deleted_count += 1
        except Exception as e:
            print(f"Помилка видалення в чаті {c_id}: {e}")

    config.write_event_log("DELETE_SPECIFIC", {
        "broadcast_id": broadcast_id,
        "geo": geo,
        "lang": lang,
        "template": type,
        "deleted_messages": deleted_count
    })

    del config.sent_history[broadcast_id]
    config.save_history(config.sent_history)

    await callback.answer("Саме цю розсилку видалено всюди!")
    await callback.message.edit_text("🗑 Ця розсилка була повністю видалена з усіх чатів.")

@router.callback_query(F.data == "back_to_geo")
async def back_to_geo(callback: CallbackQuery):
    await callback.message.edit_text(f"Виберіть напрямок для інформування:", reply_markup=get_geo_kb())
    await callback.answer()
    