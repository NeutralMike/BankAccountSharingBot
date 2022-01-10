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

bot = telebot.TeleBot(os.getenv('TG_BOT_TOKEN'))


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "What is your name?")
    bot.register_next_step_handler(message, process_name_step)


def process_name_step(message):
    sql = "INSERT INTO users(chat_id, name) VALUES(%s, %s)"
    with db_connection.cursor() as cursor:
        cursor.execute(sql, (message.chat.id, message.text))
    db_connection.commit()

    bot.send_message(message.chat.id, "What is bank account number you want to watch?")
    bot.register_next_step_handler(message, process_bank_account_step)


def process_bank_account_step(message):
    sql = "INSERT INTO bank_accounts(number, owner) VALUES(%s, %s)"
    with db_connection.cursor() as cursor:
        cursor.execute(sql, (message.text, message.chat.id))
    db_connection.commit()

    bot.send_message(message.chat.id, "Any time now just send ammount of income or outcome you generated.")


@bot.message_handler()
def send_welcome(message):
    pass

bot.infinity_polling()

