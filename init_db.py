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
                chat_id VARCHAR(32) PRIMARY KEY,
                name VARCHAR(255)
            )
            """,
            """
            CREATE TABLE bank_accounts (
                number VARCHAR(32) PRIMARY KEY,
                owner VARCHAR(32) REFERENCES users (chat_id)
            )
            """,
            """
            CREATE TABLE transactions (
                id SERIAL PRIMARY KEY,
                chat_id VARCHAR(32) REFERENCES users,
                bank_account VARCHAR(32) REFERENCES bank_accounts (number),
                amount INT NOT NULL
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
