import os
import pymysql
from typing import Dict, Any

class DatabaseConfig:
    @staticmethod
    def get_config() -> Dict[str, Any]:
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'zzirit_db'),
            'charset': os.getenv('DB_CHARSET', 'utf8mb4')
        }
    
    @staticmethod
    def get_connection():
        config = DatabaseConfig.get_config()
        return pymysql.connect(
            **config,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )