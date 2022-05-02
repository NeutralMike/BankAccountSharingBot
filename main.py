import os
import atexit

import psycopg2
import shortuuid
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
def start(message):
    get_user = "SELECT 1 FROM users WHERE user_id = %s limit = 1"
    with db_connection.cursor() as cursor:
        try:
            cursor.execute(get_user, (message.from_user.id,))
        except psycopg2.Error:
            cursor.execute("ROLLBACK")
            register(message)
        else:
            help(message)


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, "Select bank account, then any time just send ammount of income or outcome you generated.")


@bot.message_handler(commands=['register'])
def register(message):
    bot.send_message(message.chat.id, "What is your name?")
    bot.register_next_step_handler(message, process_name_step)


def process_name_step(message):
    sql = "INSERT INTO users(user_id, name) VALUES(%s, %s) ON CONFLICT (user_id) DO UPDATE SET name = EXCLUDED.name;"
    if not str(message.text).strip():
        bot.send_message(message.chat.id, "Name should not be empty, try again")
        bot.register_next_step_handler(message, process_name_step)
        return
    with db_connection.cursor() as cursor:
        cursor.execute(sql, (message.from_user.id, message.text))
    db_connection.commit()


@bot.message_handler(commands=['add_bank_account'])
def add_bank_account(message):
    bot.send_message(message.chat.id, "Enter new bank account name.")
    bot.register_next_step_handler(message, process_adding_account)


def process_adding_account(message):
    sql = "INSERT INTO bank_accounts(name, owner) VALUES(%s, %s)"
    with db_connection.cursor() as cursor:
        cursor.execute(sql, (message.text, message.from_user.id))
    db_connection.commit()


@bot.message_handler(commands=['share_bank_account'])
def share_bank_account(message):
    sql = "SELECT * FROM bank_accounts WHERE owner= %s"
    with db_connection.cursor() as cursor:
        cursor.execute(sql, (message.from_user.id, ))
        bank_accounts = cursor.fetchall()

    markup = telebot.types.InlineKeyboardMarkup()
    for account in bank_accounts:
        markup.add(telebot.types.InlineKeyboardButton(text=account[1], callback_data=account[0]))

    bot.send_message(chat_id=message.chat.id, text='Choose from the following', reply_markup=markup)


@bot.callback_query_handler(func=lambda query: True)
def callback_query(query):
    set_code = "INSERT INTO shares(bank_account, code) VALUES(%s, %s)"
    get_code = "SELECT 1 FROM shares WHERE code = %s limit = 1"
    code = shortuuid.uuid()

    with db_connection.cursor() as cursor:
        i = 0
        while i < 3:
            try:
                cursor.execute(get_code, (code,))
            except psycopg2.Error:
                cursor.execute("ROLLBACK")
                break
            else:
                code = shortuuid.uuid()
                i += 1
        if i < 3:
            cursor.execute(set_code, (query.data, code))
            bot.answer_callback_query(query.id, text="OK")
            bot.send_message(chat_id=query.message.chat.id, text=f'WORKS ONLY ONES\nCode for sharing: {code}')
    db_connection.commit()


@bot.message_handler(commands=['list_of_bank_accounts'])
def list_of_bank_accounts(message):
    sql = "SELECT name FROM bank_accounts WHERE owner= %s"
    with db_connection.cursor() as cursor:
        cursor.execute(sql, (message.from_user.id,))
        bank_accounts = cursor.fetchall()
    str_list_accounts = "\n".join([account[0] for account in bank_accounts])
    bot.send_message(chat_id=message.chat.id, text=f'Your bank accounts:\n {str_list_accounts}')


@bot.message_handler(commands=['enter_share_code'])
def enter_share_code(message):
    bot.send_message(chat_id=message.chat.id, text=f'Enter sharing code')
    bot.register_next_step_handler(message, process_share_code)


def process_share_code(message):
    get_share = "SELECT 1 FROM shares WHERE code = %s limit = 1"
    set_user = "UPDATE shares SET user_id = %s WERE code = %s"

    with db_connection.cursor() as cursor:
        try:
            cursor.execute(get_share, (message.text,))
            share = cursor.fetchone()
        except psycopg2.Error:
            cursor.execute("ROLLBACK")
            bot.send_message(chat_id=message.chat.id, text=f'Error(')
        else:
            cursor.execute(set_user, (message.from_user.id, share[2]))
            bot.send_message(chat_id=message.chat.id, text=f'Success')
    db_connection.commit()


@bot.message_handler()
def add_transaction(message):
    sql = "INSERT INTO transactions(user_id, bank_account, amount) VALUES(%s, %s, %s)"
    get_account_owner = "SELECT id FROM bank_accounts WHERE owner = %s"
    get_shared_account = "SELECT bank_account FROM shares WHERE user_id = %s"
    try:
        amount = int(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Message is not fully a number. You may enter \"-1234\" though, but may not \"1234 dollars\"")
        return

    with db_connection.cursor() as cursor:
        try:
            cursor.execute(get_account_owner, (message.from_user.id,))
            bank_account = cursor.fetchone()[0]
        except psycopg2.Error:
            cursor.execute("ROLLBACK")
            cursor.execute(get_shared_account, (message.from_user.id, ))
            bank_account = cursor.fetchone()[0]

        cursor.execute(sql, (message.from_user.id, bank_account, amount))
    db_connection.commit()

    bot.send_message(message.chat.id, "OK")

bot.infinity_polling()

