# db_handler.py  (새로 생성)
from __future__ import annotations
import os
import pymysql
from typing import Any, Iterable, Optional, Sequence

try:
    from db_config import DB_CONFIG as _DBCFG
except Exception:
    _DBCFG = {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", ""),
        "port": int(os.getenv("DB_PORT", "3306")),
        "charset": os.getenv("DB_CHARSET", "utf8mb4"),
    }

def _connect():
    return pymysql.connect(
        host=_DBCFG["host"],
        user=_DBCFG["user"],
        password=_DBCFG["password"],
        database=_DBCFG["database"],
        port=int(_DBCFG["port"]),
        charset=_DBCFG["charset"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

def query_db(sql: str, params: Optional[Sequence[Any]] = None) -> list[dict]:
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()

def execute_db(sql: str, params: Optional[Sequence[Any]] = None) -> int:
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.rowcount
    finally:
        conn.close()

def executemany_db(sql: str, seq_of_params: Iterable[Sequence[Any]]) -> int:
    conn = _connect()
    try:
        with conn.cursor() as cur:
            cur.executemany(sql, list(seq_of_params))
            return cur.rowcount
    finally:
        conn.close()
