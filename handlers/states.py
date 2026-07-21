from aiogram.fsm.state import StatesGroup, State

class BroadcastStates(StatesGroup):
    choosing_geo = State()
    choosing_lang = State()
    choosing_method = State()
    choosing_template = State()
    entering_custom_text = State()

class MassCastStates(StatesGroup):
    choosing_geo = State()
    choosing_main_template = State()

class ManageMainTemplateStates(StatesGroup):
    direction = State()
    event = State()