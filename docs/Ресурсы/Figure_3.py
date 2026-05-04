import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.interpolate import interp1d

# Настройка стиля
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'DejaVu Sans'

def generate_perfect_retention():
    days = np.arange(0, 61)
    
    # --- Опорные точки с "Якорем" на 90-м дне ---
    # Мы добавляем точку на 90 день, чтобы кривая не загнулась вверх
    x_points = np.array([0, 30, 60, 90]) 
    
    # Экспериментальная группа: [100% -> 45% -> 28% -> 20% (якорь)]
    y_exp_points = np.array([100, 45, 28, 20])
    
    # Контрольная группа: [100% -> 22% -> 11% -> 5% (якорь)]
    y_ctrl_points = np.array([100, 22, 11, 5])
    
    # Теперь используем 'cubic', так как у нас 4 точки (это теперь работает!)
    f_exp = interp1d(x_points, y_exp_points, kind='cubic')
    f_ctrl = interp1d(x_points, y_ctrl_points, kind='cubic')
    
    # Генерируем значения только для первых 60 дней
    exp_retention = f_exp(days)
    ctrl_retention = f_ctrl(days)
    
    # Добавляем минимальный шум для реализма
    exp_retention += np.random.normal(0, 0.15, size=len(days))
    ctrl_retention += np.random.normal(0, 0.15, size=len(days))
    
    return days, ctrl_retention, exp_retention

# Генерация данных
days, ctrl_retention, exp_retention = generate_perfect_retention()

# Создание фигуры
plt.figure(figsize=(12, 7))

# Отрисовка кривых
plt.plot(days, exp_retention, color='#2ecc71', linewidth=4, label='Экспериментальная группа (Авторская методика)', zorder=3)
plt.plot(days, ctrl_retention, color='#e74c3c', linewidth=4, label='Контрольная группа (Стандартный трекер)', zorder=3)

# Маркировка ключевых точек
plt.scatter([30, 60], [45, 28], color='#27ae60', s=80, zorder=4, edgecolor='white')
plt.scatter([30, 60], [22, 11], color='#c0392b', s=80, zorder=4, edgecolor='white')

# Подписи к точкам
plt.text(31, 46, '45%', fontsize=12, fontweight='bold', color='#27ae60')
plt.text(61, 29, '28%', fontsize=12, fontweight='bold', color='#27ae60')
plt.text(31, 23, '22%', fontsize=12, fontweight='bold', color='#c0392b')
plt.text(61, 12, '11%', fontsize=12, fontweight='bold', color='#c0392b')

# Оформление
plt.title('Кривая удержания пользователей (Retention Curve)\nза период эксперимента', fontsize=16, fontweight='bold', pad=20)
plt.xlabel('День с момента регистрации', fontsize=13)
plt.ylabel('Процент удержания (%)', fontsize=13)

plt.xticks(np.arange(0, 61, 10))
plt.yticks(np.arange(0, 101, 10))
plt.xlim(0, 62)
plt.ylim(0, 105)

plt.legend(loc='upper right', fontsize=12, frameon=True)

# Аннотация про плато
plt.annotate('Выход на плато\n(Стабилизация ядра)', xy=(50, 30), xytext=(40, 50),
             arrowprops=dict(arrowstyle='->', color='black', linewidth=1.5),
             fontsize=12, color='#2c3e50', fontweight='bold')

plt.grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.savefig('graph_3_retention_final.png', dpi=300)
plt.show()
