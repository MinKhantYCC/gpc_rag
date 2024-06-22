import sqlite3 as sql
import json
from utils import load_config

config = load_config()

def load_messages(session_id, cursor):

    query = "SELECT message FROM messages WHERE session_id = ?"
    cursor.execute(query, (session_id,))

    messages = cursor.fetchall()
    chat_history = []
    for message in messages:
        msg = json.loads(message[0])
        chat_history.append({"type": msg['type'],
                             "message": msg['data']['content']})
    return chat_history

def init_db():
    db_path = config["chat_sessions_database_path"]

    conn = sql.connect(db_path)
    cursor = conn.cursor()

    create_messages_table = """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        message TEXT
    );
    """

    cursor.execute(create_messages_table)
    conn.commit()
    conn.close()

def get_all_chat_history(cursor):

    query = "SELECT * FROM messages ORDER BY session_id ASC"
    cursor.execute(query)

    messages = cursor.fetchall()
    chat_history = []
    for message in messages:
        id, session_id, text_content = message
        chat_history.append({'id': id, 
                             'session_id': session_id,
                            # 'sender_type': sender_type,
                            'message': text_content})
    return chat_history

def save_text_message(conn, cursor, session_id, sender_type, text):
    cursor.execute('INSERT INTO messages (session_id, sender_type, message) VALUES (?, ?, ?)',
                   (session_id, sender_type, text))
    conn.commit()