from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from database import load_allowed_users, load_main_templates, save_main_templates
from handlers.states import ManageMainTemplateStates

router = Router()


def get_main_templates_menu_text():
    main_templates = load_main_templates()
    if not main_templates:
        text = "🗂 <b>Головні шаблони</b>\n\n📭 Список порожній."
    else:
        text = "🗂 <b>Головні шаблони:</b>\n\n"
        for tmpl_id, tmpl_data in main_templates.items():
            direction = tmpl_data.get("direction", "?")
            event = tmpl_data.get("event", "?")
            text += f"• <code>{tmpl_id}</code>  ({direction} → {event})\n"
    return text


def get_main_templates_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="➕ Додати", callback_data="mt_add"))
    kb.row(InlineKeyboardButton(text="✏️ Редагувати", callback_data="mt_edit"))
    kb.row(InlineKeyboardButton(text="🗑 Видалити", callback_data="mt_delete"))
    kb.row(InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu"))
    return kb.as_markup()


@router.message(Command("manage_main"))
async def manage_main_cmd(message: Message, state: FSMContext):
    allowed_users = load_allowed_users()
    if message.from_user.id not in allowed_users:
        await message.answer("❌ You don't have access")
        return
    await state.clear()
    await message.answer(
        get_main_templates_menu_text(),
        reply_markup=get_main_templates_menu_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "manage_main")
async def manage_main_callback(callback: CallbackQuery, state: FSMContext):
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        get_main_templates_menu_text(),
        reply_markup=get_main_templates_menu_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


# ── Додати головний шаблон ──────────────────────────────────────────────────

@router.callback_query(F.data == "mt_add")
async def mt_add_start(callback: CallbackQuery, state: FSMContext):
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data="manage_main"))

    await callback.message.edit_text(
        "➕ <b>Новий головний шаблон</b>\n\n"
        "Введіть <b>напрямок</b> (direction).\n"
        "Це тег чатів, наприклад: <code>p2p</code>, <code>card</code>, <code>quasi</code>",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(ManageMainTemplateStates.direction)
    await callback.answer()


@router.message(ManageMainTemplateStates.direction)
async def mt_add_direction(message: Message, state: FSMContext):
    direction = message.text.strip().lower()
    if not direction or " " in direction:
        await message.answer("❌ Напрямок не може містити пробілів. Спробуйте ще раз:")
        return

    data = await state.get_data()
    # Якщо це редагування — зберігаємо editing_id
    await state.update_data(direction=direction)

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data="manage_main"))

    await message.answer(
        f"✅ Напрямок: <code>{direction}</code>\n\n"
        "Тепер введіть <b>подію</b> (event).\n"
        "Наприклад: <code>stop</code>, <code>limit_500</code>, <code>start</code>",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(ManageMainTemplateStates.event)


@router.message(ManageMainTemplateStates.event)
async def mt_add_event(message: Message, state: FSMContext):
    event = message.text.strip().lower()
    if not event or " " in event:
        await message.answer("❌ Подія не може містити пробілів. Спробуйте ще раз:")
        return

    data = await state.get_data()
    direction = data["direction"]
    editing_id = data.get("editing_id")  # None якщо додавання, ID якщо редагування
    tmpl_id = f"{direction}_{event}"

    main_templates = load_main_templates()

    # Якщо це редагування — видаляємо старий
    if editing_id:
        if editing_id in main_templates:
            del main_templates[editing_id]

        # Оновлюємо main_template у регулярних шаблонах
        from database import load_templates, save_templates
        templates = load_templates()
        for lang, lang_templates in templates.items():
            for tmpl_name, tmpl_obj in lang_templates.items():
                if isinstance(tmpl_obj, dict) and tmpl_obj.get("main_template") == editing_id:
                    tmpl_obj["main_template"] = tmpl_id
        save_templates(templates)

        action_text = f"✏️ Головний шаблон <code>{editing_id}</code> → <code>{tmpl_id}</code> оновлено!"
    else:
        if tmpl_id in main_templates:
            await message.answer(
                f"❌ Головний шаблон <code>{tmpl_id}</code> вже існує!",
                parse_mode="HTML"
            )
            await state.clear()
            return
        action_text = f"✅ Головний шаблон <code>{tmpl_id}</code> створено!"

    main_templates[tmpl_id] = {"direction": direction, "event": event}
    save_main_templates(main_templates)
    await state.clear()

    await message.answer(
        f"{action_text}\n"
        f"Direction: <code>{direction}</code> → Event: <code>{event}</code>",
        reply_markup=get_main_templates_menu_kb(),
        parse_mode="HTML"
    )


# ── Редагувати головний шаблон ──────────────────────────────────────────────

@router.callback_query(F.data == "mt_edit")
async def mt_edit_start(callback: CallbackQuery):
    main_templates = load_main_templates()
    if not main_templates:
        await callback.answer("📭 Немає головних шаблонів", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    for tmpl_id, tmpl_data in main_templates.items():
        direction = tmpl_data.get("direction", "?")
        event = tmpl_data.get("event", "?")
        kb.row(InlineKeyboardButton(
            text=f"✏️ {tmpl_id}  ({direction} → {event})",
            callback_data=f"mt_edit_{tmpl_id}"
        ))
    kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data="manage_main"))

    await callback.message.edit_text(
        "✏️ Оберіть головний шаблон для редагування:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mt_edit_"))
async def mt_edit_selected(callback: CallbackQuery, state: FSMContext):
    tmpl_id = callback.data.removeprefix("mt_edit_")
    main_templates = load_main_templates()

    if tmpl_id not in main_templates:
        await callback.answer("❌ Шаблон не знайдено", show_alert=True)
        return

    await state.update_data(editing_id=tmpl_id)

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data="manage_main"))

    tmpl_data = main_templates[tmpl_id]
    await callback.message.edit_text(
        f"✏️ Редагування <code>{tmpl_id}</code>\n"
        f"Поточне: {tmpl_data['direction']} → {tmpl_data['event']}\n\n"
        "Введіть новий <b>напрямок</b> (direction):",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await state.set_state(ManageMainTemplateStates.direction)
    await callback.answer()


# ── Видалити головний шаблон ────────────────────────────────────────────────

@router.callback_query(F.data == "mt_delete")
async def mt_delete_start(callback: CallbackQuery):
    main_templates = load_main_templates()
    if not main_templates:
        await callback.answer("📭 Немає головних шаблонів", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    for tmpl_id, tmpl_data in main_templates.items():
        direction = tmpl_data.get("direction", "?")
        event = tmpl_data.get("event", "?")
        kb.row(InlineKeyboardButton(
            text=f"🗑 {tmpl_id}  ({direction} → {event})",
            callback_data=f"mt_rem_{tmpl_id}"
        ))
    kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data="manage_main"))

    await callback.message.edit_text(
        "🗑 Оберіть головний шаблон для видалення:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


# Спочатку перевіряємо confirm (довший префікс), потім звичайний вибір
@router.callback_query(F.data.startswith("mt_rem_yes_"))
async def mt_delete_execute(callback: CallbackQuery):
    tmpl_id = callback.data.removeprefix("mt_rem_yes_")
    main_templates = load_main_templates()

    if tmpl_id in main_templates:
        del main_templates[tmpl_id]
        save_main_templates(main_templates)
        await callback.message.edit_text(
            f"✅ Головний шаблон <code>{tmpl_id}</code> видалено.",
            parse_mode="HTML",
            reply_markup=get_main_templates_menu_kb()
        )
    else:
        await callback.message.edit_text("❌ Шаблон не знайдено.")

    await callback.answer()


@router.callback_query(F.data.startswith("mt_rem_"))
async def mt_delete_confirm(callback: CallbackQuery):
    tmpl_id = callback.data.removeprefix("mt_rem_")
    # Пропускаємо якщо це вже confirm (оброблено вище)
    if tmpl_id.startswith("yes_"):
        return
    main_templates = load_main_templates()

    if tmpl_id not in main_templates:
        await callback.answer("❌ Шаблон не знайдено", show_alert=True)
        return

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(
        text="✅ ТАК, ВИДАЛИТИ",
        callback_data=f"mt_rem_yes_{tmpl_id}"
    ))
    kb.row(InlineKeyboardButton(text="🚫 Скасувати", callback_data="manage_main"))

    await callback.message.edit_text(
        f"⚠️ Видалити головний шаблон <code>{tmpl_id}</code>?\n\n"
        f"Регулярні шаблони що прив'язані до нього <b>НЕ видаляються</b>, "
        f"але їх поле <code>main_template</code> стане недійсним.",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()
