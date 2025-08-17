#!/usr/bin/env python3
"""
Тестовый скрипт для проверки загрузки данных настроения
"""

import sys
import os
import pandas as pd

# Добавляем путь к модулям
sys.path.append('src')

from modules.DataManager import DataManager
from config import STATISTICS_FOLDER, COLOR_FILE

def test_mood_data():
    """Тестирует загрузку данных настроения"""
    print("Тестирование загрузки данных настроения...")
    print(f"Папка статистики: {STATISTICS_FOLDER}")
    print(f"Файл цветов: {COLOR_FILE}")
    
    # Проверяем существование папки
    if not os.path.exists(STATISTICS_FOLDER):
        print(f"❌ Папка {STATISTICS_FOLDER} не найдена!")
        return False
    
    # Проверяем существование файла цветов
    if not os.path.exists(COLOR_FILE):
        print(f"❌ Файл цветов {COLOR_FILE} не найден!")
        return False
    
    try:
        # Создаем менеджер данных
        data_manager = DataManager(STATISTICS_FOLDER, COLOR_FILE)
        
        print(f"✅ Доступные годы: {data_manager.get_available_years()}")
        print(f"✅ Годы с данными настроения: {list(data_manager.mood_data.keys())}")
        
        if not data_manager.has_mood_data():
            print("❌ Данные настроения не найдены!")
            return False
        
        # Тестируем каждый год
        for year in data_manager.mood_data.keys():
            print(f"\n--- Тестирование {year} года ---")
            mood_data = data_manager.get_mood_data(year)
            
            print(f"Количество записей: {len(mood_data.data)}")
            print(f"Колонки: {list(mood_data.data.columns)}")
            print(f"Типы данных:")
            for col in mood_data.data.columns:
                print(f"  {col}: {mood_data.data[col].dtype}")
            
            # Проверяем, что mood_num является числовым
            if 'mood_num' in mood_data.data.columns:
                mood_num = mood_data.data['mood_num']
                print(f"mood_num - уникальные значения: {mood_num.unique()}")
                print(f"mood_num - тип: {mood_num.dtype}")
                
                # Проверяем, что нет строковых значений
                non_numeric = mood_num[pd.to_numeric(mood_num, errors='coerce').isna()]
                if len(non_numeric) > 0:
                    print(f"⚠️  Найдены нечисловые значения в mood_num: {non_numeric.unique()}")
            
            # Проверяем mood_score
            if 'mood_score' in mood_data.data.columns:
                mood_score = mood_data.data['mood_score']
                print(f"mood_score - диапазон: {mood_score.min()} - {mood_score.max()}")
                print(f"mood_score - тип: {mood_score.dtype}")
            
            # Пробуем сгенерировать график
            try:
                plot = mood_data.gen_plot(year)
                print(f"✅ Календарная карта для {year} года создана успешно")
            except Exception as e:
                print(f"❌ Ошибка при создании календарной карты для {year} года: {e}")
            
            try:
                trend = mood_data.gen_mood_trend_line(year=year)
                print(f"✅ График тренда для {year} года создан успешно")
            except Exception as e:
                print(f"❌ Ошибка при создании графика тренда для {year} года: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mood_data()
    if success:
        print("\n✅ Тестирование завершено успешно!")
    else:
        print("\n❌ Тестирование завершено с ошибками!")
        sys.exit(1)
