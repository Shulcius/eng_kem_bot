from aiogram import Bot
from app.database.models import get_user_by_id


async def notify_user(bot: Bot, user_id: int, matched_user_id: int):
    user = get_user_by_id(user_id)
    matched_user = get_user_by_id(matched_user_id)
    if not user or not matched_user:
        return
    try:
        await bot.send_message(
            chat_id=user["telegram_id"],
            text=(
                f"🎉 У вас матч с <{matched_user['fullname']}!\n"
                f"Анкета: /profile_{user_id}"
            )
        )
    except Exception as e:
        print(f"[Ошибка notify_user]: {e}")
