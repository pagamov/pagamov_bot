import sqlite3
import os

class Database: 
    """ Родительский класс для работы с базой данных.  Мы не хотим переходить на postgresql!
    Мы фанаты sqlite3!
    """
    def __init__(self):
        # Мы ищем файл который исполняется
        # Далее отступаем назад и в папке db делаем файл main.db
        self.path = os.path.dirname(os.path.abspath(__file__)) + '/../../db/main.db'
        # print(self.path)

    def firstInitDatabase(self):
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        # Нужна для работы class Logger(Database)
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS bot_log (
                bot_log_id      INTEGER UNIQUE,
                datetime        TEXT NOT NULL,
                text            TEXT NOT NULL,
                PRIMARY KEY(bot_log_id)
            );
        """)
        # Нужна для работы class User(Database)
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS user (
                id_user	        INTEGER UNIQUE,
                tg_username	    TEXT NOT NULL UNIQUE,
                bot_username	TEXT,
                user_is_valid   INTEGER DEFAULT 1 CHECK (user_is_valid in (0, 1)),
                PRIMARY KEY(id_user)
            );
        """)
        # Тут указываются роли пользователей, данные заполняются при init
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS role (
                id_role	            INTEGER,
                name_role	        TEXT NOT NULL UNIQUE,
                description_role	TEXT,
                PRIMARY KEY(id_role)
            );
        """)
        con.commit()


        # Более крутые таблицы

        
        # Тут указываются какие роли для каких пользователей заведены
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS user_role (
                id_user_role	INTEGER,
                user	INTEGER NOT NULL,
                role	INTEGER NOT NULL,
                PRIMARY KEY(id_user_role),
                FOREIGN KEY(role) REFERENCES role(id_role),
                FOREIGN KEY(user) REFERENCES user(id_user)
            );
        """)
        con.commit()


        try:
            # Заполняем начальные значения для ролей в свежей базе
            cur.executemany(f"""
                INSERT INTO role
                    (name_role, description_role)
                VALUES 
                    (?,?);
            """,    [("admin", "Имеет доступ ко всему контенту"),
                     ("user", "Начальная роль всех пользователей")])
            con.commit()
        except Exception as e:
            # Если видим ошибку, получается что такие значения есть.
            print(e)

        cur.close()
        con.close()