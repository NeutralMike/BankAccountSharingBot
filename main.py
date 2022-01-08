import os

import psycopg2
import telebot

from dotenv import load_dotenv


load_dotenv()
db_connection = psycopg2.connect(
    dbname='bank_account_sharing_db',
    user='db_user',
    password='mypassword',
    host='localhost'
)

