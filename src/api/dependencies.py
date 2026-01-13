from typing import Generator
from src.db import connect

def get_db() -> Generator:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()