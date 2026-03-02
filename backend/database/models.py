import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            token_id VARCHAR(20) UNIQUE NOT NULL,
            patient_name VARCHAR(100) NOT NULL,
            doctor VARCHAR(100) NOT NULL,
            department VARCHAR(100) NOT NULL,
            status ENUM('Waiting','Called','Completed','Cancelled') DEFAULT 'Waiting',
            queue_position INT,
            appointment_date DATE DEFAULT (CURRENT_DATE)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_queries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(50),
            user_message TEXT NOT NULL,
            bot_response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(50) NOT NULL,
            role ENUM('user','assistant') NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    sample_data = [
        ('KSD2001', 'Rajan Nair', 'Dr. Rajesh Kumar M', 'General Medicine', 'Completed', None),
        ('KSD2025', 'Fathima Beevi', 'Dr. Mohammed Aslam K', 'Orthopaedics', 'Called', None),
        ('KSD2043', 'Sushma Pillai', 'Dr. Sindhu Varma', 'Gynaecology', 'Waiting', 2),
        ('KSD2044', 'Anwar Khan', 'Dr. Rajesh Kumar M', 'General Medicine', 'Waiting', 3),
        ('KSD2045', 'Krishnan Kutty', 'Dr. Arun Krishnan', 'Paediatrics', 'Waiting', 1),
        ('KSD2046', 'Meenakshi Devi', 'Dr. Suresh Babu T', 'General Surgery', 'Waiting', 4),
        ('KSD2050', 'Abdul Kareem', 'Dr. Anwar Sadath', 'Neurology', 'Waiting', 2),
    ]

    for row in sample_data:
        cursor.execute("""
            INSERT IGNORE INTO appointments
            (token_id, patient_name, doctor, department, status, queue_position)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, row)

    conn.commit()
    cursor.close()
    conn.close()
    print("MySQL tables created and sample data inserted!")

def get_token_status(token_id: str):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM appointments WHERE token_id = %s",
            (token_id.upper(),)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    except Exception as e:
        print(f"DB Error: {e}")
        return None

def save_query(session_id: str, user_msg: str, bot_response: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_queries (session_id, user_message, bot_response) VALUES (%s, %s, %s)",
            (session_id, user_msg, bot_response)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Save query error: {e}")

def save_chat_history(session_id: str, role: str, message: str):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_history (session_id, role, message) VALUES (%s, %s, %s)",
            (session_id, role, message)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Chat history error: {e}")