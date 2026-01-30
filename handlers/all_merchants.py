from operator import call
import aiogram
from aiogram import Router, F, Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config
from keyboards import back_to_geo, get_geo_kb, get_lang_kb_all, get_yes_no_custom_kb_all

router = Router()

class CustomAll(StatesGroup):
    text = State()
    lang = State()



@router.callback_query(F.data == "all_merchants")
async def listening_text_all(callback: CallbackQuery):
    await callback.message.edit_text(
        f"Виберіть мову розсилки:",
        reply_markup=get_lang_kb_all()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("all_lang"))
async def choose_lang_all(callback: CallbackQuery, state: FSMContext):
    lang_all = callback.data.split('_')[2]
    await state.update_data(lang=lang_all)
    await callback.message.edit_text(
        f"Введіть текст для усіх мерчантів",
        reply_markup=back_to_geo()
    )
    await state.set_state(CustomAll.text)
    await callback.answer()

@router.message(CustomAll.text)
async def check_text(message: Message, state: FSMContext):
    await state.update_data(text = message.text)
    data = await state.get_data()
    user_text = data.get('text')

    await message.answer(
        f'Ось твій текст для усіх мерчантів:\n\n\"{user_text}\"\n\n Надсилати?',
        reply_markup=get_yes_no_custom_kb_all()
    )

@router.callback_query(F.data.startswith('all_yes_custom'))
async def send_custom_templeate_all(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    final_text = data.get('text')
    all_lang = data.get('lang')
    success_count = 0
    error_count = 0

    broadcast_id = str(callback.id)
    temp_messages = []

    for chat in config.CHATS:
        if 'merchant' in chat["status"] and all_lang in chat["tags"]:
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
        "geo": 'all merchants',
        "lang": all_lang,
        "type": f"custom_template:{final_text}",
        "messages": temp_messages
    }
    config.save_history(config.sent_history)

    config.write_event_log("SEND CUSTOM_ALL", {
        "broadcast_id": broadcast_id,
        "geo": f'all merchants',
        "lang": f'{all_lang}',
        "template": f"custom_template:{final_text}",
        "results": {
            "success": success_count,
            "errors": error_count
        }
    })

    delete_kb = InlineKeyboardBuilder()
    delete_kb.row(InlineKeyboardButton(text='🗑 Видалити цю розсилку', callback_data=f'del_{broadcast_id}'))

    await callback.answer("Розсилка завершена!")
    await callback.message.edit_text(f"✅ Твоя розсилка для усіх виконана:\n\n\"{final_text}\"\n\nУспішно відправлено: {success_count}, Невдач: {error_count}", reply_markup=delete_kb.as_markup())
    await callback.message.answer("Виберіть наступний напрямок:", reply_markup=get_geo_kb())
    await state.clear()


@router.callback_query(F.data == "back_to_geo", CustomAll.text)
async def back_to_geo_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Виберіть напрямок для інформування:", 
        reply_markup=get_geo_kb()
    )
    await callback.answer()