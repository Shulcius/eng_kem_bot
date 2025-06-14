from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json

from app.database.models import get_user_by_telegram_id, update_user
from app.keyboards.reply import cancel_kb
from app.states.EditField import EditField
from app.states.registration import Registration
from app.keyboards.inline import main_menu_kb, skills_inline_kb_edit, activity_inline_kb_edit

router = Router()


@router.callback_query(F.data == "menu_edit")
async def show_edit_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        return await callback.message.answer("Сначала зарегистрируйтесь через /start.")

    kb = InlineKeyboardBuilder()
    kb.button(text="📝 ФИО", callback_data="edit_fullname")
    kb.button(text="📅 Возраст", callback_data="edit_age")
    kb.button(text="🏙️ Город", callback_data="edit_city")
    kb.button(text="📋 Описание", callback_data="edit_description")
    kb.button(text="💼 Навыки", callback_data="edit_skills")
    kb.button(text="🧭 Активность", callback_data="edit_activity")
    kb.button(text="🖼 Фото", callback_data="edit_photo")
    kb.button(text="🔁 Заполнить заново", callback_data="edit_restart")
    kb.button(text="🔙 Вернуться в меню", callback_data="main_menu")
    kb.adjust(2)
    await callback.message.answer("Что вы хотите изменить?", reply_markup=kb.as_markup())
    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def go_to_main(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Главное меню:", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "edit_restart")
async def restart_profile(callback: CallbackQuery, state: FSMContext):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        return await callback.message.answer("Сначала зарегистрируйтесь через /start.")
    skills = set(json.loads(user["skills"])) if user["skills"] else set()
    await state.set_data({
        "fullname": user["fullname"],
        "age": user["age"],
        "city": user["city"],
        "description": user["description"],
        "seeking": user["seeking"],
        "skills": skills,
        "activity": user["activity"],
        "photo_path": user["photo_path"],
    })
    await callback.message.answer("Введите ФИО:", reply_markup=cancel_kb())
    await state.set_state(Registration.fullname)
    await callback.answer()


@router.callback_query(F.data.in_({
    "edit_fullname", "edit_age", "edit_city",
    "edit_description", "edit_photo"
}))
async def handle_text_field_edit(callback: CallbackQuery, state: FSMContext):
    field_map = {
        "edit_fullname": ("Введите новое ФИО:", EditField.fullname),
        "edit_age": ("Введите новый возраст:", EditField.age),
        "edit_city": ("Введите новый город:", EditField.city),
        "edit_description": ("Введите новое описание:", EditField.description),
        "edit_photo": ("Отправьте новое фото:", EditField.photo)
    }

    message_text, new_state = field_map[callback.data]
    await state.set_state(new_state)

    await callback.message.answer(message_text, reply_markup=cancel_kb() if new_state != EditField.photo else None)
    await callback.answer()


# ======= ОТДЕЛЬНОЕ РЕДАКТИРОВАНИЕ ПОЛЕЙ =======

@router.message(EditField.fullname)
async def save_fullname(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    update_user(
        user_id=user["id"],
        fullname=message.text,
        age=user["age"],
        city=user["city"],
        project_name=user["project_name"],
        description=user["description"],
        skills=user["skills"],
        activity=user["activity"],
        photo_path=user["photo_path"]
    )
    await state.clear()
    await message.answer("ФИО обновлено ✅\nВозвращаю в меню")
    profile_text = f"👤 Имя: {message.text}\n"
    profile_text += f"🎂 Возраст: {user['age']}\n"
    profile_text += f"🏙 Город: {user['city']}\n"
    profile_text += f"💼 Навыки: {', '.join(user['skills']) if user['skills'] else 'не указаны'}\n"
    profile_text += f"⚙️ Вид деятельности: {user['seeking']}\n"

    if user['seeking'] == 'developer':
        if user.get('project_name'):
            profile_text += f"\n📌 Проект: {user['project_name']}\n"
        if user.get('description'):
            profile_text += f"📝 Описание: {user['description']}\n"
    else:
        if user.get('description'):
            profile_text += f"\n📝 Описание: {user['description']}\n"

    from app.keyboards.inline import main_menu_kb
    keyboard = main_menu_kb()

    if user.get('photo_path'):
        await message.answer_photo(photo=user['photo_path'], caption=profile_text, reply_markup=keyboard)
    else:
        await message.answer(profile_text, reply_markup=keyboard)

    await state.clear()


@router.message(EditField.age)
async def save_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число.")
    age = int(message.text)
    if not (10 <= age <= 100):
        return await message.answer("Возраст должен быть от 10 до 100.")
    user = get_user_by_telegram_id(message.from_user.id)
    update_user(
        user_id=user["id"],
        fullname=user["fullname"],
        age=age,
        city=user["city"],
        project_name=user["project_name"],
        description=user["description"],
        skills=user["skills"],
        activity=user["activity"],
        photo_path=user["photo_path"]
    )
    await state.clear()
    await message.answer("Возраст обновлён ✅\nВозвращаю в меню")
    profile_text = f"👤 Имя: {user['fullname']}\n"
    profile_text += f"🎂 Возраст: {age}\n"
    profile_text += f"🏙 Город: {user['city']}\n"
    profile_text += f"💼 Навыки: {', '.join(user['skills']) if user['skills'] else 'не указаны'}\n"
    profile_text += f"⚙️ Вид деятельности: {user['seeking']}\n"

    if user['seeking'] == 'developer':
        if user.get('project_name'):
            profile_text += f"\n📌 Проект: {user['project_name']}\n"
        if user.get('description'):
            profile_text += f"📝 Описание: {user['description']}\n"
    else:
        if user.get('description'):
            profile_text += f"\n📝 Описание: {user['description']}\n"

    from app.keyboards.inline import main_menu_kb
    keyboard = main_menu_kb()

    if user.get('photo_path'):
        await message.answer_photo(photo=user['photo_path'], caption=profile_text, reply_markup=keyboard)
    else:
        await message.answer(profile_text, reply_markup=keyboard)

    await state.clear()


@router.message(EditField.city)
async def save_city(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    update_user(
        user_id=user["id"],
        fullname=user["fullname"],
        age=user["age"],
        city=message.text,
        project_name=user["project_name"],
        description=user["description"],
        skills=user["skills"],
        activity=user["activity"],
        photo_path=user["photo_path"]
    )
    await state.clear()
    await message.answer("Город обновлён ✅\nВозвращаю в меню")
    profile_text = f"👤 Имя: {user['fullname']}\n"
    profile_text += f"🎂 Возраст: {user['age']}\n"
    profile_text += f"🏙 Город: {message.text}\n"
    profile_text += f"💼 Навыки: {', '.join(user['skills']) if user['skills'] else 'не указаны'}\n"
    profile_text += f"⚙️ Вид деятельности: {user['seeking']}\n"

    if user['seeking'] == 'developer':
        if user.get('project_name'):
            profile_text += f"\n📌 Проект: {user['project_name']}\n"
        if user.get('description'):
            profile_text += f"📝 Описание: {user['description']}\n"
    else:
        if user.get('description'):
            profile_text += f"\n📝 Описание: {user['description']}\n"

    from app.keyboards.inline import main_menu_kb
    keyboard = main_menu_kb()

    if user.get('photo_path'):
        await message.answer_photo(photo=user['photo_path'], caption=profile_text, reply_markup=keyboard)
    else:
        await message.answer(profile_text, reply_markup=keyboard)

    await state.clear()


@router.message(EditField.description)
async def save_description(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    update_user(
        user_id=user["id"],
        fullname=user["fullname"],
        age=user["age"],
        city=user["city"],
        project_name=user["project_name"],
        description=message.text,
        skills=user["skills"],
        activity=user["activity"],
        photo_path=user["photo_path"]
    )
    await state.clear()
    await message.answer("Описание обновлено ✅\nВозвращаю в меню")
    profile_text = f"👤 Имя: {user['fullname']}\n"
    profile_text += f"🎂 Возраст: {user['age']}\n"
    profile_text += f"🏙 Город: {user['city']}\n"
    profile_text += f"💼 Навыки: {', '.join(user['skills']) if user['skills'] else 'не указаны'}\n"
    profile_text += f"⚙️ Вид деятельности: {user['seeking']}\n"

    if user['seeking'] == 'developer':
        if user.get('project_name'):
            profile_text += f"\n📌 Проект: {user['project_name']}\n"
        if user.get('description'):
            profile_text += f"📝 Описание: {message.text}\n"
    else:
        if user.get('description'):
            profile_text += f"\n📝 Описание: {message.text}\n"

    from app.keyboards.inline import main_menu_kb
    keyboard = main_menu_kb()

    if user.get('photo_path'):
        await message.answer_photo(photo=user['photo_path'], caption=profile_text, reply_markup=keyboard)
    else:
        await message.answer(profile_text, reply_markup=keyboard)

    await state.clear()


# ======= НАВЫКИ =======
@router.callback_query(F.data == "edit_skills")
async def handle_edit_skills(callback: CallbackQuery, state: FSMContext):
    user = get_user_by_telegram_id(callback.from_user.id)
    skills_edit = set(user["skills"]) if isinstance(user["skills"], list) else set(json.loads(user["skills"]))
    await state.set_state(EditField.edit_skills)
    await state.update_data(skills=skills_edit)

    await callback.message.edit_text("Выберите навыки:", reply_markup=skills_inline_kb_edit(skills_edit))
    await callback.answer()


@router.callback_query(F.data == "edit_skills_done")
async def confirm_editing_skills(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = get_user_by_telegram_id(callback.from_user.id)
    updated_skills = list(data.get("skills", set()))

    update_user(
        user_id=user["id"],
        fullname=user["fullname"],
        age=user["age"],
        city=user["city"],
        project_name=user["project_name"],
        description=user["description"],
        skills=updated_skills,
        activity=user["activity"],
        photo_path=user["photo_path"]
    )

    await state.clear()

    user = get_user_by_telegram_id(callback.from_user.id)

    profile_text = f"👤 Имя: {user['fullname']}\n"
    profile_text += f"🎂 Возраст: {user['age']}\n"
    profile_text += f"🏙 Город: {user['city']}\n"
    profile_text += f"💼 Навыки: {', '.join(user['skills']) if user['skills'] else 'не указаны'}\n"
    profile_text += f"⚙️ Вид деятельности: {user['seeking']}\n"

    if user['seeking'] == 'developer':
        if user.get('project_name'):
            profile_text += f"\n📌 Проект: {user['project_name']}\n"
        if user.get('description'):
            profile_text += f"📝 Описание: {user['description']}\n"
    else:
        if user.get('description'):
            profile_text += f"\n📝 Описание: {user['description']}\n"

    from app.keyboards.inline import main_menu_kb
    keyboard = main_menu_kb()

    if user.get('photo_path'):
        await callback.message.answer_photo(photo=user['photo_path'], caption=profile_text, reply_markup=keyboard)
    else:
        await callback.message.answer(profile_text, reply_markup=keyboard)

    await callback.answer()


# ======= АКТИВНОСТЬ =======
@router.callback_query(F.data == "edit_activity")
async def handle_edit_activity(callback: CallbackQuery, state: FSMContext):
    user = get_user_by_telegram_id(callback.from_user.id)
    await state.set_state(EditField.activity)
    await state.update_data(activity=user["activity"])

    await callback.message.edit_text("Выберите вид деятельности:", reply_markup=activity_inline_kb_edit(user["activity"]))
    await callback.answer()


@router.callback_query(F.data.startswith("activityedit_"), EditField.activity)
async def select_activity(callback: CallbackQuery, state: FSMContext):
    activity = callback.data[9:]
    await state.update_data(activity=activity)
    await callback.message.edit_reply_markup(reply_markup=activity_inline_kb_edit(activity))
    await callback.answer()


@router.callback_query(F.data == "activity_confirm_edit", EditField.activity)
async def confirm_activity(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = get_user_by_telegram_id(callback.from_user.id)
    update_user(
        user_id=user["id"],
        fullname=user["fullname"],
        age=user["age"],
        city=user["city"],
        project_name=user["project_name"],
        description=user["description"],
        skills=user["skills"],
        activity=data["activity"],
        photo_path=user["photo_path"]
    )
    await state.clear()
    await callback.message.answer("Вид деятельности обновлён ✅\nВозвращаю в меню")
    profile_text = f"👤 Имя: {user['fullname']}\n"
    profile_text += f"🎂 Возраст: {user['age']}\n"
    profile_text += f"🏙 Город: {user['city']}\n"
    profile_text += f"💼 Навыки: {', '.join(user['skills']) if user['skills'] else 'не указаны'}\n"
    profile_text += f"⚙️ Вид деятельности: {user['seeking']}\n"

    if user['seeking'] == 'developer':
        if user.get('project_name'):
            profile_text += f"\n📌 Проект: {user['project_name']}\n"
        if user.get('description'):
            profile_text += f"📝 Описание: {user['description']}\n"
    else:
        if user.get('description'):
            profile_text += f"\n📝 Описание: {user['description']}\n"

    from app.keyboards.inline import main_menu_kb
    keyboard = main_menu_kb()

    if user.get('photo_path'):
        await callback.message.answer_photo(photo=user['photo_path'], caption=profile_text, reply_markup=keyboard)
    else:
        await callback.message.answer(profile_text, reply_markup=keyboard)

    await state.clear()
    await callback.answer()


# ======= ФОТО =======

@router.message(EditField.photo, F.photo)
async def photo_upload(message: Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1]
    photo_file_id = photo.file_id

    user = get_user_by_telegram_id(message.from_user.id)
    update_user(
        user_id=user["id"],
        fullname=user["fullname"],
        age=user["age"],
        city=user["city"],
        project_name=user["project_name"],
        description=user["description"],
        skills=user["skills"],
        activity=user["activity"],
        photo_path=photo_file_id
    )

    user = get_user_by_telegram_id(message.from_user.id)
    await state.clear()
    await message.answer("Фото обновлено ✅\nВозвращаю в меню")

    profile_text = f"👤 Имя: {user['fullname']}\n"
    profile_text += f"🎂 Возраст: {user['age']}\n"
    profile_text += f"🏙 Город: {user['city']}\n"
    profile_text += f"💼 Навыки: {', '.join(user['skills']) if user['skills'] else 'не указаны'}\n"
    profile_text += f"⚙️ Вид деятельности: {user['seeking']}\n"

    if user['seeking'] == 'developer':
        if user.get('project_name'):
            profile_text += f"\n📌 Проект: {user['project_name']}\n"
        if user.get('description'):
            profile_text += f"📝 Описание: {user['description']}\n"
    else:
        if user.get('description'):
            profile_text += f"\n📝 Описание: {user['description']}\n"

    from app.keyboards.inline import main_menu_kb
    keyboard = main_menu_kb()

    if user.get('photo_path'):
        await message.answer_photo(photo=user['photo_path'], caption=profile_text, reply_markup=keyboard)
    else:
        await message.answer(profile_text, reply_markup=keyboard)

    await state.clear()


@router.message(EditField.photo)
async def photo_no_photo(message: Message):
    await message.answer("Пожалуйста, отправьте фотографию в виде изображения.")


# ======= ОТМЕНА =======

@router.message(F.text == "Отмена")
async def cancel_edit(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Редактирование отменено.", reply_markup=main_menu_kb())


@router.callback_query(F.data.startswith("skilledit_"))
async def process_skilledit_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    skills_edit = set(data.get("skills", []))

    skill = callback.data.split("_", 1)[1]
    if skill in skills_edit:
        skills_edit.remove(skill)
    else:
        skills_edit.add(skill)

    await state.update_data(skills=skills_edit)

    await callback.message.edit_reply_markup(reply_markup=skills_inline_kb_edit(skills_edit))
    await callback.answer()