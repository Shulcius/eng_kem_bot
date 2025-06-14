import asyncio

from app.database.models import get_connection


async def clear_blacklist_and_dislikes_periodically():
    while True:
        print("🧹 Очищаю таблицы blacklists и dislikes...")

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM blacklists;")
            cursor.execute("DELETE FROM dislikes;")
            conn.commit()

        print("✅ Очистка завершена. Следующая через 4 часа.")
        await asyncio.sleep(4 * 60 * 60)
