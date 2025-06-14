import os
from dotenv import load_dotenv
import psycopg2
from contextlib import contextmanager

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "sslmode": os.getenv("DB_SSLMODE"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "target_session_attrs": os.getenv("DB_TARGET_SESSION_ATTRS")
}

@contextmanager
def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()
