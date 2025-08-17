import os

# Путь к папке "Статистика" с данными
STATISTICS_FOLDER = r"D:\OneDrive\LIFE\Statistics"

# Путь к файлу с цветами для активностей (общий для всех лет)
COLOR_FILE = r"D:\OneDrive\LIFE\Statistics\static\colors.csv"

# Проверяем существование папки
if not os.path.exists(STATISTICS_FOLDER):
    print(f"Внимание: Папка {STATISTICS_FOLDER} не найдена!")
    print("Пожалуйста, измените путь в config.py на правильный путь к папке 'Статистика'")

# Проверяем существование файла с цветами
if not os.path.exists(COLOR_FILE):
    print(f"Внимание: Файл с цветами {COLOR_FILE} не найден!")
    print("Пожалуйста, измените путь COLOR_FILE в config.py на правильный путь к файлу с цветами")
