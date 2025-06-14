from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from app.database.models import (
    get_user_by_telegram_id,
    get_potential_matches,
    get_user_by_id,
    add_dislike,
    add_like,
    check_match, save_message_like, get_like_message,
)
from app.keyboards.inline import like_dislike_message_kb, like_dislike_kb
from app.states.Message import MessageStates
from app.utils.matchmaking import filter_candidates

router = Router()


@router.callback_query(F.data == "menu_search")
async def start_search(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.message.answer("Сначала зарегистрируйтесь через /start.")
        return
    if user["is_sleeping"]:
        await callback.message.answer("Вы в спящем режиме, поиск недоступен.")
        return

    candidates = get_potential_matches(user)
    filtered = filter_candidates(user, candidates)
    if not filtered:
        await callback.message.answer("К сожалению, подходящих анкет нет.")
        return

    first_candidate = filtered[0]
    await show_candidate(callback, first_candidate)
    await callback.answer()


@router.callback_query(F.data.startswith(("like_", "dislike_", "message_")))
async def process_reaction(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    action, candidate_id_str = callback.data.split("_", 1)
    candidate_id = int(candidate_id_str)

    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Пользователь не найден.", show_alert=True)
        return

    candidate = get_user_by_id(candidate_id)
    if not candidate:
        await callback.answer("Анкета не найдена.", show_alert=True)
        return

    if action == "dislike":
        add_dislike(user["id"], candidate_id)
        await callback.message.answer("Вы пропустили анкету.")
        await show_next_candidate(callback, user)
        return

    elif action == "like":
        add_like(user["id"], candidate_id)
        if check_match(user["id"], candidate_id):
            candidate_link = f"@{candidate['username']}" if candidate.get("username") else f"/profile_{candidate_id}"
            user_link = f"@{user['username']}" if user.get("username") else f"/profile_{user['id']}"
            await callback.bot.send_message(
                chat_id=user["telegram_id"],
                text=f"💘 У вас мэтч с {candidate['fullname']}!\n📎 {candidate_link}"
            )
            await callback.bot.send_message(
                chat_id=candidate["telegram_id"],
                text=f"💘 У вас мэтч с {user['fullname']}!\n📎 {user_link}"
            )
        else:
            notify_text = f"✨ Ваша анкета заинтересовала {user['fullname']}!"
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="👀 Посмотреть", callback_data=f"view_{user['id']}")]
                ]
            )
            await callback.bot.send_message(
                chat_id=candidate["telegram_id"],
                text=notify_text,
                reply_markup=keyboard
            )

            await callback.message.answer("Спасибо за вашу реакцию!")
        await show_next_candidate(callback, user)
        return

    elif action == "message":
        await state.update_data(candidate_id=candidate_id)
        await state.set_state(MessageStates.waiting_for_message)
        await callback.message.answer(f"Напишите сообщение, которое хотите отправить {candidate['fullname']}:")


@router.message(MessageStates.waiting_for_message)
async def handle_message_text(message: Message, state: FSMContext):
    data = await state.get_data()
    candidate_id = data.get("candidate_id")
    user = get_user_by_telegram_id(message.from_user.id)
    candidate = get_user_by_id(candidate_id)

    if not candidate:
        await message.answer("Анкета не найдена.")
        await state.clear()
        return

    user_message = message.text.strip()
    if not user_message:
        await message.answer("Сообщение не может быть пустым. Попробуйте снова.")
        return

    add_like(user["id"], candidate_id)
    save_message_like(user["id"], candidate_id, user_message)

    notify_text = f"✨ Ваша анкета заинтересовала {user['fullname']}!"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👀 Посмотреть", callback_data=f"view_{user['id']}")]
        ]
    )
    await message.bot.send_message(
        chat_id=candidate["telegram_id"],
        text=notify_text,
        reply_markup=keyboard
    )

    await message.answer("Сообщение отправлено!")
    await state.clear()
    await show_next_candidate(message, user)


async def show_candidate(callback: CallbackQuery, candidate: dict):
    user = get_user_by_telegram_id(callback.from_user.id)
    profile_text = format_profile(candidate, viewer_id=user['id'])
    buttons = like_dislike_message_kb(candidate["id"])

    photo_id = candidate.get("photo_path")
    if photo_id:
        await callback.message.answer_photo(
            photo=photo_id,
            caption=profile_text,
            reply_markup=buttons
        )
    else:
        await callback.message.answer(
            text=profile_text,
            reply_markup=buttons
        )


@router.callback_query(F.data.startswith("view_"))
async def view_profile(callback: CallbackQuery):
    candidate_id = int(callback.data.split("_")[1])
    candidate = get_user_by_id(candidate_id)

    if not candidate:
        await callback.answer("Анкета не найдена.", show_alert=True)
        return

    viewer = get_user_by_telegram_id(callback.from_user.id)
    extra_message = get_like_message(candidate_id, viewer['id'])# ⚠️ поменяй на нужный порядок, если логика иная

    profile_text = format_profile(candidate)
    if extra_message:
        profile_text += f"\n💬 Сообщение: {extra_message}"

    buttons = like_dislike_kb(candidate["id"])

    photo_id = candidate.get("photo_path")
    if photo_id:
        await callback.message.answer_photo(
            photo=photo_id,
            caption=profile_text,
            reply_markup=buttons
        )
    else:
        await callback.message.answer(
            text=profile_text,
            reply_markup=buttons
        )

    await callback.answer()


def format_profile(candidate: dict, viewer_id: int = None) -> str:
    skills_raw = candidate.get("skills", [])
    if isinstance(skills_raw, str):
        try:
            import json
            skills_list = json.loads(skills_raw)
        except Exception:
            skills_list = [skills_raw]
    else:
        skills_list = skills_raw
    skills = ", ".join(skills_list)

    description = candidate.get("description", "") or ""
    project_name = candidate.get("project_name", "") or ""

    profile_text = (
        f"👤 Имя: {candidate.get('fullname', 'Не указано')}\n"
        f"🎂 Возраст: {candidate.get('age', 'Не указано')}\n"
        f"🏙️ Город: {candidate.get('city', 'Не указано')}\n"
        f"🛠 Навыки: {skills if skills else 'Не указаны'}\n"
        f"⚙️ Вид деятельности: {candidate.get('activity', 'Не указано')}\n"
    )

    if candidate.get("seeking") == "developer":
        profile_text += f"📌 Название проекта: {project_name}\n"
        profile_text += f"📝 Описание проекта: {description}\n"
    else:
        profile_text += f"📝 Описание: {description}\n"

    if viewer_id:
        message_like = get_like_message(viewer_id, candidate['id'])
        if message_like:
            profile_text += f"\n\n✉️ Сообщение от вас:\n{message_like}"
    return profile_text


async def show_next_candidate(message_obj, user):
    candidates = get_potential_matches(user)
    filtered = filter_candidates(user, candidates)

    if not filtered:
        await message_obj.answer("Анкеты закончились. Попробуйте позже.")
        return

    next_candidate = filtered[0]
    if isinstance(message_obj, CallbackQuery):
        await show_candidate(message_obj, next_candidate)
    else:
        fake_callback = CallbackQuery(id="1", from_user=message_obj.from_user, message=message_obj)
        await show_candidate(fake_callback, next_candidate)