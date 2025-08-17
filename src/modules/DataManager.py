import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import sys

# Добавляем путь к родительской директории для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.mood.DaylioJournal import DaylioJournal
from modules.timedata.TimeData import TimeData
from modules.dailydata.DailyData import DailyData

class DataManager:
    def __init__(self, statistics_folder: str, color_file: str):
        """
        Инициализация менеджера данных
        
        Args:
            statistics_folder: Путь к папке "Статистика"
            color_file: Путь к файлу с цветами для активностей
        """
        self.statistics_folder = statistics_folder
        self.color_file = color_file
        self.mood_data = {}
        self.time_data = {}
        self.daily_data = {}
        self.available_years = []
        
        # Загружаем все доступные данные
        self.load_all_data()
    
    def load_all_data(self):
        """Загружает все доступные данные из папки статистики"""
        if not os.path.exists(self.statistics_folder):
            print(f"Папка {self.statistics_folder} не найдена!")
            return
        
        # Проверяем существование файла с цветами
        if not os.path.exists(self.color_file):
            print(f"Файл с цветами {self.color_file} не найден!")
            return
        
        # Получаем список папок с годами
        year_folders = []
        for item in os.listdir(self.statistics_folder):
            item_path = os.path.join(self.statistics_folder, item)
            if os.path.isdir(item_path) and item.isdigit():
                year_folders.append(int(item))
        
        self.available_years = sorted(year_folders)
        
        # Загружаем данные для каждого года
        for year in self.available_years:
            year_folder = os.path.join(self.statistics_folder, str(year))
            self.load_year_data(year, year_folder)
    
    def load_year_data(self, year: int, year_folder: str):
        """Загружает данные для конкретного года"""
        # Загружаем данные настроения
        mood_file = os.path.join(year_folder, f"mood_{year}.csv")
        if os.path.exists(mood_file):
            try:
                self.mood_data[year] = DaylioJournal(mood_file)
                print(f"Загружены данные настроения за {year} год")
            except Exception as e:
                print(f"Ошибка загрузки данных настроения за {year} год: {e}")
        
        # Загружаем данные времени (используем общий файл с цветами)
        time_file = os.path.join(year_folder, f"time_{year}.csv")
        
        if os.path.exists(time_file):
            try:
                self.time_data[year] = TimeData(time_file, self.color_file)
                print(f"Загружены данные времени за {year} год")
            except Exception as e:
                print(f"Ошибка загрузки данных времени за {year} год: {e}")
        
        # Загружаем ежедневные данные
        daily_file = os.path.join(year_folder, f"data_{year}.csv")
        if os.path.exists(daily_file):
            try:
                self.daily_data[year] = DailyData(daily_file)
                print(f"Загружены ежедневные данные за {year} год")
            except Exception as e:
                print(f"Ошибка загрузки ежедневных данных за {year} год: {e}")
    
    def get_mood_data(self, year: Optional[int] = None) -> Optional[DaylioJournal]:
        """Получает данные настроения для указанного года или последнего доступного"""
        if year is None:
            year = max(self.mood_data.keys()) if self.mood_data else None
        
        return self.mood_data.get(year)
    
    def get_time_data(self, year: Optional[int] = None) -> Optional[TimeData]:
        """Получает данные времени для указанного года или последнего доступного"""
        if year is None:
            year = max(self.time_data.keys()) if self.time_data else None
        
        return self.time_data.get(year)
    
    def get_daily_data(self, year: Optional[int] = None) -> Optional[DailyData]:
        """Получает ежедневные данные для указанного года или последнего доступного"""
        if year is None:
            year = max(self.daily_data.keys()) if self.daily_data else None
        
        return self.daily_data.get(year)
    
    def get_available_years(self) -> List[int]:
        """Возвращает список доступных лет"""
        return self.available_years
    
    def has_mood_data(self, year: Optional[int] = None) -> bool:
        """Проверяет наличие данных настроения"""
        if year is None:
            return len(self.mood_data) > 0
        return year in self.mood_data
    
    def has_time_data(self, year: Optional[int] = None) -> bool:
        """Проверяет наличие данных времени"""
        if year is None:
            return len(self.time_data) > 0
        return year in self.time_data
    
    def has_daily_data(self, year: Optional[int] = None) -> bool:
        """Проверяет наличие ежедневных данных"""
        if year is None:
            return len(self.daily_data) > 0
        return year in self.daily_data
    
    def get_data_summary(self) -> Dict:
        """Возвращает сводку по загруженным данным"""
        return {
            'available_years': self.available_years,
            'mood_years': list(self.mood_data.keys()),
            'time_years': list(self.time_data.keys()),
            'daily_years': list(self.daily_data.keys()),
            'total_mood_records': sum(len(data.data) for data in self.mood_data.values()),
            'total_time_records': sum(len(data.df) for data in self.time_data.values()),
            'total_daily_records': sum(len(data.df) for data in self.daily_data.values())
        }
