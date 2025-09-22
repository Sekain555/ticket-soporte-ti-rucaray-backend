import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "sistema_tickets")
DB_USER = os.getenv("DB_USER", "pybackend")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return connection
    except Error as e:
        print(f"Error de conexión: {e}")
        return None
