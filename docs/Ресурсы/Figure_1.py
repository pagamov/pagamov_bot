import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Настройка стиля для научной работы
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'DejaVu Sans' # Стандартный шрифт, поддерживающий кириллицу

def generate_data():
    days = np.arange(1, 61)
    
    # --- Контрольная группа (резкий спад) ---
    # Начинаем с 95%, после 7 дня начинается экспоненциальный спад
    control = []
    for d in days:
        if d <= 7:
            val = 95 - (d * 1.5) # Незначительный спад в первую неделю
        else:
            # Экспоненциальное падение после первой недели
            val = 85 * np.exp(-0.05 * (d - 7)) + 10 
        control.append(val + np.random.normal(0, 1)) # Добавляем небольшой шум
    
    # --- Экспериментальная группа (плавный спад и всплески) ---
    experimental = []
    for d in days:
        # Более медленный линейный спад
        base_val = 95 - (d * 0.6)
        
        # Имитируем "всплески" активности при получении бейджей (на 14, 21, 30, 45 дни)
        spike = 0
        if d in [14, 21, 30, 45]:
            spike = 8 # Резкий возврат пользователей
        elif d in range(15, 17, 1) or d in range(31, 33, 1):
            spike = 4 # Эхо всплеска
            
        val = base_val + spike
        experimental.append(val + np.random.normal(0, 1.5)) # Чуть больше шума для реализма
        
    return days, np.array(control), np.array(experimental)

# Генерация данных
days, control_data, exp_data = generate_data()

# Создание фигуры
plt.figure(figsize=(12, 7))

# Отрисовка линий
plt.plot(days, exp_data, color='#2ecc71', linewidth=3, label='Экспериментальная группа (Авторская методика)', marker='o', markevery=5, markersize=6)
plt.plot(days, control_data, color='#e74c3c', linewidth=3, label='Контрольная группа (Стандартный трекер)', marker='x', markevery=5, markersize=6)

# Оформление осей и заголовка
plt.title('Динамика ежедневной активной аудитории (DAU) в течение 60 дней', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('День эксперимента', fontsize=13)
plt.ylabel('Процент активных пользователей (%)', fontsize=13)

# Настройка шкалы
plt.xticks(np.arange(0, 61, 5))
plt.yticks(np.arange(0, 101, 10))
plt.xlim(0, 61)
plt.ylim(0, 105)

# Добавление легенды
plt.legend(loc='upper right', fontsize=12, frameon=True)

# Добавление аннотации про "эффект первой недели"
plt.annotate('Эффект первой недели\n(резкий отток)', xy=(7, 85), xytext=(2, 62),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8),
             fontsize=11, color='#c0392b')

# Добавление аннотации про геймификацию
plt.annotate('Всплески активности\n(получение достижений)', xy=(30, 75), xytext=(25, 62),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8),
             fontsize=11, color='#27ae60')

# Добавление сетки с прозрачностью
plt.grid(True, linestyle='--', alpha=0.6)

# Сохранение и вывод
plt.tight_layout()
plt.savefig('graph_1_dau.png', dpi=300) # Высокое разрешение для печати в дипломе
plt.show()
