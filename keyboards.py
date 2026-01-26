from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_geo_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🇵🇪 Перу", callback_data="geo_peru"))
    builder.row(InlineKeyboardButton(text="🇺🇦 Україна", callback_data="geo_ua"))
    builder.row(InlineKeyboardButton(text="🗑 Видалити останню розсилку", callback_data="delete_last"))
    return builder.as_markup()


def get_template_kb(lang, geo):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Create custom template", callback_data=f"custom_{geo}_{lang}"))
    builder.row(InlineKeyboardButton(text="📉 Низький SR", callback_data=f"tmpl_{lang}_low_sr_{geo}"))
    builder.row(InlineKeyboardButton(text="⚙️ Техроботи", callback_data=f"tmpl_{lang}_tech_{geo}"))
    builder.row(InlineKeyboardButton(text="✅ Фікс", callback_data=f"tmpl_{lang}_fixed_{geo}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад до вибору мови", callback_data=f"geo_{geo}"))
    return builder.as_markup()


def get_yes_no_custom_kb(geo_from_state, lang_from_state):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Yes, send please", callback_data="yes_custom"))
    builder.add(InlineKeyboardButton(text="Cancel please", callback_data="no_custom"))
    return builder.as_markup()


def get_lang_kb(geo: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🇺🇦 UA", callback_data=f"lang_ua_{geo}"))
    builder.row(InlineKeyboardButton(text="🇺🇸 EN", callback_data=f"lang_en_{geo}"))
    builder.row(InlineKeyboardButton(text="ru", callback_data=f"lang_ru_{geo}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_geo"))
    return builder.as_markup()
