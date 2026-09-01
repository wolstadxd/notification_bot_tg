import html
from aiogram import Router, F
from database import load_templates, save_templates, load_main_templates, load_allowed_users
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
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


def get_templates_main_menu():
    templates = load_templates()
    ua_count = len(templates.get("ua", {}))
    ru_count = len(templates.get("ru", {}))
    en_count = len(templates.get("en", {}))
    total_count = ua_count + ru_count + en_count

    text = (
        "📝 <b>Керування шаблонами</b>\n\n"
        f"Всього шаблонів у базі: <b>{total_count}</b>\n\n"
        "Оберіть мову для перегляду та керування:"
    )

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"🇺🇦 UA ({ua_count})", callback_data="tmpl_view_ua"))
    kb.row(InlineKeyboardButton(text=f"🇷🇺 RU ({ru_count})", callback_data="tmpl_view_ru"))
    kb.row(InlineKeyboardButton(text=f"🇬🇧 EN ({en_count})", callback_data="tmpl_view_en"))
    kb.row(InlineKeyboardButton(text="➕ Додати новий шаблон", callback_data="add_template"))
    kb.row(InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu"))

    return text, kb.as_markup()


def get_lang_templates_data(lang: str):
    templates = load_templates()
    lang_templates = templates.get(lang, {})
    flag = {"ua": "🇺🇦", "ru": "🇷🇺", "en": "🇬🇧"}.get(lang, "🌐")

    if not lang_templates:
        text = f"{flag} <b>Шаблони {lang.upper()}:</b>\n\n📭 Шаблони відсутні для цієї мови."
    else:
        text = f"{flag} <b>Шаблони {lang.upper()} ({len(lang_templates)}):</b>\n\n"
        for template_type, tmpl_obj in lang_templates.items():
            tmpl_text = tmpl_obj["text"] if isinstance(tmpl_obj, dict) else tmpl_obj
            main_tmpl = tmpl_obj.get("main_template") if isinstance(tmpl_obj, dict) else None
            preview = tmpl_text[:50] + "..." if len(tmpl_text) > 50 else tmpl_text

            safe_type = html.escape(str(template_type))
            safe_preview = html.escape(str(preview))
            safe_main = html.escape(str(main_tmpl)) if main_tmpl else None

            linked = f" 🔗 <code>{safe_main}</code>" if safe_main else ""
            text += f"  • <code>{safe_type}</code>{linked}: {safe_preview}\n"

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text=f"➕ Додати шаблон ({lang.upper()})", callback_data=f"add_template_{lang}"))
    kb.row(InlineKeyboardButton(text=f"✏️ Редагувати ({lang.upper()})", callback_data=f"edit_template_{lang}"))
    kb.row(InlineKeyboardButton(text=f"🗑 Видалити ({lang.upper()})", callback_data=f"delete_template_{lang}"))
    kb.row(InlineKeyboardButton(text="⬅️ До вибору мови", callback_data="manage_templates"))

    return text, kb.as_markup()


@router.message(Command("manage_templates"))
async def manage_templates_cmd(message: Message):
    allowed_users = load_allowed_users()
    if message.from_user.id not in allowed_users:
        await message.answer("❌ You don't have access")
        return

    text, reply_markup = get_templates_main_menu()
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")


@router.callback_query(F.data == "manage_templates")
async def manage_templates_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    current_users = load_allowed_users()
    if callback.from_user.id not in current_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return

    text, reply_markup = get_templates_main_menu()
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("tmpl_view_"))
async def tmpl_view_lang_callback(callback: CallbackQuery):
    current_users = load_allowed_users()
    if callback.from_user.id not in current_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return

    lang = callback.data.removeprefix("tmpl_view_")
    text, reply_markup = get_lang_templates_data(lang)
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    await callback.answer()


# ==================== ДОДАВАННЯ ШАБЛОНУ ====================

@router.callback_query(F.data.startswith("add_template"))
async def add_template_start(callback: CallbackQuery, state: FSMContext):
    current_users = load_allowed_users()
    if callback.from_user.id not in current_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return

    if callback.data.startswith("add_template_"):
        lang = callback.data.removeprefix("add_template_")
        await state.update_data(lang=lang)
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data=f"tmpl_view_{lang}"))
        await callback.message.edit_text(
            f"📝 Додавання шаблону для <b>{lang.upper()}</b>.\nВведіть назву шаблону (наприклад: low_sr, tech, p2p_stop):",
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await state.set_state(AddTemplate.template_type)
    else:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="🇺🇦 UA", callback_data="add_template_ua"))
        kb.row(InlineKeyboardButton(text="🇷🇺 RU", callback_data="add_template_ru"))
        kb.row(InlineKeyboardButton(text="🇬🇧 EN", callback_data="add_template_en"))
        kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data="manage_templates"))
        await callback.message.edit_text("📝 Оберіть мову для нового шаблону:", reply_markup=kb.as_markup())

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

    link_info = f"🔗 Прив'язано до: <code>{html.escape(main_template_value)}</code>" if main_template_value else "🚫 Без прив'язки"
    await callback.message.edit_text(
        f"✅ Шаблон <code>{html.escape(template_type)}</code> для мови <code>{lang}</code> додано!\n{link_info}",
        parse_mode="HTML"
    )

    text, reply_markup = get_lang_templates_data(lang)
    await callback.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await state.clear()
    await callback.answer()


# ==================== РЕДАГУВАННЯ ШАБЛОНУ ====================

@router.callback_query(F.data.startswith("edit_template"))
async def edit_template_start(callback: CallbackQuery, state: FSMContext):
    current_users = load_allowed_users()
    if callback.from_user.id not in current_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return

    templates = load_templates()

    if callback.data.startswith("edit_template_"):
        lang = callback.data.removeprefix("edit_template_")
        if lang not in templates or not templates[lang]:
            await callback.answer(f"❌ Для мови {lang.upper()} немає шаблонів!", show_alert=True)
            return

        await state.update_data(lang=lang)
        kb = InlineKeyboardBuilder()
        for tmpl_name in templates[lang].keys():
            kb.row(InlineKeyboardButton(text=f"✏️ {tmpl_name}", callback_data=f"sel_edit_tmpl_{tmpl_name}"))
        kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data=f"tmpl_view_{lang}"))

        await callback.message.edit_text(
            f"📝 Оберіть шаблон <b>{lang.upper()}</b> для редагування:",
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
        await state.set_state(EditTemplate.template_type)
    else:
        kb = InlineKeyboardBuilder()
        kb.row(InlineKeyboardButton(text="🇺🇦 UA", callback_data="edit_template_ua"))
        kb.row(InlineKeyboardButton(text="🇷🇺 RU", callback_data="edit_template_ru"))
        kb.row(InlineKeyboardButton(text="🇬🇧 EN", callback_data="edit_template_en"))
        kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data="manage_templates"))
        await callback.message.edit_text("📝 Оберіть мову шаблону для редагування:", reply_markup=kb.as_markup())

    await callback.answer()


@router.callback_query(EditTemplate.template_type, F.data.startswith("sel_edit_tmpl_"))
async def process_select_edit_template(callback: CallbackQuery, state: FSMContext):
    template_type = callback.data.removeprefix("sel_edit_tmpl_")
    data = await state.get_data()
    lang = data['lang']
    templates = load_templates()

    if lang not in templates or template_type not in templates[lang]:
        await callback.answer("❌ Шаблон не знайдено!", show_alert=True)
        return

    tmpl_obj = templates[lang][template_type]
    current_text = tmpl_obj["text"] if isinstance(tmpl_obj, dict) else tmpl_obj

    await state.update_data(template_type=template_type)
    await callback.message.edit_text(
        f"📝 Редагування: <code>{html.escape(template_type)}</code> ({lang.upper()})\n\n"
        f"<b>Поточний текст:</b>\n{html.escape(current_text)}\n\n"
        f"Введіть новий текст шаблону (або надішліть той самий, якщо змінюєте лише прив'язку):",
        parse_mode="HTML"
    )
    await state.set_state(EditTemplate.template_text)
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
        await message.answer(f"❌ Шаблон <code>{html.escape(template_type)}</code> для мови <code>{lang}</code> не знайдено!", parse_mode="HTML")
        await state.clear()
        return

    tmpl_obj = templates[lang][template_type]
    current_text = tmpl_obj["text"] if isinstance(tmpl_obj, dict) else tmpl_obj

    await state.update_data(template_type=template_type)
    await message.answer(f"📝 <b>Поточний текст:</b>\n\n{html.escape(current_text)}\n\nВведіть новий текст шаблону:", parse_mode="HTML")
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

    current_info = f"Поточна прив'язка: <code>{html.escape(current_main)}</code>" if current_main else "Поточна прив'язка: немає"
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

    link_info = f"🔗 Прив'язано до: <code>{html.escape(main_template_value)}</code>" if main_template_value else "🚫 Без прив'язки"
    await callback.message.edit_text(
        f"✅ Шаблон <code>{html.escape(template_type)}</code> для мови <code>{lang}</code> оновлено!\n{link_info}",
        parse_mode="HTML"
    )

    text, reply_markup = get_lang_templates_data(lang)
    await callback.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await state.clear()
    await callback.answer()


# ==================== ВИДАЛЕННЯ ШАБЛОНУ ====================

@router.callback_query(F.data.startswith("delete_template"))
async def delete_template_start(callback: CallbackQuery, state: FSMContext):
    templates = load_templates()
    if not templates:
        await callback.answer("📭 Шаблони відсутні", show_alert=True)
        return

    if callback.data.startswith("delete_template_"):
        lang = callback.data.removeprefix("delete_template_")
        lang_templates = templates.get(lang, {})
        if not lang_templates:
            await callback.answer(f"📭 Немає шаблонів для {lang.upper()}", show_alert=True)
            return

        kb = InlineKeyboardBuilder()
        for template_type in lang_templates.keys():
            kb.row(InlineKeyboardButton(
                text=f"🗑 {template_type}",
                callback_data=f"rem_tmpl_{lang}_{template_type}"
            ))
        kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data=f"tmpl_view_{lang}"))
        await callback.message.edit_text(f"🗑 Оберіть шаблон <b>{lang.upper()}</b> для видалення:", reply_markup=kb.as_markup(), parse_mode="HTML")
    else:
        kb = InlineKeyboardBuilder()
        for lang, lang_templates in templates.items():
            for template_type in lang_templates.keys():
                kb.row(InlineKeyboardButton(
                    text=f"{lang.upper()}: {template_type}",
                    callback_data=f"rem_tmpl_{lang}_{template_type}"
                ))
        kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data="manage_templates"))
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
    kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data=f"tmpl_view_{lang}"))

    await callback.message.edit_text(
        f"⚠️ Ви впевнені, що хочете видалити шаблон <code>{html.escape(template_type)}</code> для мови <code>{lang}</code>?",
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
            f"✅ Шаблон <code>{html.escape(template_type)}</code> для мови <code>{lang}</code> видалено!",
            parse_mode="HTML"
        )
        text, reply_markup = get_lang_templates_data(lang)
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    else:
        await callback.message.edit_text("❌ Шаблон не знайдено")

    await callback.answer()


@router.callback_query(F.data == "cancel_delete_template")
async def cancel_delete_template(callback: CallbackQuery):
    text, reply_markup = get_templates_main_menu()
    await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    await callback.answer()

