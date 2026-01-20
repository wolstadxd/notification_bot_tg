from aiogram import Bot
from aiogram import Router, F
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from config import ALLOWED_USERS, TEMPLATES, CHATS, sent_history
import config
from keyboards import get_geo_kb, get_template_kb, get_lang_kb

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

@router.callback_query(F.data.startswith("lang_"))
async def choose_template(callback: CallbackQuery):
    parts = callback.data.split("_")
    lang = parts[1]
    geo = parts[2]

    await callback.message.edit_text(
        f"ГЕО: {geo.upper()} | Мова: {lang.upper()}\nЯкий шаблон відправити?",
        reply_markup=get_template_kb(lang, geo) # Передаємо далі
    )



@router.callback_query(F.data.startswith('del_'))
async def delete_specific_broadcast(callback: CallbackQuery, bot: Bot):
    broadcast_id = callback.data.split('_')[1]
    if broadcast_id in config.sent_history:
        messages_to_delete = config.sent_history.pop(broadcast_id)
        config.save_history(config.sent_history)
        for c_id, m_id in messages_to_delete:
            try:
                await bot.delete_message(chat_id=c_id, message_id=m_id)
            except Exception as e:
                print(f"Помилка видалення в чаті {c_id}: {e}")

        await callback.answer("Саме цю розсилку видалено всюди!")
        await callback.message.edit_text("🗑 Ця розсилка була повністю видалена з усіх чатів.")
    else:
        await callback.answer("Дані не знайдені або розсилка вже видалена.", show_alert=True)

@router.callback_query(F.data.startswith("tmpl_"))
async def send_broadcast(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    lang = parts[1]        # "ua"
    geo = parts[-1]
    tmpl_type = "_".join(parts[2:-1])

    success_count = 0
    error_count = 0

    try:
        template_text = config.TEMPLATES[lang][tmpl_type].format(geo=geo.upper())
    except KeyError:
        await callback.answer("Помилка: Шаблон не знайдено", show_alert=True)
        return
    
    broadcast_id = str(callback.id)
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

    if success_count == 0 and error_count == 0:
        await callback.message.edit_text(
            f"⚠️ **Чати не знайдені!**\n\nДля напрямку **{geo.upper()}** з мовою **{lang.upper()}** в конфігу немає жодного чату.\nПеревірте теги в `config.py`.",
            reply_markup=get_geo_kb() # Повертаємо на початок
        )
        return # Зупиняємо функцію тут

    config.sent_history[broadcast_id] = temp_messages
    config.save_history(config.sent_history)

    delete_cb=InlineKeyboardBuilder()
    delete_cb.row(InlineKeyboardButton(text='Видалити цю розсилку', callback_data=f'del_{broadcast_id}'))

    await callback.answer("Відправлено!")
    await callback.message.edit_text(f"✅ Розсилка завершена!\nНапрямок: {geo}\nТип: {tmpl_type}\n\n Успішно відправлено: {success_count}, Невдач: {error_count}", reply_markup=delete_cb.as_markup())
    await callback.message.answer("Виберіть наступний напрямок:", reply_markup=get_geo_kb())
    
@router.callback_query(F.data == "back_to_geo")
async def back(callback: CallbackQuery):
    await callback.message.edit_text("Виберіть напрямок:", reply_markup=get_geo_kb())

@router.callback_query(F.data == "delete_last")
async def delete_broadcast(callback: CallbackQuery, bot: Bot):
    if not config.sent_history:
        await callback.answer("Немає розсилок для видалення", show_alert=True)
        return

    last_id = list(config.sent_history.keys())[-1]
    messages = config.sent_history.pop(last_id)

    for c_id, m_id in messages:
        try:
            await bot.delete_message(chat_id=c_id, message_id=m_id)
        except:
            pass

    config.save_history(config.sent_history)
    await callback.answer("Видалено!")
    await callback.message.edit_text("🗑 Повідомлення видалені.")
    await callback.message.answer('Виберіть наступний напрямок:', reply_markup=get_geo_kb())
    
    