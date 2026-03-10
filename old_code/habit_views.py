# views/habit_views.py
from const import Text, Keyboard

class HabitViews:
    @staticmethod
    def get_habit_menu_keyboard():
        """Клавиатура меню привычек"""
        return Keyboard.HABBIT_MENU
    
    @staticmethod
    def format_habit_list(habits: list) -> str:
        """Форматирование списка привычек для отображения"""
        if not habits:
            return "У вас пока нет привычек. Добавьте первую!"
        
        message = "📝 Ваши привычки:\n\n"
        for i, habit in enumerate(habits, 1):
            status_emoji = "✅" if habit.get('is_active', 1) else "⏸️"
            message += f"{i}. {status_emoji} {habit['description']}\n"
            message += f"   Частота: {HabitViews._format_frequency(habit)}\n"
            message += f"   Время: {habit['time_of_day']}\n\n"
        
        return message
    
    @staticmethod
    def _format_frequency(habit: dict) -> str:
        """Форматирование частоты привычки"""
        freq_type = habit['frequency_type']
        if freq_type == 'daily':
            return "Ежедневно"
        elif freq_type == 'weekly':
            days = {
                '0': 'Пн', '1': 'Вт', '2': 'Ср', '3': 'Чт', 
                '4': 'Пт', '5': 'Сб', '6': 'Вс'
            }
            selected_days = [days.get(d, d) for d in 
                             (habit['frequency_value'] or '').split(',') if d]
            return f"По {', '.join(selected_days)}"
        else:
            return "Пользовательская"
    
    @staticmethod
    def get_frequency_selection_keyboard():
        """Клавиатура выбора частоты"""
        from telegram import ReplyKeyboardMarkup, KeyboardButton
        return ReplyKeyboardMarkup([
            [KeyboardButton("Ежедневно")],
            [KeyboardButton("Выбрать дни недели")],
            [KeyboardButton("Отмена")]
        ], resize_keyboard=True)
    
    @staticmethod
    def get_weekdays_keyboard():
        """Клавиатура выбора дней недели"""
        from telegram import ReplyKeyboardMarkup, KeyboardButton
        return ReplyKeyboardMarkup([
            [KeyboardButton("Пн"), KeyboardButton("Вт"), KeyboardButton("Ср")],
            [KeyboardButton("Чт"), KeyboardButton("Пт"), KeyboardButton("Сб")],
            [KeyboardButton("Вс"), KeyboardButton("Готово"), 
             KeyboardButton("Отмена")]
        ], resize_keyboard=True)
    
    @staticmethod
    def get_time_selection_keyboard():
        """Клавиатура выбора времени"""
        from telegram import ReplyKeyboardMarkup, KeyboardButton
        from datetime import time, timedelta
        import math
        
        buttons = []
        current_time = time(6, 0)  # Начинаем с 6:00
        
        row = []
        for hour in range(6, 23):  # с 6:00 до 22:00
            for minute in [0, 30]:  # Каждые 30 минут
                if len(row) >= 3:
                    buttons.append(row)
                    row = []
                row.append(KeyboardButton(f"{hour:02d}:{minute:02d}"))
        
        if row:
            buttons.append(row)
        buttons.append([KeyboardButton("Отмена")])
        
        return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
