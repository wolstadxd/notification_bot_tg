from aiogram import Router, F
from database import load_templates, save_templates
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import load_allowed_users
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

router = Router()

class EditTemplate(StatesGroup):
    lang = State()
    template_type = State()
    template_text = State()

class AddTemplate(StatesGroup):
    lang = State()
    template_type = State()
    template_text = State()

def get_templates_list_data():
    templates = load_templates()
    if not templates:
        return "📭 Шаблони відсутні", None
    
    text = "📋 **Доступні шаблони:**\n\n"
    for lang, lang_templates in templates.items():
        text += f"🌐 **{lang.upper()}:**\n"
        for template_type, template_text in lang_templates.items():
            preview = template_text[:50] + "..." if len(template_text) > 50 else template_text
            text += f"  • `{template_type}`: {preview}\n"
        text += "\n"
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ Додати шаблон", callback_data="add_template"))
    kb.row(InlineKeyboardButton(text="✏️ Редагувати шаблон", callback_data="edit_template"))
    kb.row(InlineKeyboardButton(text="🗑 Видалити шаблон", callback_data="delete_template"))
    kb.row(InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu"))
    
    return text, kb.as_markup()

@router.message(Command("."))
async def manage_templates_cmd(message: Message):
    allowed_users = load_allowed_users()
    if message.from_user.id not in allowed_users:
        await message.answer("❌ У вас немає доступу")
        return
    
    text, reply_markup = get_templates_list_data()
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")

@router.callback_query(F.data == "manage_templates")
async def manage_templates_callback(callback: CallbackQuery):
    from database import load_allowed_users
    current_users = load_allowed_users()
    if callback.from_user.id not in current_users:
        await callback.answer("❌ У вас немає доступу", show_alert=True)
        return
    
    text, reply_markup = get_templates_list_data()
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "add_template")
async def add_template_start(callback: CallbackQuery, state: FSMContext):
    from database import load_allowed_users
    current_users = load_allowed_users()
    if callback.from_user.id not in current_users:
        await callback.answer("❌ У вас немає доступу", show_alert=True)
        return
    
    await callback.message.edit_text("📝 Введіть мову шаблону (ua/ru/en):")
    await state.set_state(AddTemplate.lang)
    await callback.answer()

@router.message(AddTemplate.lang)
async def process_add_lang(message: Message, state: FSMContext):
    lang = message.text.strip().lower()
    if lang not in ['ua', 'ru', 'en']:
        await message.answer("❌ Невірна мова! Введіть: ua, ru або en")
        return
    
    await state.update_data(lang=lang)
    await message.answer(f"📝 Введіть тип шаблону (наприклад: low_sr, tech, fixed):")
    await state.set_state(AddTemplate.template_type)

@router.message(AddTemplate.template_type)
async def process_add_template_type(message: Message, state: FSMContext):
    template_type = message.text.strip()
    await state.update_data(template_type=template_type)
    await message.answer("📝 Введіть текст шаблону. Використовуйте {geo} для підстановки гео:")
    await state.set_state(AddTemplate.template_text)

@router.message(AddTemplate.template_text)
async def process_add_template_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    template_type = data['template_type']
    template_text = message.text
    
    templates = load_templates()
    
    if lang not in templates:
        templates[lang] = {}
    
    templates[lang][template_type] = template_text
    save_templates(templates)
    
    await message.answer(f"✅ Шаблон `{template_type}` для мови `{lang}` успішно додано!")
    
    text, reply_markup = get_templates_list_data()
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    
    await state.clear()

@router.callback_query(F.data == "edit_template")
async def edit_template_start(callback: CallbackQuery, state: FSMContext):
    from database import load_allowed_users
    current_users = load_allowed_users()
    if callback.from_user.id not in current_users:
        await callback.answer("❌ У вас немає доступу", show_alert=True)
        return
    
    await callback.message.edit_text("📝 Введіть мову шаблону (ua/ru/en):")
    await state.set_state(EditTemplate.lang)
    await callback.answer()

@router.message(EditTemplate.lang)
async def process_edit_lang(message: Message, state: FSMContext):
    lang = message.text.strip().lower()
    templates = load_templates()
    
    if lang not in templates or not templates[lang]:
        await message.answer(f"❌ Для мови `{lang}` немає шаблонів!")
        await state.clear()
        return
    
    await state.update_data(lang=lang)
    await message.answer(f"📝 Введіть тип шаблону для редагування (доступні: {', '.join(templates[lang].keys())}):")
    await state.set_state(EditTemplate.template_type)

@router.message(EditTemplate.template_type)
async def process_edit_template_type(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    template_type = message.text.strip()
    templates = load_templates()
    
    if lang not in templates or template_type not in templates[lang]:
        await message.answer(f"❌ Шаблон `{template_type}` для мови `{lang}` не знайдено!")
        await state.clear()
        return
    
    await state.update_data(template_type=template_type)
    await message.answer(f"📝 Поточний текст:\n\n{templates[lang][template_type]}\n\nВведіть новий текст шаблону:")
    await state.set_state(EditTemplate.template_text)

@router.message(EditTemplate.template_text)
async def process_edit_template_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    template_type = data['template_type']
    template_text = message.text
    
    templates = load_templates()
    templates[lang][template_type] = template_text
    save_templates(templates)
    
    await message.answer(f"✅ Шаблон `{template_type}` для мови `{lang}` успішно оновлено!")
    
    text, reply_markup = get_templates_list_data()
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    
    await state.clear()

@router.callback_query(F.data == "delete_template")
async def delete_template_start(callback: CallbackQuery, state: FSMContext):
    templates = load_templates()
    if not templates:
        await callback.answer("📭 Шаблони відсутні", show_alert=True)
        return
    
    # Створюємо клавіатуру з доступними шаблонами
    kb = InlineKeyboardBuilder()
    for lang, lang_templates in templates.items():
        for template_type in lang_templates.keys():
            kb.row(InlineKeyboardButton(
                text=f"{lang.upper()}: {template_type}",
                callback_data=f"rem_tmpl_{lang}_{template_type}"
            ))
    kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data="cancel_delete_template"))
    
    await callback.message.edit_text("🗑 Оберіть шаблон для видалення:", reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("rem_tmpl_"))
async def confirm_delete_template(callback: CallbackQuery):
    parts = callback.data.split("_")
    lang = parts[2]
    template_type = "_".join(parts[3:])
    
    templates = load_templates()
    
    if lang not in templates or template_type not in templates[lang]:
        await callback.answer("❌ Шаблон не знайдено", show_alert=True)
        return
    
    # Підтвердження
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text="✅ ТАК, ВИДАЛИТИ",
        callback_data=f"cfm_del_tmpl_{lang}_{template_type}"
    ))
    kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data="manage_templates"))
    
    await callback.message.edit_text(
        f"⚠️ Ви впевнені, що хочете видалити шаблон `{template_type}` для мови `{lang}`?",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("cfm_del_tmpl_"))
async def real_delete_template(callback: CallbackQuery):
    parts = callback.data.split("_")
    lang = parts[3]
    template_type = "_".join(parts[4:])
    
    templates = load_templates()
    
    if lang in templates and template_type in templates[lang]:
        del templates[lang][template_type]
        
        # Якщо мова порожня, видаляємо її теж
        if not templates[lang]:
            del templates[lang]
        
        save_templates(templates)
        await callback.message.edit_text(f"✅ Шаблон `{template_type}` для мови `{lang}` видалено!")
    else:
        await callback.message.edit_text("❌ Шаблон не знайдено")
    
    await callback.answer()

@router.callback_query(F.data == "cancel_delete_template")
async def cancel_delete_template(callback: CallbackQuery):
    text, reply_markup = get_templates_list_data()
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    await callback.answer()
