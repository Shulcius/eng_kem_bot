from aiogram.fsm.state import State, StatesGroup


class EditField(StatesGroup):
    fullname = State()
    age = State()
    city = State()
    description = State()
    edit_skills = State()
    activity = State()
    photo = State()
