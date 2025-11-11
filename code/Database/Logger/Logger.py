import sqlite3
import logging

# Можно настроить минимальный уровень вывода в консоль или файл
# logging.basicConfig(level=logging.INFO, filename="py_log.log",filemode="w")
# logging.basicConfig(level=logging.INFO)

from Const import LOGGER_VERBOSE
from Database.Database import Database

class Logger(Database):
    """
    Данный класс работает с таблицей bot_log
    Туда я хочу писать события и ошибки бота

    TODO sec_taken - хочу сюда писать кол-во времени которое заняла та или иная операция
    TODO хочется чтобы при краше, выдавался список ошибок которые были ранее, например 10 до. что привело к ошибке.
    """

    def __init__(self):
        super().__init__()
    
    def log(self, message : str, level : str = 'INFO', verbose : bool = LOGGER_VERBOSE) -> None:
        """
        level = INFO | ERROR | WARNING | CRITICAL
        """
        assert message != '', "message is empty"
        assert level in ['INFO', 'ERROR', 'WARNING', 'CRITICAL'], f"level cant be {level}"
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute(f"""
            INSERT INTO bot_log 
            (datetime, text)
            VALUES
            (datetime(), "{message}")
        """)
        con.commit()
        cur.close()
        con.close()

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
                    
    def tail_log_bot(self, n : int) -> list[str] | str:
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        cur.execute("""
        WITH tmp AS
            (SELECT * from bot_log
            ORDER BY bot_log_id DESC
            LIMIT {})
        SELECT 
            datetime, text 
        from tmp
        ORDER BY
            bot_log_id ASC
        """.format(n))
        res = cur.fetchall()
        cur.close()
        con.close()

        if len(res) == 0:
            return "Данная таблица пустая"
        else:
            return ["{} : {}\n\n".format(row[0], row[1]) for row in res]
