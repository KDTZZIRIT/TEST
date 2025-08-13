import os

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "52.79.248.3"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "bigdata054"),
    "password": os.getenv("DB_PASSWORD", "1234"),
    "database": os.getenv("DB_NAME", "my_db"),
    "charset": "utf8mb4"
}
