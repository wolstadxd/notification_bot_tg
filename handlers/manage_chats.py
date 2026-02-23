from aiogram import Router
from database import load_chats, save_chats
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

class AddChat(StatesGroup):
    name = State()
    chat_id = State()
    tags = State()
    mentions = State()

@router.message(Command('add_chat'))
async def add_chat(message: Message, state: FSMContext):
    await message.answer('Введіть назву каналу:')
    await state.set_state(AddChat.name)
    
@router.message(AddChat.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name = message.text)
    await message.answer('Введіть chat_id мерчанта:')
    await state.set_state(AddChat.chat_id)

@router.message(AddChat.chat_id)
async def process_id(message: Message, state: FSMContext):
    await state.update_data(chat_id = int(message.text))
    await message.answer('Введіть теги мерчанта через пробіл (гео, мова) - peru ua:')
    await state.set_state(AddChat.tags)

@router.message(AddChat.tags)
async def process_tags(message: Message, state: FSMContext):
    tags_list = message.text.split() 
    await state.update_data(tags=tags_list)
    
    await state.set_state(AddChat.mentions)
    await message.answer('Введіть юзернеми через пробіл (@test1 @test2) або "ні"')


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

    await message.answer(f"✅ Чат '{user_data['name']}' успішно додано до загального списку!")
    await state.clear()