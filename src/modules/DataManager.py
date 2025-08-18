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
        
        # Загружаем ежедневные данные (объединяем data_YYYY.csv и data2_YYYY.csv)
        daily_file = os.path.join(year_folder, f"data_{year}.csv")
        data2_file = os.path.join(year_folder, f"data2_{year}.csv")
        
        if os.path.exists(daily_file) or os.path.exists(data2_file):
            try:
                # Создаем объединенный файл или используем существующий
                merged_file = self._merge_daily_data_files(daily_file, data2_file, year)
                self.daily_data[year] = DailyData(merged_file)
                print(f"Загружены ежедневные данные за {year} год (объединены data и data2)")
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
    
    def generate_data2_files(self):
        """Генерирует файлы data2_YYYY.csv на основе time_YYYY.csv если они не существуют"""
        for year in self.available_years:
            year_folder = os.path.join(self.statistics_folder, str(year))
            time_file = os.path.join(year_folder, f"time_{year}.csv")
            data2_file = os.path.join(year_folder, f"data2_{year}.csv")
            
            # Проверяем, существует ли уже файл data2
            # if os.path.exists(data2_file):
            #     print(f"Файл data2_{year}.csv уже существует, пропускаем")
            #     continue
            
            # Проверяем, существует ли файл time
            if not os.path.exists(time_file):
                print(f"Файл time_{year}.csv не найден, пропускаем генерацию data2_{year}.csv")
                continue
            
            try:
                self._generate_data2_file(time_file, data2_file, year)
                print(f"Сгенерирован файл data2_{year}.csv")
            except Exception as e:
                print(f"Ошибка при генерации data2_{year}.csv: {e}")
    
    def _generate_data2_file(self, time_file: str, data2_file: str, year: int):
        """Генерирует файл data2_YYYY.csv на основе time_YYYY.csv"""
        # Читаем данные времени
        time_df = pd.read_csv(time_file)
        
        # Конвертируем Start в datetime
        time_df['Start'] = pd.to_datetime(time_df['Start'])
        
        # Извлекаем дату из Start
        time_df['Date'] = time_df['Start'].dt.date
        
        # Нормализуем активности: все, что начинается с "Work", объединяем в одну активность "Work"
        time_df['Activity'] = time_df['Activity'].astype(str)
        work_mask = time_df['Activity'].str.match(r'^Work')
        time_df.loc[work_mask, 'Activity'] = 'Work'

        # Получаем все уникальные активности
        all_activities = time_df['Activity'].unique()
        
        # Создаем полный диапазон дат за год
        start_date = pd.Timestamp(year, 1, 1)
        end_date = pd.Timestamp(year, 12, 31)
        all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Создаем DataFrame с датами
        data2_df = pd.DataFrame({
            'Date': all_dates.strftime('%d.%m.%y')
        })
        
        # Для каждой активности создаем столбец
        for activity in all_activities:
            activity_values = []
            for date in all_dates:
                date_obj = date.date()
                # Получаем все записи для этой даты
                day_records = time_df[time_df['Date'] == date_obj]
                
                # Проверяем, была ли эта активность в этот день
                if len(day_records) > 0 and activity in day_records['Activity'].values:
                    activity_values.append(1)
                else:
                    activity_values.append(0)
            
            # Добавляем столбец для этой активности
            data2_df[activity] = activity_values
        
        # Сохраняем файл
        data2_df.to_csv(data2_file, index=False)
    
    def _merge_daily_data_files(self, daily_file: str, data2_file: str, year: int) -> str:
        """Объединяет файлы data_YYYY.csv и data2_YYYY.csv в один файл"""
        # Создаем временный файл для объединенных данных
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        temp_file.close()
        
        # Читаем данные из data_YYYY.csv если он существует
        data_df = None
        if os.path.exists(daily_file):
            data_df = pd.read_csv(daily_file)
            print(f"Загружен файл data_{year}.csv с {len(data_df)} строками")
        
        # Читаем данные из data2_YYYY.csv если он существует
        data2_df = None
        if os.path.exists(data2_file):
            data2_df = pd.read_csv(data2_file)
            print(f"Загружен файл data2_{year}.csv с {len(data2_df)} строками")
        
        # Объединяем данные
        if data_df is not None and data2_df is not None:
            # Оба файла существуют - объединяем по столбцу Date
            merged_df = pd.merge(data_df, data2_df, on='Date', how='outer')
            print(f"Объединены файлы data и data2, результат: {len(merged_df)} строк")
        elif data_df is not None:
            # Только data_YYYY.csv существует
            merged_df = data_df
            print(f"Используется только файл data_{year}.csv")
        elif data2_df is not None:
            # Только data2_YYYY.csv существует
            merged_df = data2_df
            print(f"Используется только файл data2_{year}.csv")
        else:
            # Ни один файл не существует
            raise FileNotFoundError(f"Не найдены файлы data_{year}.csv и data2_{year}.csv")
        
        # Сохраняем объединенный файл
        merged_df.to_csv(temp_file.name, index=False)
        return temp_file.name
    
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
