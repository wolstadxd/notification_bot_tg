from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_template_kb(lang, geo):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Створили свою розсилку", callback_data=f"custom_{geo}_{lang}"))
    builder.row(InlineKeyboardButton(text="📉 Низький SR", callback_data=f"tmpl_{lang}_low_sr_{geo}"))
    builder.row(InlineKeyboardButton(text="⚙️ Техроботи", callback_data=f"tmpl_{lang}_tech_{geo}"))
    builder.row(InlineKeyboardButton(text="✅ Фікс", callback_data=f"tmpl_{lang}_fixed_{geo}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад до вибору мови", callback_data=f"geo_{geo}"))
    return builder.as_markup()

def get_yes_no_custom_kb():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Так, відправити", callback_data="yes_custom"))
    builder.add(InlineKeyboardButton(text="Ні, повернутись до ГЕО", callback_data="cancel_action"))
    return builder.as_markup()

def get_yes_no_custom_kb_all():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Так, відправити", callback_data="all_yes_custom"))
    builder.add(InlineKeyboardButton(text="Ні, повернутись до ГЕО", callback_data="cancel_action"))
    return builder.as_markup()

def get_lang_kb(geo: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🇺🇦 UA", callback_data=f"lang_ua_{geo}"))
    builder.row(InlineKeyboardButton(text="🇺🇸 EN", callback_data=f"lang_en_{geo}"))
    builder.row(InlineKeyboardButton(text="ru", callback_data=f"lang_ru_{geo}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_geo"))
    return builder.as_markup()

def get_lang_kb_all():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🇺🇦 UA", callback_data=f"all_lang_ua"))
    builder.row(InlineKeyboardButton(text="🇺🇸 EN", callback_data=f"all_lang_en"))
    builder.row(InlineKeyboardButton(text="ru", callback_data=f"all_lang_ru"))
    builder.row(InlineKeyboardButton(text="Видалити останнє повідомлення", callback_data=f"delete_last"))
    return builder.as_markup()

def back_to_geo():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад до ГЕО", callback_data=f"back_to_geo"))
    return builder.as_markup()

def back_to_lang_all_kb():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад до вибору мови", callback_data=f"back_to_lang_all_kb"))
    return builder.as_markup()