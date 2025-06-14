import psycopg2
import json
from typing import Optional, List, Dict
from .db import get_db, DB_CONFIG


def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            seeking TEXT NOT NULL,
            fullname TEXT,
            age INTEGER,
            city TEXT,
            description TEXT,
            project_name TEXT,
            skills TEXT,
            activity TEXT,
            photo_path TEXT,
            username TEXT,
            is_sleeping BOOLEAN DEFAULT FALSE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            liked_user_id INTEGER NOT NULL,
            UNIQUE(user_id, liked_user_id)
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dislikes (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            disliked_user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, disliked_user_id)
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklists (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            blacklisted_user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, blacklisted_user_id)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_likes (
            user_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            message_text TEXT NOT NULL,
            PRIMARY KEY (user_id, candidate_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (candidate_id) REFERENCES users(id)
        );
        """)
        conn.commit()


def create_user(telegram_id: int, seeking: str, username: str) -> int:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (telegram_id, seeking, username) VALUES (%s, %s, %s) RETURNING id",
            (telegram_id, seeking, username)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        return user_id


def get_user_by_telegram_id(telegram_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
        row = cursor.fetchone()
        if row:
            user = dict(zip([col.name for col in cursor.description], row))
            if user["skills"]:
                user["skills"] = json.loads(user["skills"])
            else:
                user["skills"] = []
            return user
        return None


def update_user(user_id: int, fullname: str, age: int, city: str, project_name: Optional[str],
                description: Optional[str], skills: List[str], activity: str, photo_path: Optional[str]):
    with get_connection() as conn:
        cursor = conn.cursor()
        skills_json = json.dumps(skills)
        cursor.execute("""
            UPDATE users SET fullname=%s, age=%s, city=%s, project_name=%s, description=%s, skills=%s, activity=%s, photo_path=%s
            WHERE id=%s
        """, (fullname, age, city, project_name, description, skills_json, activity, photo_path, user_id))
        conn.commit()


def set_user_sleeping(user_id: int, sleeping: bool):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET is_sleeping=%s WHERE id=%s", (sleeping, user_id))
        conn.commit()


def get_potential_matches(user: Dict) -> List[Dict]:
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            try:
                cursor.execute("""
                    SELECT liked_id FROM likes WHERE liker_id = %s
                    UNION
                    SELECT disliked_id FROM dislikes WHERE disliker_id = %s
                    UNION
                    SELECT blocked_id FROM blacklist WHERE blocker_id = %s
                    UNION
                    SELECT blocker_id FROM blacklist WHERE blocked_id = %s
                """, (user["id"], user["id"], user["id"], user["id"]))
                excluded_ids = {row[0] for row in cursor.fetchall()}
            except Exception:
                excluded_ids = set()

            excluded_ids.add(user["id"])

            if not excluded_ids:
                return []

            placeholders = ",".join("%s" for _ in excluded_ids)
            query = f"SELECT * FROM users WHERE id NOT IN ({placeholders})"

            cursor.execute(query, tuple(excluded_ids))
            rows = cursor.fetchall()

            if not rows:
                return []

            users = []
            for row in rows:
                u = dict(zip([col.name for col in cursor.description], row))
                u["skills"] = json.loads(u["skills"]) if u["skills"] else []
                users.append(u)

            return users

    except Exception as e:
        print(f"[get_potential_matches] Ошибка: {e}")
        return []


def add_like(user_id: int, liked_user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO likes (user_id, liked_user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user_id, liked_user_id)
        )
        conn.commit()


def add_dislike(user_id: int, disliked_user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO dislikes (user_id, disliked_user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user_id, disliked_user_id)
        )
        cursor.execute(
            "INSERT INTO blacklists (user_id, blacklisted_user_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user_id, disliked_user_id)
        )
        conn.commit()


def check_match(user_id: int, candidate_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM likes WHERE user_id = %s AND liked_user_id = %s",
            (candidate_id, user_id)
        )
        reciprocal = cursor.fetchone()
        return reciprocal is not None


# async def notify_user(user_id: int, matched_user_id: int):
#     user = get_user_by_id(user_id)
#     matched_user = get_user_by_id(matched_user_id)
#     if not user or not matched_user:
#         return
#     telegram_id = user["telegram_id"]
#     text = (
#         f"🎉 У вас матч! Пользователь <b>{matched_user['fullname']}</b> заинтересовался вашей анкетой.\n"
#         f"Посмотреть профиль: /profile_{matched_user_id}"
#     )
#     try:
#         await bot.send_message(chat_id=telegram_id, text=text)
#     except Exception as e:
#         # Логируем ошибку, чтобы знать если не удалось отправить
#         print(f"Ошибка при отправке уведомления: {e}")


def get_user_by_id(user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip([col.name for col in cursor.description], row))
        return None


def is_mutual_like(user_id: int, liked_user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM likes
            WHERE user_id = %s AND liked_user_id = %s
        """, (liked_user_id, user_id))
        return cursor.fetchone() is not None


def save_message_like(user_id: int, candidate_id: int, message_text: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO message_likes (user_id, candidate_id, message_text)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, candidate_id) DO UPDATE
            SET message_text = EXCLUDED.message_text
        """, (user_id, candidate_id, message_text))
        conn.commit()


def get_like_message(user_id: int, candidate_id: int) -> Optional[str]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_text FROM message_likes
            WHERE user_id = %s AND candidate_id = %s
        """, (user_id, candidate_id))
        row = cursor.fetchone()
        return row[0] if row else None


def clear_blacklists_and_dislikes():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dislikes")
        cursor.execute("DELETE FROM blacklists")
        conn.commit()

