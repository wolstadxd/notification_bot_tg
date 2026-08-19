from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from database import load_allowed_users, get_latest_method_statuses, load_method_history

router = Router()


def _format_status_desc(record):
    """Повертає короткий опис типу/шаблону для першого рядка."""
    cast_type = record.get("cast_type", "?")
    template_name = record.get("template_name", "?")
    text = record.get("text", "")

    if cast_type == "mass_cast":
        return f"⚡ <code>{template_name}</code>"
    elif cast_type == "custom":
        preview = text[:60] + "…" if len(text) > 60 else text
        return f'✍️ "<i>{preview}</i>"'
    else:  # new_cast
        return f"📝 <code>{template_name}</code>"


def _build_status_text():
    """Будує текстове повідомлення зі статусами всіх методів по ГЕО."""
    statuses = get_latest_method_statuses()

    if not statuses:
        return "📊 <b>Methods status</b>\n\n🔹 Історія розсилок порожня.", None

    lines = ["📊 <b>Methods status</b>\n"]
    buttons = []

    for geo in sorted(statuses.keys()):
        methods = statuses[geo]
        lines.append(f"📍 <b>{geo.upper()}</b>")
        for method in sorted(methods.keys()):
            record = methods[method]
            status_desc = _format_status_desc(record)
            timestamp = record.get("timestamp", "")
            success = record.get("success_count", 0)
            errors = record.get("error_count", 0)

            # Скорочуємо час до HH:MM для компактності
            time_short = timestamp[11:16] if len(timestamp) >= 16 else timestamp

            lines.append(f"  ⚙️ <b>{method}</b> — {status_desc}")
            lines.append(f"      У:{success}  Н:{errors}   🕒 {time_short}")
            lines.append("")
            buttons.append((geo, method))

    return "\n".join(lines), buttons


@router.message(Command("methods_status"))
async def methods_status_cmd(message: Message):
    allowed_users = load_allowed_users()
    if message.from_user.id not in allowed_users:
        await message.answer("❌ You don't have access")
        return

    text, buttons = _build_status_text()

    kb = InlineKeyboardBuilder()
    if buttons:
        for geo, method in buttons:
            kb.row(InlineKeyboardButton(
                text=f"🔎 {geo.upper()} — {method}",
                callback_data=f"ms_detail_{geo.lower()}_{method.lower()}"
            ))
    kb.row(InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu"))

    await message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data == "methods_status_menu")
async def methods_status_menu_callback(callback: CallbackQuery):
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return

    await callback.answer()  # знімаємо Loading миттєво

    text, buttons = _build_status_text()

    kb = InlineKeyboardBuilder()
    if buttons:
        for geo, method in buttons:
            kb.row(InlineKeyboardButton(
                text=f"🔎 {geo.upper()} — {method}",
                callback_data=f"ms_detail_{geo.lower()}_{method.lower()}"
            ))
    kb.row(InlineKeyboardButton(text="⬅️ Назад до меню", callback_data="admin_menu"))

    try:
        await callback.message.edit_text(text, reply_markup=kb.as_markup(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb.as_markup(), parse_mode="HTML")


@router.callback_query(F.data.startswith("ms_detail_"))
async def method_detail_callback(callback: CallbackQuery):
    allowed_users = load_allowed_users()
    if callback.from_user.id not in allowed_users:
        await callback.answer("❌ You don't have access", show_alert=True)
        return

    await callback.answer()  # знімаємо Loading миттєво

    # Парсуємо geo та method з callback_data: ms_detail_<geo>_<method>
    parts = callback.data.removeprefix("ms_detail_").split("_", 1)
    if len(parts) < 2:
        await callback.message.answer("❌ Невірний формат")
        return

    geo = parts[0]
    method = parts[1]
    key = f"{geo.lower()}:{method.lower()}"

    data = load_method_history()
    records = data.get(key, [])

    if not records:
        await callback.message.answer("❌ Дані не знайдено")
        return

    latest = records[-1]
    cast_type = latest.get("cast_type", "?")
    template_name = latest.get("template_name", "?")
    text = latest.get("text", "—")
    timestamp = latest.get("timestamp", "?")
    success = latest.get("success_count", 0)
    errors = latest.get("error_count", 0)

    # Обмежуємо текст повідомлення для Telegram (4096 символів)
    max_text_len = 3000
    display_text = text[:max_text_len] + "…" if len(text) > max_text_len else text

    type_label = {
        "new_cast": "📝 New Cast",
        "mass_cast": "⚡ Mass Cast",
        "custom": "✍️ Custom Cast"
    }.get(cast_type, cast_type)

    detail_msg = (
        f"📊 <b>Деталі останньої розсилки</b>\n\n"
        f"📍 ГЕО: <b>{geo.upper()}</b>\n"
        f"⚙️ Метод: <code>{method}</code>\n"
        f"📋 Тип: {type_label}\n"
        f"🏷 Шаблон: <code>{template_name}</code>\n"
        f"🕐 Час: {timestamp}\n"
        f"✅ Успішно: {success} | ❌ Помилок: {errors}\n\n"
        f"<b>Текст повідомлення:</b>\n"
        f"<pre>{display_text}</pre>"
    )

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="⬅️ Назад до статусів", callback_data="methods_status_menu"))
    kb.row(InlineKeyboardButton(text="🏠 Головне меню", callback_data="admin_menu"))

    try:
        await callback.message.edit_text(detail_msg, reply_markup=kb.as_markup(), parse_mode="HTML")
    except Exception:
        await callback.message.answer(detail_msg, reply_markup=kb.as_markup(), parse_mode="HTML")
