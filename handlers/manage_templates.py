from aiogram import Router, F
from database import load_templates, save_templates, load_main_templates
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from database import load_allowed_users
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

class EditTemplate(StatesGroup):
    lang = State()
    template_type = State()
    template_text = State()
    edit_main_template = State()

class AddTemplate(StatesGroup):
    lang = State()
    template_type = State()
    template_text = State()
    main_template = State()

def get_templates_list_data():
    templates = load_templates()
    if not templates:
        return "📭 Шаблони відсутні", None

    text = "📋 <b>Доступні шаблони:</b>\n\n"
    for lang, lang_templates in templates.items():
        text += f"🌐 <b>{lang.upper()}:</b>\n"
        for template_type, tmpl_obj in lang_templates.items():
            # Підтримуємо обидва формати на випадок якщо міграція ще не відбулась
            tmpl_text = tmpl_obj["text"] if isinstance(tmpl_obj, dict) else tmpl_obj
            main_tmpl = tmpl_obj.get("main_template") if isinstance(tmpl_obj, dict) else None
            preview = tmpl_text[:50] + "..." if len(tmpl_text) > 50 else tmpl_text
            linked = f" 🔗 <code>{main_tmpl}</code>" if main_tmpl else ""
            text += f"  • <code>{template_type}</code>{linked}: {preview}\n"
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
        await message.answer("❌ You don't have access")
        return

    text, reply_markup = get_templates_list_data()
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")

@router.callback_query(F.data == "manage_templates")
async def manage_templates_callback(callback: CallbackQuery):
    from database import load_allowed_users
    current_users = load_allowed_users()
    if callback.from_user.id not in current_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return

    text, reply_markup = get_templates_list_data()
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "add_template")
async def add_template_start(callback: CallbackQuery, state: FSMContext):
    from database import load_allowed_users
    current_users = load_allowed_users()
    if callback.from_user.id not in current_users:
        await callback.answer("❌ You don't have access", show_alert=True)
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
    await message.answer(f"📝 Введіть назву шаблону (наприклад: low_sr, tech, p2p_stop):")
    await state.set_state(AddTemplate.template_type)

@router.message(AddTemplate.template_type)
async def process_add_template_type(message: Message, state: FSMContext):
    template_type = message.text.strip()
    await state.update_data(template_type=template_type)
    await message.answer("📝 Введіть текст шаблону. Використовуйте {geo} для підстановки гео:")
    await state.set_state(AddTemplate.template_text)

@router.message(AddTemplate.template_text)
async def process_add_template_text(message: Message, state: FSMContext):
    await state.update_data(template_text=message.text)

    # Показуємо список головних шаблонів для вибору
    main_templates = load_main_templates()

    kb = InlineKeyboardBuilder()
    if main_templates:
        for tmpl_id, tmpl_data in main_templates.items():
            direction = tmpl_data.get("direction", "?")
            event = tmpl_data.get("event", "?")
            kb.row(InlineKeyboardButton(
                text=f"🔗 {tmpl_id}  ({direction} → {event})",
                callback_data=f"add_link_{tmpl_id}"
            ))
    kb.row(InlineKeyboardButton(text="🚫 Без прив'язки", callback_data="add_link_none"))

    if main_templates:
        prompt = (
            "🔗 <b>Прив'язати до головного шаблону?</b>\n\n"
            "Оберіть головний шаблон або натисніть «Без прив'язки»:"
        )
    else:
        prompt = (
            "ℹ️ Головних шаблонів ще немає.\n"
            "Натисніть «Без прив'язки» або спочатку створіть головний шаблон через /manage_main."
        )

    await message.answer(prompt, reply_markup=kb.as_markup(), parse_mode="HTML")
    await state.set_state(AddTemplate.main_template)


@router.callback_query(AddTemplate.main_template, F.data.startswith("add_link_"))
async def process_add_main_template(callback: CallbackQuery, state: FSMContext):
    selected = callback.data.removeprefix("add_link_")
    main_template_value = None if selected == "none" else selected

    data = await state.get_data()
    lang = data['lang']
    template_type = data['template_type']
    template_text = data['template_text']

    templates = load_templates()
    if lang not in templates:
        templates[lang] = {}

    templates[lang][template_type] = {
        "text": template_text,
        "main_template": main_template_value
    }
    save_templates(templates)

    link_info = f"🔗 Прив'язано до: <code>{main_template_value}</code>" if main_template_value else "🚫 Без прив'язки"
    await callback.message.edit_text(
        f"✅ Шаблон <code>{template_type}</code> для мови <code>{lang}</code> додано!\n{link_info}",
        parse_mode="HTML"
    )

    text, reply_markup = get_templates_list_data()
    await callback.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "edit_template")
async def edit_template_start(callback: CallbackQuery, state: FSMContext):
    from database import load_allowed_users
    current_users = load_allowed_users()
    if callback.from_user.id not in current_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return

    await callback.message.edit_text("📝 Введіть мову шаблону (ua/ru/en):")
    await state.set_state(EditTemplate.lang)
    await callback.answer()

@router.message(EditTemplate.lang)
async def process_edit_lang(message: Message, state: FSMContext):
    lang = message.text.strip().lower()
    templates = load_templates()

    if lang not in templates or not templates[lang]:
        await message.answer(f"❌ Для мови <code>{lang}</code> немає шаблонів!", parse_mode="HTML")
        await state.clear()
        return

    await state.update_data(lang=lang)
    await message.answer(f"📝 Введіть назву шаблону для редагування (доступні: {', '.join(templates[lang].keys())}):")
    await state.set_state(EditTemplate.template_type)

@router.message(EditTemplate.template_type)
async def process_edit_template_type(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    template_type = message.text.strip()
    templates = load_templates()

    if lang not in templates or template_type not in templates[lang]:
        await message.answer(f"❌ Шаблон <code>{template_type}</code> для мови <code>{lang}</code> не знайдено!", parse_mode="HTML")
        await state.clear()
        return

    tmpl_obj = templates[lang][template_type]
    current_text = tmpl_obj["text"] if isinstance(tmpl_obj, dict) else tmpl_obj

    await state.update_data(template_type=template_type)
    await message.answer(f"📝 Поточний текст:\n\n{current_text}\n\nВведіть новий текст шаблону:")
    await state.set_state(EditTemplate.template_text)

@router.message(EditTemplate.template_text)
async def process_edit_template_text(message: Message, state: FSMContext):
    await state.update_data(new_text=message.text)

    data = await state.get_data()
    lang = data['lang']
    template_type = data['template_type']
    templates = load_templates()
    tmpl_obj = templates[lang][template_type]
    current_main = tmpl_obj.get("main_template") if isinstance(tmpl_obj, dict) else None

    main_templates = load_main_templates()

    kb = InlineKeyboardBuilder()
    if main_templates:
        for tmpl_id, tmpl_data in main_templates.items():
            direction = tmpl_data.get("direction", "?")
            event = tmpl_data.get("event", "?")
            prefix = "✅" if tmpl_id == current_main else "🔗"
            kb.row(InlineKeyboardButton(
                text=f"{prefix} {tmpl_id}  ({direction} → {event})",
                callback_data=f"edit_link_{tmpl_id}"
            ))
    kb.row(InlineKeyboardButton(text="🚫 Без прив'язки", callback_data="edit_link_none"))
    kb.row(InlineKeyboardButton(text="⏩ Залишити як є", callback_data=f"edit_link_keep"))

    current_info = f"Поточна прив'язка: <code>{current_main}</code>" if current_main else "Поточна прив'язка: немає"
    await message.answer(
        f"🔗 <b>Прив'язка до головного шаблону</b>\n{current_info}\n\n"
        f"Оберіть головний шаблон або залиште як є:",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(EditTemplate.edit_main_template)


@router.callback_query(EditTemplate.edit_main_template, F.data.startswith("edit_link_"))
async def process_edit_main_template(callback: CallbackQuery, state: FSMContext):
    selected = callback.data.removeprefix("edit_link_")

    data = await state.get_data()
    lang = data['lang']
    template_type = data['template_type']
    new_text = data['new_text']

    templates = load_templates()
    tmpl_obj = templates[lang][template_type]
    old_main = tmpl_obj.get("main_template") if isinstance(tmpl_obj, dict) else None

    if selected == "keep":
        main_template_value = old_main
    elif selected == "none":
        main_template_value = None
    else:
        main_template_value = selected

    templates[lang][template_type] = {
        "text": new_text,
        "main_template": main_template_value
    }
    save_templates(templates)

    link_info = f"🔗 Прив'язано до: <code>{main_template_value}</code>" if main_template_value else "🚫 Без прив'язки"
    await callback.message.edit_text(
        f"✅ Шаблон <code>{template_type}</code> для мови <code>{lang}</code> оновлено!\n{link_info}",
        parse_mode="HTML"
    )

    text, reply_markup = get_templates_list_data()
    await callback.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "delete_template")
async def delete_template_start(callback: CallbackQuery, state: FSMContext):
    templates = load_templates()
    if not templates:
        await callback.answer("📭 Шаблони відсутні", show_alert=True)
        return

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

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text="✅ ТАК, ВИДАЛИТИ",
        callback_data=f"cfm_del_tmpl_{lang}_{template_type}"
    ))
    kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data="manage_templates"))

    await callback.message.edit_text(
        f"⚠️ Ви впевнені, що хочете видалити шаблон <code>{template_type}</code> для мови <code>{lang}</code>?",
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

        if not templates[lang]:
            del templates[lang]

        save_templates(templates)
        await callback.message.edit_text(
            f"✅ Шаблон <code>{template_type}</code> для мови <code>{lang}</code> видалено!",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text("❌ Шаблон не знайдено")

    await callback.answer()

@router.callback_query(F.data == "cancel_delete_template")
async def cancel_delete_template(callback: CallbackQuery):
    text, reply_markup = get_templates_list_data()
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    await callback.answer()
