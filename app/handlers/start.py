import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from app.database.models import get_user_by_telegram_id, create_user, update_user
from app.states.registration import Registration
from app.keyboards.inline import seeking_inline_kb, skills_inline_kb, activity_inline_kb

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    # await asyncio.create_task(clear_blacklist_and_dislikes_periodically())  #функция для того чтобы каждые 4 часа очищать бд чёрного списка
    if user:
        profile_text = f"👤 Имя: {user['fullname']}\n"
        profile_text += f"🎂 Возраст: {user['age']}\n"
        profile_text += f"🏙 Город: {user['city']}\n"
        profile_text += f"💼 Навыки: {', '.join(user['skills']) if user['skills'] else 'не указаны'}\n"
        profile_text += f"⚙️ Вид деятельности: {user.get('activity', 'Не указано')}\n"

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
    else:
        await message.answer(
            "Привет! Кого вы ищете?\nВыберите один вариант:",
            reply_markup=seeking_inline_kb()
        )
        await state.set_state(Registration.seeking)


@router.callback_query(F.data.startswith("seeking_"))
async def process_seeking(callback: CallbackQuery, state: FSMContext):
    seeking = callback.data.split("_")[1]
    await state.update_data(seeking=seeking)
    await callback.message.answer("Введите ваше ФИО:")
    await state.set_state(Registration.fullname)
    await callback.answer()


@router.message(Registration.fullname)
async def process_fullname(message: Message, state: FSMContext):
    await state.update_data(fullname=message.text)
    await message.answer("Введите ваш возраст:")
    await state.set_state(Registration.age)


@router.message(Registration.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введите число.")
    age = int(message.text)
    if age < 0 or age > 100:
        return await message.answer("Введите реалистичный возраст.")
    await state.update_data(age=age)
    await message.answer("Выберите вид вашей деятельности:", reply_markup=activity_inline_kb())
    await state.set_state(Registration.activity)


@router.callback_query(F.data == "activity_confirm")
async def confirm_activity(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    activity = data.get("activity")

    if not activity:
        await callback.answer("Пожалуйста, выберите один вариант.", show_alert=True)
        return

    await callback.message.answer("Введите ваш город:")
    await state.set_state(Registration.city)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("activity_") and c.data != "activity_confirm")
async def process_activity_selection(callback: CallbackQuery, state: FSMContext):
    activity = callback.data.split("_", 1)[1]
    await state.update_data(activity=activity)
    await callback.message.edit_reply_markup(reply_markup=activity_inline_kb(activity))
    await callback.answer()


@router.message(Registration.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()
    if data['seeking'] == 'developer':
        await message.answer("Введите название проекта:")
        await state.set_state(Registration.project_name)
    else:
        await message.answer(
            "Выберите ваши навыки:",
            reply_markup=skills_inline_kb(set())
        )
        await state.set_state(Registration.skills)


@router.message(Registration.project_name)
async def process_project_name(message: Message, state: FSMContext):
    await state.update_data(project_name=message.text)
    await message.answer("Введите описание проекта:")
    await state.set_state(Registration.description)


@router.message(Registration.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "Выберите ваши навыки:",
        reply_markup=skills_inline_kb(set())
    )
    await state.set_state(Registration.skills)


@router.callback_query(F.data.startswith("skill_"))
async def process_skill_selection(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    skills = set(data.get("skills", []))

    skill = callback.data.split("_", 1)[1]
    if skill in skills:
        skills.remove(skill)
    else:
        skills.add(skill)

    await state.update_data(skills=skills)

    await callback.message.edit_reply_markup(reply_markup=skills_inline_kb(skills))
    await callback.answer()


@router.callback_query(F.data == "skills_confirm", Registration.skills)
async def process_skills_done(callback: CallbackQuery, state: FSMContext):
    print("callback", callback.data)
    data = await state.get_data()
    skills = list(data.get("skills", []))
    if not skills:
        await callback.answer("Пожалуйста, выберите хотя бы один навык.", show_alert=True)
        return

    await state.update_data(skills=skills)

    await callback.message.answer("Теперь отправьте вашу фотографию:")
    await state.set_state(Registration.photo)
    await callback.answer()


@router.message(Registration.photo, F.content_type == "photo")
async def process_photo(message: Message, state: FSMContext):
    username = message.from_user.username  # Может быть None
    if not message.photo:
        await message.answer("Что-то не так с фотографией. Попробуйте снова.")
        return

    photo = message.photo[-1]
    file_id = photo.file_id
    await state.update_data(photo_path=file_id)

    data = await state.get_data()

    seeking = data.get("seeking")
    fullname = data.get("fullname")
    age = data.get("age")
    city = data.get("city")
    project_name = data.get("project_name")
    description = data.get("description", "")
    skills = data.get("skills", [])
    photo_path = data.get("photo_path")
    activity = data.get("activity")

    user = get_user_by_telegram_id(message.from_user.id)
    if user:
        user_id = user["id"]
    else:
        user_id = create_user(message.from_user.id, seeking, username)

    update_user(
        user_id=user_id,
        fullname=fullname,
        age=age,
        city=city,
        project_name=project_name,
        description=description,
        skills=skills,
        activity=activity,
        photo_path=photo_path
    )

    profile_text = f"📸 Фотография сохранена!\n\n"
    profile_text += f"👤 Имя: {fullname}\n"
    profile_text += f"🎂 Возраст: {age}\n"
    profile_text += f"🏙 Город: {city}\n"
    profile_text += f"💼 Навыки: {', '.join(skills) if skills else 'не указаны'}\n"
    profile_text += f"⚙️ Вид деятельности: {activity}\n"
    if seeking == "developer" and project_name:
        profile_text += f"\n📌 Проект: {project_name}\n"
        if description:
            profile_text += f"📝 Описание: {description}\n"
    elif seeking != "developer" and description:
        profile_text += f"\n📝 Описание: {description}\n"

    from app.keyboards.inline import main_menu_kb
    keyboard = main_menu_kb()

    await message.answer_photo(photo=file_id, caption=profile_text, reply_markup=keyboard)
    await state.clear()


@router.message(Registration.photo)
async def process_wrong_photo(message: Message):
    await message.answer("Пожалуйста, отправьте фотографию.")


@router.message(F.text == "Отмена")
async def cancel_registration(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Регистрация отменена. Чтобы начать заново, напишите /start.")
