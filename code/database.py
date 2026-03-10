import sqlite3
import os
import random
from datetime import datetime

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            self.path = os.path.join(os.path.dirname(__file__), 'db', 'main.db')
        else:
            self.path = db_path
        
        # Создаем директорию если она не существует
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        
    def get_connection(self):
        return sqlite3.connect(self.path)
    
    def execute_query(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor
    
    def fetch_all(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def fetch_one(self, query, params=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
    
    def initialize_database(self):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_username TEXT UNIQUE NOT NULL,
                bot_username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                description TEXT NOT NULL,
                frequency_type TEXT NOT NULL,
                frequency_value TEXT,
                time_of_day TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS habit_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER,
                date TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(habit_id) REFERENCES habits(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER,
                description TEXT NOT NULL,
                time_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_notify TIMESTAMP NOT NULL,
                sent INTEGER DEFAULT 0,
                done INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        ]
        
        for query in queries:
            self.execute_query(query)

class UserService:
    def __init__(self, database):
        self.db = database
    
    def create_user(self, tg_username):
        bot_username = self.generate_bot_username()
        query = "INSERT OR IGNORE INTO users (tg_username, bot_username) VALUES (?, ?)"
        self.db.execute_query(query, (tg_username, bot_username))
        return bot_username
    
    def generate_bot_username(self):
        adjectives = ["Удачливый", "Смелый", "Весёлый", "Храбрый", "Гениальный",
                     "Остроумный", "Талантливый", "Умный", "Забавный", "Быстрый",
                     "Честный", "Осторожный", "Решительный", "Проницательный",
                     "Верный", "Любимый", "Дерзкий", "Очаровательный", "Щедрый",
                     "Находчивый"]
        
        animals = ['слон', 'тигр', 'медведь', 'лев', 'крокодил',
                  'голубь', 'жираф', 'верблюд', 'броненосец', 'кот']
        
        digits = ''.join([str(random.randint(0, 9)) for _ in range(5)])
        
        return f"{random.choice(adjectives)}_{random.choice(animals)}_{digits}"
    
    def get_user_by_tg_username(self, tg_username):
        query = "SELECT * FROM users WHERE tg_username = ?"
        return self.db.fetch_one(query, (tg_username,))
    
    def get_bot_username(self, tg_username):
        user = self.get_user_by_tg_username(tg_username)
        return user[2] if user else None
    
    def update_bot_username(self, tg_username, new_bot_username):
        query = "UPDATE users SET bot_username = ? WHERE tg_username = ?"
        self.db.execute_query(query, (new_bot_username, tg_username))

class HabitService:
    def __init__(self, database):
        self.db = database
    
    def create_habit(self, user_id, description, frequency_type, time_of_day, 
                     start_date, end_date=None, frequency_value=None):
        query = """
        INSERT INTO habits 
        (user_id, description, frequency_type, frequency_value, time_of_day, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self.db.execute_query(query, (user_id, description, frequency_type, 
                                             frequency_value, time_of_day, start_date, end_date))
        return cursor.lastrowid
    
    def get_user_habits(self, user_id):
        query = """
        SELECT id, description, frequency_type, frequency_value, time_of_day, 
               start_date, end_date, is_active, created_at
        FROM habits 
        WHERE user_id = ? AND is_active = 1
        ORDER BY created_at DESC
        """
        return self.db.fetch_all(query, (user_id,))
    
    def delete_habit(self, habit_id):
        query = "UPDATE habits SET is_active = 0 WHERE id = ?"
        self.db.execute_query(query, (habit_id,))
