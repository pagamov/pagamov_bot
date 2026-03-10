from telegram import Update
from telegram.ext import ContextTypes
from database import Database, UserService, HabitService
import re

class HabitHandler:
    def __init__(self):
        self.db = Database()
        self.user_service = UserService(self.db)
        self.habit_service = HabitService(self.db)
    
    async def show_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        
        if text == "Мои привычки":
            await self.show_my_habits(update, context)
        elif text == "Добавить":
            await self.start_add_habit(update, context)
        elif text == "Удалить":
            await self.start_delete_habit(update, context)
        elif text == "Назад":
            await update.message.reply_text("Возвращаемся в главное меню")
        
        return "HABBIT_MENU"
    
    async def show_my_habits(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        tg_username = update.effective_user.username
        user = self.user_service.get_user_by_tg_username(tg_username)
        
        if user:
            habits = self.habit_service.get_user_habits(user[0])  # user[0] is user_id
            if habits:
                message = "Ваши привычки:\n\n"
                for i, habit in enumerate(habits, 1):
                    message += f"{i}. {habit[1]}\n"  # habit[1] is description
            else:
                message = "У вас пока нет привычек."
        else:
            message = "Ошибка: пользователь не найден."
        
        await update.message.reply_text(message)
    
    async def start_add_habit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Введите описание привычки:")
        return "ADD_HABIT_DESCRIPTION"
    
    async def add_habit_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['habit_description'] = update.message.text
        await update.message.reply_text("Введите частоту (ежедневно/еженедельно):")
        return "ADD_HABIT_FREQUENCY"
    
    async def add_habit_frequency(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        frequency = update.message.text.lower()
        if frequency in ["ежедневно", "еженедельно"]:
            context.user_data['habit_frequency'] = frequency
            await update.message.reply_text("Введите время (ЧЧ:ММ):")
            return "ADD_HABIT_TIME"
        else:
            await update.message.reply_text("Пожалуйста, введите 'ежедневно' или 'еженедельно'")
            return "ADD_HABIT_FREQUENCY"
    
    async def add_habit_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        time_pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
        if re.match(time_pattern, update.message.text):
            context.user_data['habit_time'] = update.message.text
            
            # Сохраняем привычку в базу данных
            tg_username = update.effective_user.username
            user = self.user_service.get_user_by_tg_username(tg_username)
            
            if user:
                habit_id = self.habit_service.create_habit(
                    user_id=user[0],
                    description=context.user_data['habit_description'],
                    frequency_type=context.user_data['habit_frequency'],
                    time_of_day=context.user_data['habit_time'],
                    start_date="2024-01-01"  # TODO: использовать текущую дату
                )
                await update.message.reply_text("Привычка успешно добавлена!")
            else:
                await update.message.reply_text("Ошибка: пользователь не найден.")
        else:
            await update.message.reply_text("Пожалуйста, введите время в формате ЧЧ:ММ")
            return "ADD_HABIT_TIME"
        
        return "HABBIT_MENU"
    
    async def start_delete_habit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        tg_username = update.effective_user.username
        user = self.user_service.get_user_by_tg_username(tg_username)
        
        if user:
            habits = self.habit_service.get_user_habits(user[0])
            if habits:
                message = "Выберите привычку для удаления:\n\n"
                for i, habit in enumerate(habits, 1):
                    message += f"{i}. {habit[1]}\n"
                message += "\nВведите номер привычки:"
                await update.message.reply_text(message)
                context.user_data['habits_for_deletion'] = habits
                return "DELETE_HABIT"
            else:
                await update.message.reply_text("У вас нет привычек для удаления.")
        else:
            await update.message.reply_text("Ошибка: пользователь не найден.")
        
        return "HABBIT_MENU"
    
    async def delete_habit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            habit_number = int(update.message.text) - 1
            habits = context.user_data.get('habits_for_deletion', [])
            
            if 0 <= habit_number < len(habits):
                habit_id = habits[habit_number][0]  # habit[0] is habit_id
                self.habit_service.delete_habit(habit_id)
                await update.message.reply_text("Привычка удалена!")
            else:
                await update.message.reply_text("Неверный номер привычки.")
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите номер привычки.")
            return "DELETE_HABIT"
        
        return "HABBIT_MENU"
