import os
import atexit

import psycopg2
import telebot

from dotenv import load_dotenv


load_dotenv()
db_connection = psycopg2.connect(
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST')
)
atexit.register(db_connection.close)
