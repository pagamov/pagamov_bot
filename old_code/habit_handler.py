# handlers/habit_handler.py
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes
from database import HabitService
from habit_views import HabitViews
from database import User
from const import Text, State, Keyboard
from utils import get_user_info, return_to_main_menu

class HabitHandler:
    def __init__(self):
        self.habit_service = HabitService()
        self.views = HabitViews()
        self.user_service = User()
    
    async def menu(self, update: Update, 
                   context: ContextTypes.DEFAULT_TYPE) -> int:
        """Главное меню привычек"""
        text, tg_username = get_user_info(update)
        
        if text == Text.HABBIT_MENU_KEYBOARD[0]:  # Мои привычки
            return await self._show_my_habits(update, context, tg_username)
        
        elif text == Text.HABBIT_MENU_KEYBOARD[1]:  # Добавить
            return await self._start_add_habit(update, context)
        
        elif text == Text.HABBIT_MENU_KEYBOARD[2]:  # Удалить
            return await self._start_delete_habit(update, context, tg_username)
        
        elif text == Text.HABBIT_MENU_KEYBOARD[3]:  # Изменить
            await update.message.reply_text(
                "Функция изменения привычек в разработке")
            return State.HABBIT_MENU
        
        elif text == Text.HABBIT_MENU_KEYBOARD[4]:  # Настройки
            await update.message.reply_text(
                "Функция настроек привычек в разработке")
            return State.HABBIT_MENU
        
        elif text == Text.HABBIT_MENU_KEYBOARD[-1]:  # Назад
            return await return_to_main_menu(update, tg_username)
        
        return State.HABBIT_MENU
    
    async def _show_my_habits(self, update: Update, 
                              context: ContextTypes.DEFAULT_TYPE, 
                             tg_username: str) -> int:
        """Показать список привычек пользователя"""
        user_id = self.user_service.get_id_user(tg_username)
        habits = self.habit_service.get_user_habits(user_id)
        
        message = self.views.format_habit_list(habits)
        await update.message.reply_text(message, 
                            reply_markup=self.views.get_habit_menu_keyboard())
        
        return State.HABBIT_MENU
    
    async def _start_add_habit(self, update: Update, 
                               _: ContextTypes.DEFAULT_TYPE) -> int:
        
        """Начать процесс добавления привычки"""
        await update.message.reply_text(
            "🎯 Какую привычку вы хотите добавить?",
            reply_markup=Keyboard.NOTIFY_MENU_ADD_CANCEL_KEYBOARD
        )
        return State.HABBIT_MENU_ADD_DESCRIPTION
    
    async def add_description(self, update: Update, 
                              context: ContextTypes.DEFAULT_TYPE) -> int:
        """Шаг 1: Получение описания привычки"""
        text = update.message.text
        
        if text == "Отменить":
            return await self._cancel_operation(update)
        
        context.user_data['habit_description'] = text
        await update.message.reply_text(
            "📅 Как часто выполнять привычку?",
            reply_markup=self.views.get_frequency_selection_keyboard()
        )
        return State.HABBIT_MENU_ADD_FREQUENCY
    
    async def add_frequency(self, update: Update, 
                            context: ContextTypes.DEFAULT_TYPE) -> int:
        """Шаг 2: Выбор частоты"""
        text = update.message.text
        
        if text == "Отменить":
            return await self._cancel_operation(update)
        
        frequency_map = {
            "Ежедневно": "daily",
            "Выбрать дни недели": "weekly"
        }
        
        if text in frequency_map:
            context.user_data['habit_frequency'] = frequency_map[text]
            
            if frequency_map[text] == "weekly":
                await update.message.reply_text(
                    "Выберите дни недели:",
                    reply_markup=self.views.get_weekdays_keyboard()
                )
                context.user_data['selected_weekdays'] = []
                return State.HABBIT_MENU_ADD_WEEKDAYS
            else:
                await update.message.reply_text(
                    "⏰ В какое время напоминать?",
                    reply_markup=self.views.get_time_selection_keyboard()
                )
                return State.HABBIT_MENU_ADD_TIME
        else:
            await update.message.reply_text(
                "Пожалуйста, выберите корректную частоту",
                reply_markup=self.views.get_frequency_selection_keyboard()
            )
            return State.HABBIT_MENU_ADD_FREQUENCY
    
    async def add_weekdays(self, update: Update, 
                           context: ContextTypes.DEFAULT_TYPE) -> int:
        """Шаг 2.5: Выбор дней недели"""
        text = update.message.text
        
        if text == "Отменить":
            return await self._cancel_operation(update)
        
        if text == "Готово":
            if not context.user_data.get('selected_weekdays'):
                await update.message.reply_text(
                    "Пожалуйста, выберите хотя бы один день")
                return State.HABBIT_MENU_ADD_WEEKDAYS
            
            context.user_data['habit_frequency_value'] = ','.join(
                context.user_data['selected_weekdays']
            )
            await update.message.reply_text(
                "⏰ В какое время напоминать?",
                reply_markup=self.views.get_time_selection_keyboard()
            )
            return State.HABBIT_MENU_ADD_TIME
        
        weekdays_map = {
            "Пн": "0", "Вт": "1", "Ср": "2", "Чт": "3",
            "Пт": "4", "Сб": "5", "Вс": "6"
        }
        
        if text in weekdays_map:
            selected = context.user_data.get('selected_weekdays', [])
            day_num = weekdays_map[text]
            if day_num not in selected:
                selected.append(day_num)
                context.user_data['selected_weekdays'] = selected
                await update.message.reply_text(
                    f"Выбраны дни: \
                        {[k for k, v in weekdays_map.items() if v in selected]}"
                )
        
        return State.HABBIT_MENU_ADD_WEEKDAYS
    
    async def add_time(self, update: Update, 
                       context: ContextTypes.DEFAULT_TYPE) -> int:
        """Шаг 3: Выбор времени"""
        text = update.message.text
        tg_username = update.effective_user.username
        
        if text == "Отменить":
            return await self._cancel_operation(update)
        
        # Проверка формата времени
        import re
        if re.match(r'^\d{1,2}:\d{2}$', text):
            context.user_data['habit_time'] = text
            
            # Сохраняем привычку
            user_id = self.user_service.get_id_user(tg_username)
            habit_id = self.habit_service.create_habit(
                user_id=user_id,
                description=context.user_data['habit_description'],
                frequency_type=context.user_data['habit_frequency'],
                frequency_value=context.user_data.get('habit_frequency_value'),
                time_of_day=context.user_data['habit_time'],
                start_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            await update.message.reply_text(
                f"🎉 Привычка '{context.user_data['habit_description']}' \
                    успешно добавлена!",
                reply_markup=self.views.get_habit_menu_keyboard()
            )
            
            # Очищаем временные данные
            for key in list(context.user_data.keys()):
                if key.startswith('habit_'):
                    del context.user_data[key]
            
            return State.HABBIT_MENU
        else:
            await update.message.reply_text(
                "Пожалуйста, введите время в формате ЧЧ:ММ",
                reply_markup=self.views.get_time_selection_keyboard()
            )
            return State.HABBIT_MENU_ADD_TIME
    
    async def _start_delete_habit(self, update: Update, 
                                  context: ContextTypes.DEFAULT_TYPE, 
                                  tg_username: str) -> int:
        """Начать процесс удаления привычки"""
        user_id = self.user_service.get_id_user(tg_username)
        habits = self.habit_service.get_user_habits(user_id)
        
        if not habits:
            await update.message.reply_text(
                "У вас нет привычек для удаления",
                reply_markup=self.views.get_habit_menu_keyboard()
            )
            return State.HABBIT_MENU
        
        message = "Выберите привычку для удаления:\n\n"
        for i, habit in enumerate(habits, 1):
            message += f"{i}. {habit['description']}\n"
        
        context.user_data['habits_for_deletion'] = habits
        await update.message.reply_text(
            message + "\nВведите номер привычки или 'Отмена'",
            reply_markup=Keyboard.NOTIFY_MENU_DELETE_CANCEL_KEYBOARD
        )
        
        return State.HABBIT_MENU_DELETE
    
    async def delete_habit(self, update: Update, 
                           context: ContextTypes.DEFAULT_TYPE) -> int:
        """Удаление привычки"""
        text = update.message.text
        tg_username = update.effective_user.username
        
        if text == "Отмена":
            return await self._cancel_operation(update)
        
        try:
            habit_number = int(text) - 1
            habits = context.user_data.get('habits_for_deletion', [])
            
            if 0 <= habit_number < len(habits):
                habit = habits[habit_number]
                self.habit_service.delete_habit(habit['id_habit'])
                
                await update.message.reply_text(
                    f"Привычка '{habit['description']}' удалена",
                    reply_markup=self.views.get_habit_menu_keyboard()
                )
                return State.HABBIT_MENU
            else:
                await update.message.reply_text("Неверный номер привычки")
                return State.HABBIT_MENU_DELETE
                
        except ValueError:
            await update.message.reply_text(
                "Пожалуйста, введите номер привычки")
            return State.HABBIT_MENU_DELETE
    
    async def _cancel_operation(self, update: Update) -> int:
        """Отмена операции"""
        await update.message.reply_text(
            "Операция отменена",
            reply_markup=self.views.get_habit_menu_keyboard()
        )
        return State.HABBIT_MENU
