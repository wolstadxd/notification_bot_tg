from aiogram import Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from database import load_chats
import config
from keyboards import get_geo_kb, get_yes_no_custom_kb, back_to_geo

router = Router()

class Custom(StatesGroup):
    geo = State()
    text = State()
    lang = State()

@router.callback_query(F.data.startswith("custom_"))
async def listening_new_text(callback: CallbackQuery, state: FSMContext):
    geo_name = callback.data.split("_")[1]
    lang_name = callback.data.split("_")[2]
    await state.update_data(geo=geo_name)
    await state.update_data(lang=lang_name)
    await callback.message.edit_text(
        f"Напишіть костомну розсилку:\nГЕО: {geo_name.upper()} | Мова: {lang_name.upper()}",
        reply_markup=back_to_geo()
    )
    await state.set_state(Custom.text)
    await callback.answer()

@router.callback_query(F.data == "back_to_geo", Custom.text)
async def back_to_geo_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Виберіть напрямок для інформування:", 
        reply_markup=get_geo_kb()
    )
    await callback.answer()

@router.message(Custom.text)
async def check_text(message: Message, state: FSMContext):
    await state.update_data(user_text = message.text)
    data = await state.get_data()
    geo_from_state = data.get('geo')
    text_from_state = data.get('user_text')
    lang_from_state = data.get('lang')

    await message.answer(
        f'Ось твій текст для гео {geo_from_state.upper()} та мови {lang_from_state.upper()}:\n\n{text_from_state}\n\n Надсилати?',
        reply_markup=get_yes_no_custom_kb()
    )

@router.callback_query(F.data.startswith('yes_custom'))
async def send_custom_templeate(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    geo = data.get('geo').lower()
    lang = data.get('lang').lower()
    final_text = data.get('user_text')

    success_count = 0
    error_count = 0

    broadcast_id = str(callback.id)
    temp_messages = []

    chats = load_chats()
    for chat in chats:
        if geo in chat["tags"] and lang in chat["tags"]:
            try:
                mentions_list = chat.get("mentions", [])
                mentions_text = "\n\n" + " ".join(mentions_list) if mentions_list else ""
                full_message_text = final_text + mentions_text

                msg = await bot.send_message(
                    chat_id=chat["id"], 
                    text=full_message_text,
                    parse_mode="Markdown"
                )

                temp_messages.append((chat["id"], msg.message_id))
                
                success_count += 1
            except Exception as e:
                print(f"Помилка в {chat['name']}: {e}")
                error_count += 1

    config.sent_history[broadcast_id] = {
        "geo": geo.upper(),
        "lang": lang.upper(),
        "type": f"custom_template:{final_text}",
        "messages": temp_messages
    }
    config.save_history(config.sent_history)

    config.write_event_log("SEND CUSTOM", {
        "broadcast_id": broadcast_id,
        "geo": geo.upper(),
        "lang": lang.upper(),
        "template": f"custom_template:{final_text}",
        "results": {
            "success": success_count,
            "errors": error_count
        }
    })

    delete_kb = InlineKeyboardBuilder()
    delete_kb.row(InlineKeyboardButton(text='🗑 Видалити цю розсилку', callback_data=f'del_{broadcast_id}'))

    await callback.answer("Розсилка завершена!")
    await callback.message.edit_text(f"✅ Твоя розсилка для ГЕО {geo.upper()} | Мова {lang.upper()} виконана:\n\"{final_text}\"\n\nУспішно відправлено: {success_count}, Невдач: {error_count}", reply_markup=delete_kb.as_markup())
    await callback.message.answer("Виберіть наступний напрямок:", reply_markup=get_geo_kb())
    await state.clear()

@router.callback_query(F.data == 'no_custom')
async def cancel_custom(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Повторіть спробу кастомного тексту!")
    await callback.message.edit_text("❌ Скасовано.")
    await callback.message.answer("Виберіть напрямок для інформування:", reply_markup=get_geo_kb())