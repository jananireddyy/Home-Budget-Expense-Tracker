
import mysql.connector
from config import Config

def get_db_connection():
    if not Config.MYSQL_PASSWORD:
        raise RuntimeError(
            "MYSQL_PASSWORD is not set. Set it in PowerShell before starting Flask."
        )

    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        port=Config.MYSQL_PORT
    )
