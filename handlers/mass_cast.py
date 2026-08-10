from aiogram import Bot, Router, F
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from handlers.states import MassCastStates
from database import load_chats, load_allowed_users, load_templates, load_main_templates, record_method_broadcast
import config

router = Router()


def get_active_geos():
    """Повертає унікальні ГЕО з тегів чатів (перший тег)."""
    chats = load_chats()
    geos = set()
    for chat in chats:
        tags = chat.get("tags", [])
        if tags:
            geos.add(tags[0])
    return sorted(list(geos))


@router.message(Command("mass_cast"))
async def start_mass_cast(message: Message, state: FSMContext):
    allowed_users = load_allowed_users()
    if message.from_user.id not in allowed_users:
        await message.answer("❌ You don't have access")
        return
    await state.clear()
    await _show_geo_selection(message, state, edit=False)


@router.callback_query(F.data == "mass_cast_start")
async def mass_cast_start_callback(callback: CallbackQuery, state: FSMContext):
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return
    await state.clear()
    await _show_geo_selection(callback.message, state, edit=True)
    await callback.answer()


async def _show_geo_selection(message: Message, state: FSMContext, edit: bool):
    geos = get_active_geos()
    if not geos:
        text = "❌ В базі немає чатів."
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
        return

    kb = InlineKeyboardBuilder()
    for geo in geos:
        kb.row(InlineKeyboardButton(
            text=f"📍 {geo.upper()}",
            callback_data=f"mc_geo_{geo}"
        ))
    kb.row(InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu"))

    await state.set_state(MassCastStates.choosing_geo)

    text = "📢 <b>Mass Cast</b>\n\nВиберіть ГЕО:"
    if edit:
        await message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(MassCastStates.choosing_geo, F.data.startswith("mc_geo_"))
async def choose_main_template(callback: CallbackQuery, state: FSMContext):
    geo = callback.data.removeprefix("mc_geo_")
    await state.update_data(geo=geo)

    main_templates = load_main_templates()
    if not main_templates:
        await callback.message.edit_text(
            "❌ Немає жодного головного шаблону.\n"
            "Спочатку створіть їх через /manage_main",
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return

    # Фільтруємо: показуємо тільки шаблони, для яких є чати з geo + direction
    chats = load_chats()
    available_directions = set()
    for chat in chats:
        tags = chat.get("tags", [])
        if tags and tags[0] == geo:
            for tag in tags[1:]:
                available_directions.add(tag)

    kb = InlineKeyboardBuilder()
    filtered_count = 0
    for tmpl_id, tmpl_data in main_templates.items():
        direction = tmpl_data.get("direction", "?")
        event = tmpl_data.get("event", "?")
        if direction in available_directions:
            kb.row(InlineKeyboardButton(
                text=f"⚡ {direction.upper()} — {event.upper()}",
                callback_data=f"mc_tmpl_{tmpl_id}"
            ))
            filtered_count += 1
    kb.row(InlineKeyboardButton(text="⬅️ Назад до ГЕО", callback_data="mc_back_geo"))

    if filtered_count == 0:
        await callback.message.edit_text(
            f"📍 ГЕО: <b>{geo.upper()}</b>\n\n"
            "❌ Для цього ГЕО немає відповідних головних шаблонів.\n"
            "Перевірте теги чатів та direction головних шаблонів.",
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return

    await state.set_state(MassCastStates.choosing_main_template)
    await callback.message.edit_text(
        f"📍 ГЕО: <b>{geo.upper()}</b>\n\nОберіть подію:",
        reply_markup=kb.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "mc_back_geo")
async def mc_back_to_geo(callback: CallbackQuery, state: FSMContext):
    await _show_geo_selection(callback.message, state, edit=True)
    await callback.answer()


@router.callback_query(MassCastStates.choosing_main_template, F.data.startswith("mc_tmpl_"))
async def execute_mass_cast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    main_tmpl_id = callback.data.removeprefix("mc_tmpl_")
    data = await state.get_data()
    geo = data.get("geo")

    main_templates = load_main_templates()
    if main_tmpl_id not in main_templates:
        await callback.answer("❌ Головний шаблон не знайдено", show_alert=True)
        return

    main_tmpl = main_templates[main_tmpl_id]
    direction = main_tmpl["direction"]
    event = main_tmpl["event"]

    templates = load_templates()
    chats = load_chats()

    # Знаходимо всі регулярні шаблони прив'язані до цього головного
    linked = []  # [(lang, tmpl_name, text)]
    for lang, lang_templates in templates.items():
        for tmpl_name, tmpl_obj in lang_templates.items():
            if not isinstance(tmpl_obj, dict):
                continue
            if tmpl_obj.get("main_template") == main_tmpl_id:
                linked.append((lang, tmpl_name, tmpl_obj["text"]))

    if not linked:
        await callback.message.edit_text(
            f"❌ Немає регулярних шаблонів прив'язаних до <code>{main_tmpl_id}</code>.\n"
            f"Додайте шаблони через /manage_templates і прив'яжіть їх до цього головного шаблону.",
            parse_mode="HTML"
        )
        await state.clear()
        await callback.answer()
        return

    # Відправка: для кожного мовного шаблону — знаходимо чати з geo + lang + direction
    total_success = 0
    total_errors = 0
    lang_stats = {}
    all_sent_messages = []

    for lang, tmpl_name, tmpl_text in linked:
        try:
            formatted_text = tmpl_text.format(geo=geo.upper())
        except Exception:
            formatted_text = tmpl_text

        target_chats = [
            c for c in chats
            if len(c.get("tags", [])) >= 2
            and c["tags"][0] == geo
            and c["tags"][1] == lang
            and direction in c["tags"][2:]
        ]

        lang_success = 0
        lang_errors = 0

        for chat in target_chats:
            try:
                mentions = " ".join(chat.get("mentions", []))
                full_text = f"{formatted_text}\n\n{mentions}" if mentions else formatted_text
                msg = await bot.send_message(chat_id=chat["id"], text=full_text, parse_mode="HTML")
                all_sent_messages.append((chat["id"], msg.message_id))
                lang_success += 1
            except Exception as e:
                print(f"Mass cast помилка в {chat['name']}: {e}")
                lang_errors += 1

        lang_stats[lang] = {"success": lang_success, "errors": lang_errors}
        total_success += lang_success
        total_errors += lang_errors

    # Зберігаємо в історію для можливості видалення
    broadcast_id = str(callback.id)
    config.sent_history[broadcast_id] = {
        "geo": geo.upper(),
        "direction": direction,
        "event": event,
        "main_template": main_tmpl_id,
        "messages": all_sent_messages
    }
    config.save_history(config.sent_history)

    # Записуємо статус методу (direction = method)
    # Беремо текст з першого мовного шаблону для прев'ю
    sample_text = linked[0][2] if linked else ""
    record_method_broadcast(
        broadcast_id, geo, direction, "mass_cast",
        f"{direction}_{event}", sample_text,
        total_success, total_errors
    )

    config.write_event_log("MASS_SEND", {
        "broadcast_id": broadcast_id,
        "geo": geo.upper(),
        "main_template": main_tmpl_id,
        "direction": direction,
        "event": event,
        "results": {"success": total_success, "errors": total_errors},
        "lang_stats": lang_stats
    })

    # Формат звіту
    lang_lines = "\n".join(
        f"  • {lang.upper()} → {stat['success']} чатів"
        for lang, stat in lang_stats.items()
        if stat["success"] > 0
    )

    delete_kb = InlineKeyboardBuilder()
    delete_kb.row(InlineKeyboardButton(
        text="🗑 Видалити розсилку",
        callback_data=f"del_{broadcast_id}"
    ))

    await callback.message.edit_text(
        f"🚀 <b>Масова розсилка завершена!</b>\n\n"
        f"📊 Результати:\n"
        f"✅ Успішно: {total_success}\n"
        f"❌ Помилок: {total_errors}\n\n"
        f"Фільтр: {geo.upper()} | {direction.upper()} | {event.upper()}\n"
        f"{lang_lines}",
        parse_mode="HTML",
        reply_markup=delete_kb.as_markup()
    )

    await state.clear()
    await callback.answer("Готово!")
