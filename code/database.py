import sqlite3
import os
import logging
import random

from const import *

# Можно настроить минимальный уровень вывода в консоль или файл
# logging.basicConfig(level=logging.INFO, filename="py_log.log",filemode="w")
# logging.basicConfig(level=logging.INFO)


class Database:
    """Родительский класс для работы с базой данных.

    Мы не хотим переходить на postgresql!

    Мы фанаты sqlite3!
    """

    def __init__(self):
        # Мы ищем файл который исполняется
        # Далее отступаем назад и в папке db делаем файл main.db
        self.path = os.path.dirname(os.path.abspath(__file__)) \
            + '/../db/main.db'

    def run_query(self, query: str) -> None:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(query)
        con.commit()
        cur.close()
        con.close()

    def run_many_query(self, query: str, arr: list) -> None:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        try:
            cur.executemany(query, arr)
            con.commit()
        except:
            print('error in run_many_query')
            pass
        cur.close()
        con.close()

    def get_from_query(self, query: str) -> list[any]:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(query)
        res = cur.fetchall()
        cur.close()
        con.close()
        return res
    
    def run_query_with_return(self, query: str, params: tuple = ()) -> int:
        """Выполнить запрос и вернуть ID последней вставленной записи"""
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(query, params)
        last_id = cur.lastrowid
        con.commit()
        cur.close()
        con.close()
        return last_id

    def firstInitDatabase(self):

        firstInitDatabase_message_to_delete: str = """
        CREATE TABLE IF NOT EXISTS message_to_delete (
            message_to_delete_id    INTEGER UNIQUE,
            datetime_to_delete      TEXT NOT NULL,
            chat_id                 TEXT NOT NULL,
            message_id              TEXT NOT NULL,
            deleted                 INTEGER DEFAULT 0,
            PRIMARY KEY(message_to_delete_id)
        );"""

        # Хочется чтобы чат был чистый, тут пишутся сообщения на удаление
        self.run_query(firstInitDatabase_message_to_delete)

        # Нужна для работы class Logger(Database)
        self.run_query(Text.firstInitDatabase_bot_log)

        # Нужна для работы class User(Database)
        self.run_query(Text.firstInitDatabase_user)

        # Тут указываются роли пользователей, данные заполняются при init
        self.run_query(Text.firstInitDatabase_role)

        firstInitDatabase_notify: str = """
        CREATE TABLE IF NOT EXISTS notify (
            id_notify               INTEGER,
            chat_id                 INTEGER NOT NULL,
            user_id                 INTEGER NOT NULL,
            description             TEXT NOT NULL,
            time_create             TEXT NOT NULL,
            time_notify             TEXT NOT NULL,
            sent                    INTEGER DEFAULT 0,
            done                    INTEGER DEFAULT 0,
            PRIMARY KEY(id_notify),
            FOREIGN KEY(user_id) REFERENCES user(id_user)
        );"""

        # Таблица напоминаний
        self.run_query(firstInitDatabase_notify)

        firstInitDatabase_user_habbit: str = """
        CREATE TABLE IF NOT EXISTS user_habbit (
            id_user_habbit	INTEGER,
            id_user	INTEGER NOT NULL,
            description TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            PRIMARY KEY(id_user_habbit),
            FOREIGN KEY(id_user) REFERENCES user(id_user)
        );"""

        # Таблица с привычками пользователей
        self.run_query(firstInitDatabase_user_habbit)

        # Более крутые таблицы
        # Тут указываются какие роли для каких пользователей заведены
        self.run_query(Text.firstInitDatabase_user_role)

        # В метод firstInitDatabase класса Database
        firstInitDatabase_habit: str = """
        CREATE TABLE IF NOT EXISTS habit (
            id_habit            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER NOT NULL,
            description         TEXT NOT NULL,
            frequency_type      TEXT NOT NULL, -- daily, weekly, custom
            frequency_value     TEXT,          -- для custom: "1,3,5"
            time_of_day         TEXT NOT NULL, -- время напоминания HH:MM
            start_date          TEXT NOT NULL, -- дата начала
            end_date            TEXT,          -- дата окончания (опционально)
            is_active           INTEGER DEFAULT 1,
            created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES user(id_user)
        );"""

        firstInitDatabase_habit_progress: str = """
        CREATE TABLE IF NOT EXISTS habit_progress (
            id_progress         INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id            INTEGER NOT NULL,
            date                TEXT NOT NULL,
            status              TEXT NOT NULL, -- completed, missed, skipped
            notes               TEXT,
            created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(habit_id) REFERENCES habit(id_habit)
        );"""

        # Добавляем в firstInitDatabase
        self.run_query(firstInitDatabase_habit)
        self.run_query(firstInitDatabase_habit_progress)

        try:
            firstInitDatabase_insert_role: str = """
                INSERT INTO role
                    (name_role, description_role)
                VALUES 
                    (?,?);"""
            
            firstInitDatabase_insert_role_arr: list = [
                ("admin", "Имеет доступ ко всему контенту"),
                ("user", "Начальная роль всех пользователей")]

            # Заполняем начальные значения для ролей в свежей базе
            self.run_many_query(firstInitDatabase_insert_role,
                                firstInitDatabase_insert_role_arr)
        except Exception as e:
            # Если видим ошибку, получается что такие значения есть.
            print(e)


class HabitService:
    def __init__(self):
        self.database = Database()
    
    def create_habit(self, user_id: int, description: str, frequency_type: str,
                     time_of_day: str, start_date: str, end_date: str = None,
                     frequency_value: str = None) -> int:
        """Создание новой привычки"""
        query = """
        INSERT INTO habit 
            (user_id, description, frequency_type, frequency_value, 
             time_of_day, start_date, end_date, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """
        
        habit_id = self.database.run_query_with_return(
            query, (user_id, description, frequency_type, frequency_value,
                   time_of_day, start_date, end_date)
        )
        return habit_id
    
    def get_user_habits(self, user_id: int) -> list:
        """Получение всех активных привычек пользователя"""
        query = """
        SELECT id_habit, description, frequency_type, frequency_value,
               time_of_day, start_date, end_date, created_at
        FROM habit
        WHERE user_id = ? AND is_active = 1
        ORDER BY created_at DESC
        """
        return self.database.get_from_query(query, (user_id,))
    
    def get_habit_by_id(self, habit_id: int) -> dict:
        """Получение привычки по ID"""
        query = """
        SELECT id_habit, description, frequency_type, frequency_value,
               time_of_day, start_date, end_date, is_active, created_at
        FROM habit
        WHERE id_habit = ?
        """
        result = self.database.get_from_query(query, (habit_id,))
        return result[0] if result else None
    
    def update_habit(self, habit_id: int, **kwargs) -> None:
        """Обновление привычки"""
        allowed_fields = ['description', 'frequency_type', 'frequency_value',
                         'time_of_day', 'start_date', 'end_date', 'is_active']
        
        updates = []
        values = []
        for field, value in kwargs.items():
            if field in allowed_fields:
                updates.append(f"{field} = ?")
                values.append(value)
        
        if updates:
            query = f"UPDATE habit SET {', '.join(updates)} WHERE id_habit = ?"
            values.append(habit_id)
            self.database.run_query_with_params(query, tuple(values))
    
    def delete_habit(self, habit_id: int) -> None:
        """Удаление привычки (мягкое удаление)"""
        query = "UPDATE habit SET is_active = 0 WHERE id_habit = ?"
        self.database.run_query_with_params(query, (habit_id,))
    
    def mark_habit_completed(self, habit_id: int, 
                             date: str, notes: str = None) -> None:
        """Отметить выполнение привычки"""
        query = """
        INSERT INTO habit_progress (habit_id, date, status, notes)
        VALUES (?, ?, 'completed', ?)
        """
        self.database.run_query_with_params(query, (habit_id, date, notes))
    
    def get_habit_schedule_for_period(self, habit_id: int, 
                                      start_date: str, end_date: str) -> list:
        """Получение расписания привычки на период"""
        habit = self.get_habit_by_id(habit_id)
        if not habit:
            return []
        
        scheduled_dates = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end_datetime:
            if self._should_notify_on_date(habit, current_date):
                scheduled_dates.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'time': habit['time_of_day'],
                    'description': habit['description']
                })
            current_date += timedelta(days=1)
        
        return scheduled_dates
    
    def _should_notify_on_date(self, habit: dict, date: datetime) -> bool:
        """Проверка, нужно ли отправля уведомление в конкретную дату"""
        if habit['frequency_type'] == 'daily':
            return True
        elif habit['frequency_type'] == 'weekly':
            # Например, если frequency_value = "1,3,5" 
            # (понедельник, среда, пятница)
            weekday = str(date.weekday())  # 0 = понедельник
            return weekday in (habit['frequency_value'] or '').split(',')
        elif habit['frequency_type'] == 'custom':
            # Пользовательские дни
            return str(date.weekday()) in \
                (habit['frequency_value'] or '').split(',')
        
        return False


class Logger:
    """Данный класс работает с таблицей bot_log
    Туда я хочу писать события и ошибки бота

    TODO sec_taken - хочу сюда писать кол-во времени \
        которое заняла та или иная операция
    TODO хочется чтобы при краше, выдавался список ошибок \
        которые были ранее, например 10 до. что привело к ошибке.
    """

    def log(self, message: str,
            level: str = 'INFO',
            verbose: bool = LOGGER_VERBOSE) -> None:
        """level = INFO | ERROR | WARNING | CRITICAL
        """

        assert message != '', "message is empty"
        assert level in ['INFO', 'ERROR', 'WARNING', 'CRITICAL'], \
            f"level cant be {level}"

        Database().run_query(Text.log_insert_query.format(message))

        if verbose:
            match level:
                case "INFO":
                    logging.info(f"{message}")
                case "ERROR":
                    logging.error(f"{message}")
                case "WARNING":
                    logging.warning(f"{message}")
                case "CRITICAL":
                    logging.critical(f"{message}")
                    exit()

    def tail_log_bot(self, n: int) -> list[str] | str:
        res = Database().get_from_query(Text.tail_log_bot_t0.format(n))
        if len(res) == 0:
            return "Данная таблица пустая"
        else:
            return ["{} : {}\n\n".format(row[0], row[1]) for row in res]


class User:
    """def createUser(self, tg_username : str) -> None

    def get_id_user(self, tg_username : str) -> int
    def get_bot_username(self, tg_username : str) -> str
    """

    def __init__(self):
        self.default_user_role = "user"
        self.admin_user_role = "admin"
        self.admin_list = ["pagamov"]

    def createBot_username(self) -> str:

        pril: list[str] = \
        ["Удачливый", "Смелый", "Весёлый", "Храбрый", "Гениальный",
         "Остроумный", "Талантливый", "Умный", "Забавный", "Быстрый",
         "Честный", "Осторожный", "Решительный", "Проницательный",
         "Верный", "Любимый", "Дерзкий", "Очаровательный", "Щедрый",
         "Находчивый"]
        
        animals: list[str] = \
        ['слон', 'тигр', 'медведь', 'лев', 'крокодил',
         'голубь', 'жираф', 'верблюд', 'броненосец', 'кот']
        
        dig: list[str] = \
        ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

        result = f"{random.choice(pril)}_" \
            + f"{random.choice(animals)}_" \
            + f"{''.join([random.choice(dig) for i in range(5)])}"

        return result

    def createUser(self, tg_username: str) -> None:
        """1. Добавляет пользователя в базу

        2. Ставит ему базовые права пользователя (роль)

        3. Проверяет есть ли ник в списке админов. \
            Если есть - добавляет ему админские права
        """
        assert tg_username != '', Text.User_t1_err


        User_t0 = "Создаем пользователя {}"

        Logger().log(User_t0.format(tg_username))
        Database().run_query(
            Text.createUser_t0.format(tg_username, self.createBot_username()))

        # Ставим пользователю доступ по умолчанию

        User_t2 = "Создаем пользователя {} - права по умолчанию"

        Logger().log(User_t2.format(tg_username))
        Database().run_query(
            Text.createUser_t1.format(tg_username, self.default_user_role))

        # Админские штучки
        if tg_username in self.admin_list:
            Logger().log(Text.User_t3.format(tg_username))
            Database().run_query(
                Text.createUser_t2.format(tg_username, self.admin_user_role))

    def get_id_user(self, tg_username: str) -> int:
        """Вернем id_user из таблицы user по нику из tg. 

        -1 если пользователя нет в базе.
        """
        assert tg_username != '', Text.User_t1_err

        Logger().log(Text.User_t4.format(tg_username))
        res = Database().get_from_query(Text.get_id_user_t0.format(tg_username))

        return -1 if len(res) == 0 else res[0][0]

    def is_admin(self, tg_username: str) -> bool:
        """Проверяет, является ли человек админом в системе по нику в тг.
        """
        assert tg_username != '', Text.User_t1_err

        Logger().log(Text.User_t5.format(tg_username))
        res = Database().get_from_query(
            Text.is_admin_t0.format(tg_username, self.admin_user_role))

        return False if len(res) == 0 else True

    def get_bot_username(self, tg_username: str) -> str:
        assert tg_username != '', Text.get_bot_username_err

        Logger().log(Text.User_t6.format(tg_username))
        res = Database().get_from_query(
            Text.get_bot_username_t0.format(tg_username))

        bot_username: str = res[0][0]
        assert bot_username != '', Text.get_bot_username_err
        return bot_username
