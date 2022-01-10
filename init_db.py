import os

import psycopg2

from dotenv import load_dotenv


load_dotenv()


def create_tables():
    db_connection = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST')
    )
    try:
        commands = (
            """
            CREATE TABLE users (
                chat_id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            )
            """,
            """
            CREATE TABLE bank_accounts (
                number BIGINT PRIMARY KEY,
                owner INTEGER NOT NULL REFERENCES users
            )
            """,
            """
            CREATE TABLE transactions (
                id SERIAL PRIMARY KEY,
                chat_id INTEGER NOT NULL REFERENCES users,
                bank_account BIGINT NOT NULL REFERENCES bank_accounts,
                amount INTEGER NOT NULL
            )
            """,
        )
        with db_connection.cursor() as cursor:
            for command in commands:
                cursor.execute(command)
        db_connection.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        db_connection.close()
