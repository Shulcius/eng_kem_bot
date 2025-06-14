from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.database.models import get_user_by_telegram_id
from app.keyboards.inline import main_menu_kb

router = Router()


@router.callback_query(F.data == "menu_sleep")
async def toggle_sleeping_mode(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Сначала зарегистрируйтесь через /start.")
        return

    from app.database.models import set_user_sleeping
    is_sleeping = user["is_sleeping"]

    if is_sleeping:
        set_user_sleeping(user["id"], False)
        await callback.message.answer("😴 Спящий режим отключён.", reply_markup=main_menu_kb())
    else:
        set_user_sleeping(user["id"], True)
        await callback.message.answer("🌙 Спящий режим включён. Вы не будете получать новые анкеты.", reply_markup=main_menu_kb())

    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
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
            await callback.message.answer_photo(photo=user['photo_path'], caption=profile_text, reply_markup=keyboard)
        else:
            await callback.message.answer(profile_text, reply_markup=keyboard)

    else:
        await callback.message.answer(
            "Привет! Нажми на /start чтобы зарегестрироваться"
        )