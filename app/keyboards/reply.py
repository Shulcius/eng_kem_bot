from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def main_menu_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton(text="Искать"),
        KeyboardButton(text="Спящий режим"),
        KeyboardButton(text="Изменить данные"),
    )
    return kb
