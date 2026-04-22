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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        learner TEXT,
        qualification TEXT,
        state TEXT,
        created_by TEXT,
        created_at TEXT,
        schedule_json TEXT
    )
    """)

    conn.commit()
    conn.close()


# CREATE DEFAULT ADMIN FOR DEPLOYMENT
def create_default_admin():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (email,password,role) VALUES (?,?,?)",
            ("admin@company.com", "admin123", "admin")
        )
        conn.commit()

    conn.close()


# ---------------- USERS ----------------

def add_user(email, password, role):

    email = email.strip().lower()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (email,password,role) VALUES (?,?,?)",
            (email, password, role)
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def get_user(email, password):

    email = email.strip().lower()

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

    users = cursor.fetchall()

    conn.close()

    return users


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


# ---------------- SCHEDULE ----------------

def save_schedule(learner, qualification, state, user, schedule_df):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO schedules 
    (learner, qualification, state, created_by, created_at, schedule_json)
    VALUES (?,?,?,?,datetime('now'),?)
    """, (
        learner,
        qualification,
        state,
        user,
        schedule_df.to_json()
    ))

    conn.commit()
    conn.close()


def get_schedules():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, learner, qualification, state, created_by, created_at
    FROM schedules
    ORDER BY id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return data


def get_schedule(schedule_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT schedule_json FROM schedules WHERE id=?",
        (schedule_id,)
    )

    data = cursor.fetchone()

    conn.close()

    return data[0]


def delete_schedule(schedule_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM schedules WHERE id=?",
        (schedule_id,)
    )

    conn.commit()
    conn.close()
