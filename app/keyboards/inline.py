from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def seeking_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Ищу разработчика", callback_data="seeking_developer")],
            [InlineKeyboardButton(text="Ищу проект", callback_data="seeking_project")]
        ]
    )


def skills_inline_kb(selected_skills: set) -> InlineKeyboardMarkup:
    skills = [
        "Python", "JavaScript", "Go", "Rust", "Java",
        "React", "Django", "Flask", "Node.js", "AI/ML"
    ]
    buttons = []
    for i in range(0, len(skills), 3):
        row = []
        for skill in skills[i:i + 3]:
            prefix = "✅ " if skill in selected_skills else ""
            row.append(
                InlineKeyboardButton(text=f"{prefix}{skill}", callback_data=f"skill_{skill}")
            )
        buttons.append(row)

    buttons.append(
        [InlineKeyboardButton(text="Подтвердить", callback_data="skills_confirm")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def activity_inline_kb(selected_activity: str = None) -> InlineKeyboardMarkup:
    activities = ["Frontend", "Backend", "Fullstack", "DevOps", "Data Science", "Mobile"]
    buttons = []

    for i in range(0, len(activities), 2):
        row = []
        for act in activities[i:i + 2]:
            prefix = "✅ " if act == selected_activity else ""
            row.append(
                InlineKeyboardButton(text=f"{prefix}{act}", callback_data=f"activity_{act}")
            )
        buttons.append(row)

    buttons.append(
        [InlineKeyboardButton(text="Подтвердить", callback_data="activity_confirm")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def like_dislike_message_kb(candidate_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👍 Лайк", callback_data=f"like_{candidate_id}"),
                InlineKeyboardButton(text="💬 Сообщение", callback_data=f"message_{candidate_id}"),
                InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"dislike_{candidate_id}")
            ],
            [
                InlineKeyboardButton(text="↩️ Вернуться в меню", callback_data="back_to_menu")
            ]
        ]
    )


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Искать", callback_data="menu_search")],
            [InlineKeyboardButton(text="Спящий режим", callback_data="menu_sleep")],
            [InlineKeyboardButton(text="Изменить данные", callback_data="menu_edit")],
        ]
    )


def view_profile_kb(candidate_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👀 Посмотреть", callback_data=f"view_{candidate_id}")]
        ]
    )


def like_dislike_kb(candidate_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="👍 Лайк", callback_data=f"like_{candidate_id}"),
            InlineKeyboardButton(text="👎 Дизлайк", callback_data=f"dislike_{candidate_id}")
        ]]
    )


def skills_inline_kb_edit(selected_skills: set) -> InlineKeyboardMarkup:
    skills = [
        "Python", "JavaScript", "Go", "Rust", "Java",
        "React", "Django", "Flask", "Node.js", "AI/ML"
    ]
    buttons = []
    for i in range(0, len(skills), 3):
        row = []
        for skill in skills[i:i + 3]:
            prefix = "✅ " if skill in selected_skills else ""
            row.append(
                InlineKeyboardButton(text=f"{prefix}{skill}", callback_data=f"skilledit_{skill}")
            )
        buttons.append(row)

    buttons.append(
        [InlineKeyboardButton(text="Подтвердить", callback_data="edit_skills_done")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def activity_inline_kb_edit(selected_activity: str = None) -> InlineKeyboardMarkup:
    activities = ["Frontend", "Backend", "Fullstack", "DevOps", "Data Science", "Mobile"]
    buttons = []

    for i in range(0, len(activities), 2):
        row = []
        for act in activities[i:i + 2]:
            prefix = "✅ " if act in selected_activity else ""
            row.append(
                InlineKeyboardButton(text=f"{prefix}{act}", callback_data=f"activityedit_{act}")
            )
        buttons.append(row)

    buttons.append(
        [InlineKeyboardButton(text="Подтвердить", callback_data="activity_confirm_edit")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)