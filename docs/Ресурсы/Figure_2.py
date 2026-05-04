import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Настройка стиля
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'DejaVu Sans'

def generate_streak_data():
    # N = 30 человек в каждой группе
    n_users = 30
    
    # --- Контрольная группа ---
    # Большинство людей срываются быстро (экспоненциальное распределение)
    # Средняя серия около 5-7 дней
    control_streaks = np.random.exponential(scale=6, size=n_users)
    control_streaks = np.clip(control_streaks, 1, 60).astype(int)
    
    # --- Экспериментальная группа ---
    # Распределение смещено вправо (Гамма-распределение)
    # Многие достигают 20-40 дней, некоторые доходят до 60
    exp_streaks = np.random.gamma(shape=5, scale=5, size=n_users)
    exp_streaks = np.clip(exp_streaks, 1, 60).astype(int)
    
    return control_streaks, exp_streaks

# Генерация данных
control_data, exp_data = generate_streak_data()

# Создание фигуры
plt.figure(figsize=(12, 7))

# Отрисовка гистограмм
# Используем sns.histplot для красивого наложения
sns.histplot(exp_data, color='#2ecc71', label='Экспериментальная группа', 
             kde=True, stat="count", alpha=0.6, bins=20, edgecolor='white')
sns.histplot(control_data, color='#e74c3c', label='Контрольная группа', 
              kde=True, stat="count", alpha=0.6, bins=20, edgecolor='white')

# Добавление вертикальной линии "Порога привычки" (21 день)
plt.axvline(x=21, color='grey', linestyle='--', linewidth=2)
plt.text(22, 1, 'Порог устойчивости\n(21 день)', color='grey', fontweight='bold', fontsize=11)

# Оформление
plt.title('Распределение длины серий выполнения привычек\n(Streak Distribution)', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('Количество дней подряд (длина серии)', fontsize=13)
plt.ylabel('Количество пользователей', fontsize=13)

# Настройка шкалы
plt.xticks(np.arange(0, 61, 5))
plt.yticks(np.arange(0, 16, 2))
plt.xlim(0, 60)
plt.ylim(0, 15)

# Легенда
plt.legend(loc='upper right', fontsize=12, frameon=True)

# Добавление поясняющей надписи о результате
plt.text(30, 10, 'Заметный сдвиг\nв сторону\nдолгосрочных серий', 
         fontsize=12, color='#27ae60', fontweight='bold', 
         bbox=dict(facecolor='white', alpha=0.8, edgecolor='#2ecc71'))

plt.grid(True, linestyle='--', alpha=0.5)

# Сохранение
plt.tight_layout()
plt.savefig('graph_2_streaks.png', dpi=300)
plt.show()
