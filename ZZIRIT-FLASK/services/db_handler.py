import pymysql
import mysql.connector
from typing import Any, List, Dict, Optional
from db_config import DB_CONFIG

def get_db_connection():
    """PyMySQL 연결"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        port=DB_CONFIG['port'],
        charset=DB_CONFIG['charset'],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def get_mysql_connection():
    """MySQL Connector 연결"""
    return mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        port=DB_CONFIG['port'],
        charset=DB_CONFIG['charset']
    )

def query_db(sql: str, params: Optional[tuple] = None) -> List[Dict]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()

# 나머지 함수들 포함...