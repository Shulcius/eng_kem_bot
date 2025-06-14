from aiogram.fsm.state import StatesGroup, State


class Registration(StatesGroup):
    seeking = State()        # выбор: 'developer' или 'project'
    fullname = State()       # ФИО
    age = State()            # возраст
    city = State()           # город
    description = State()    # описание проекта (если ищет разработчика)
    project_name = State()   # название проекта
    skills = State()         # выбор навыков (через инлайн кнопки)
    activity = State()       # вид деятельности (одиночный выбор)
    photo = State()          # загрузка фото
