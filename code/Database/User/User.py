import sqlite3

from database.Database import Database
import random


class User(Database):
    """
    def __createBot_username(self) -> str

    def createUser(self, tg_username : str) -> None

    def get_id_user(self, tg_username : str) -> int
    def get_bot_username(self, tg_username : str) -> str
    """

    def __init__(self):
        super().__init__()
        self.default_user_role = 'user'
        self.admin_user_role = 'admin'
        self.admin_list = ['pagamov']

    def __createBot_username(self) -> str:
        """
        Делаем случайное имя для анонимного чата
        """
        pril = ["Удачливый","Смелый","Весёлый","Храбрый","Гениальный","Остроумный","Талантливый","Умный","Забавный",
                "Быстрый","Честный","Осторожный","Решительный","Проницательный","Верный","Любимый","Дерзкий","Очаровательный","Щедрый","Находчивый"]
        animals = ['слон','тигр','медведь','лев','крокодил','голубь','жираф','верблюд','броненосец','кот']
        dig = ['0','1','2','3','4','5','6','7','8','9']

        return f"{random.choice(pril)}_{random.choice(animals)}_{''.join([random.choice(dig) for i in range(5)])}"

    def createUser(self, tg_username : str) -> None:
        """
        1. Добавляет пользователя в базу
        
        2. Ставит ему базовые права пользователя (роль)
        
        3. Проверяет есть ли ник в списке админов. Если есть - добавляет ему админские права
        """
        assert tg_username != '', "tg_username is empty"
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(f"""
            INSERT INTO 
                    user 
                    (tg_username, bot_username)
            VALUES 
                    ("{tg_username}", "{self.__createBot_username()}");
        """)
        con.commit()
        # Ставим пользователю доступ по умолчанию
        cur.execute(f"""
            INSERT INTO user_role
                (user, role)
            VALUES
            (
                (SELECT user.id_user FROM user WHERE user.tg_username = '{tg_username}'), 
                (SELECT role.id_role FROM role WHERE role.name_role = '{self.default_user_role}')
            )
        """)


        # Админские штучки
        if tg_username in self.admin_list:
            cur.execute(f"""
                INSERT INTO user_role
                    (user, role)
                VALUES
                (
                    (SELECT user.id_user FROM user WHERE user.tg_username = '{tg_username}'), 
                    (SELECT role.id_role FROM role WHERE role.name_role = '{self.admin_user_role}')
                )
            """)
        # 
        con.commit()
        cur.close()
        con.close()

    def get_id_user(self, tg_username : str) -> int:
        """
        Вернем id_user из таблицы user по нику из tg. 
        
        -1 если пользователя нет в базе.
        """
        assert tg_username != '', "tg_username is empty"

        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(f"""
            SELECT id_user FROM user
            WHERE tg_username = "{tg_username}"
        """)
        res = cur.fetchall()
        cur.close()
        con.close()
        return -1 if len(res) == 0 else res[0][0]

    def is_admin(self, tg_username : str) -> bool:
        """
        Проверяет, является ли человек админом в системе по нику в тг.
        """
        assert tg_username != '', "tg_username is empty"

        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(f"""
            SELECT 
                id_user_role 
            FROM
                user_role
            WHERE 
                user = (SELECT id_user FROM user WHERE tg_username = '{tg_username}') AND 
                role = (SELECT id_role FROM role WHERE name_role = '{self.admin_user_role}')
        """)
        res = cur.fetchall()
        cur.close()
        con.close()
        return False if len(res) == 0 else True

    def get_bot_username(self, tg_username : str) -> str:
        assert tg_username != '', "tg_username is empty"

        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(f"""
            SELECT bot_username FROM user
            WHERE tg_username = "{tg_username}"
        """)
        res = cur.fetchall()
        cur.close()
        con.close()
        
        bot_username : str = res[0][0]
        
        assert bot_username != '', "bot_username is empty"
        
        return bot_username
