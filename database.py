import sqlite3


def get_connection():
    return sqlite3.connect("traineeship.db", check_same_thread=False)


def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    conn.commit()
    conn.close()


def add_user(email, password, role):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users (email,password,role) VALUES (?,?,?)",
        (email, password, role)
    )

    conn.commit()
    conn.close()


def get_user(email, password):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=? AND password=? AND active=1",
        (email, password)
    )

    user = cursor.fetchone()
    conn.close()

    return user


def get_users():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")

    data = cursor.fetchall()

    conn.close()

    return data


def toggle_user(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET active = NOT active WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()


def delete_user(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()
