
from database import *

Database().run_query(f"""
        INSERT INTO notify
            (chat_id, user_id, description, time_create, time_notify)
        VALUES   
            ({321911494},
            (SELECT id_user FROM user WHERE tg_username = "pagamov" limit 1),
            "Описание", DATETIME('NOW'), 
            DATETIME('NOW', '+3 hours', '+1 minute'))
        """)


# notify_to_send = Database().get_from_query(f"""
#         SELECT
#           id_notify, chat_id, description
# FROM
#           notify
#         WHERE
#           sent = 0 and
#           time_notify < DATETIME('now', '+3 hours')
#     """)

# print(notify_to_send)
