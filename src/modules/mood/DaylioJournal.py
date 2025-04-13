import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
import matplotlib as mpl
import calmap
from matplotlib import colors

# Daylio moods ordered from worst to best
ORDERED_MOODS = ['awful', 'bad', 'meh', 'good', 'great']
# The scale for your mood score. This means scores will be between 0 and range(SCALE)
SCALE = 5


class DaylioJournal:
    def __init__(self,
                 path_to_csv,
                 ordered_moods=ORDERED_MOODS,
                 scale=SCALE):

        self.ordered_moods = ordered_moods
        self.scale = scale
        self.raw_data = pd.read_csv(path_to_csv, index_col=False)
        self.data, self.activities = self.clean_df()

    def clean_df(self):
        df = self.raw_data
        df = df.iloc[::-1]
        ordered_moods = self.ordered_moods
        scale = self.scale

        df['mood_num'] = df['mood'].replace(ordered_moods, range(len(ordered_moods)))

        df.full_date = pd.to_datetime(df.full_date)
        df_with_one_hot_encoding, all_activities = self.convert_activities_to_categorical(df)
        df_with_mood_scores = self.mood_to_score(df_with_one_hot_encoding)

        df_with_mood_scores = df_with_mood_scores.set_index('full_date')

        return (df_with_mood_scores, all_activities)

    def gen_hist(self):
        moods = self.data[['mood']]

        sns.set()
        sns.countplot(data=moods, x="mood", order=ORDERED_MOODS, color='gray')
        plt.title("mood distribution")

        return (plt)
    
    def gen_plot(self, year):
        colors = ["red", "orange", "yellow", "lawngreen", "green"]
        palette = mpl.colors.LinearSegmentedColormap.from_list("palette", colors, len(colors))
        df = self.data
        plt.figure(figsize=(20, 10))
        calmap.yearplot(df['mood_num'], year=year, cmap=palette, daylabels='MTWTFSS', dayticks=[0, 2, 4, 6],
                linewidth=2.5)

    def gen_dots(self, matrix_length=30):
        '''
        Generates a matrix dot plot visualization representing all my moods over time.
        '''
        df = self.data

        mood_categories = {}
        category = 0
        for mood in self.ordered_moods:
            mood_categories[mood] = category
            category += 1

        mood_list = []
        for mood in list(df.mood):
            mood_list.append(mood_categories[mood])

        next_round_value = matrix_length * (len(mood_list) // matrix_length + 1)
        matrix_height = int(next_round_value / matrix_length)
        mood_list_with_remainder = mood_list + [category] * (next_round_value - len(mood_list))

        all_mood_array = []

        for x in range(matrix_height):
            new_row = mood_list_with_remainder[(x * matrix_length):((x + 1) * matrix_length)]
            all_mood_array.append(new_row)

        all_mood_array = np.array(all_mood_array)

        plt.figure(figsize=(5, 5))
        colormap = colors.ListedColormap([
            "red", "orange", "yellow", "lawngreen",
            "green", "darkgrey"
        ])
        plt.imshow(all_mood_array, cmap=colormap)
        plt.axis('off')

        return (plt)

    def gen_wordcloud_per_mood(self):
        all_words = ''
        stopwords = set(STOPWORDS)

        words_by_mood = {}

        for mood in self.ordered_moods:
            words_by_mood[mood] = ''

        for index, row in self.data.iterrows():
            mood = row[['mood']].mood
            note = row[['note']].note
            if type(note) == str:
                clean_note = note.translate(str.maketrans('', '', string.punctuation)).lower()
            words_by_mood[mood] += clean_note

        wordcloud_dict = {}

        for mood, words in words_by_mood.items():
            wordcloud = WordCloud(width=800,
                                height=800,
                                background_color='white',
                                stopwords=stopwords,
                                min_font_size=10,
                                max_words=100).generate(words)
            plt.figure(figsize=(8, 8), facecolor=None)
            plt.imshow(wordcloud)
            plt.axis("off")
            plt.tight_layout(pad=0)
            plt.savefig(mood + ".png")
            wordcloud_dict[mood] = plt

        return (wordcloud_dict)

    def gen_entries_over_time_hist(self):
        df = self.data
        df.full_date = pd.to_datetime(df.full_date).dt.to_period('M').dt.to_timestamp()
        earliest_entry = min(df.full_date)
        start_year = earliest_entry.year
        start_month = earliest_entry.month

        latest_entry = max(df.full_date)
        end_year = latest_entry.year
        end_month = latest_entry.month

        all_months = [
            date(m // 12, m % 12 + 1, 1)
            for m in range(start_year * 12 + start_month - 1, end_year * 12 + end_month)
        ]

        num_entries = []

        for month in all_months:
            num_entries.append(len(df[df.full_date == month]))

        ax = plt.subplot(111)
        ax.bar(all_months, num_entries, width=25, color="darkorange")
        ax.xaxis_date()
        plt.title("# journal entries written, by month")

        return (plt)

    def convert_activities_to_categorical(self, df):
        all_activities = []

        for index, row in df.iterrows():
            if type(row['activities']) == str:
                activities_list = row['activities'].split(" | ")
                for activity in activities_list:
                    if activity not in all_activities:
                        all_activities.append(activity)

        categorical_activity_matrix = []

        for index, row in df.iterrows():
            activity_list_binary = []
            if type(row['activities']) != str:
                activity_list_binary = [False] * len(all_activities)
            else:
                for activity in all_activities:
                    if activity in row['activities']:
                        activity_list_binary.append(True)
                    else:
                        activity_list_binary.append(False)
            categorical_activity_matrix.append(activity_list_binary)

        categorical_df = pd.DataFrame(categorical_activity_matrix, columns=all_activities)

        full_df = pd.concat([df, categorical_df], axis=1)

        return (full_df, all_activities)

    def mood_to_score(self, df):
        original_metric = {}
        num = 1
        for mood in self.ordered_moods:
            original_metric[mood] = num
            num += 1

        old_min = min(original_metric.values())
        old_max = max(original_metric.values())

        ordered_mood_scores = {}
        for mood in original_metric.keys():
            value = original_metric[mood]
            weighted_score = self.scale / (old_max - old_min) * (value - old_max) + self.scale
            ordered_mood_scores[mood] = weighted_score

        df['mood_score'] = df['mood'].map(ordered_mood_scores)

        return (df)

    def gen_mood_trend_line(self, window_size=30, year=None):
        '''
        Создает линейный график тренда настроения с использованием скользящего среднего.
        
        Входные параметры:
            window_size: int, размер окна для скользящего среднего (по умолчанию: 7 дней)
            year: int, год для отображения данных. Если None, отображаются все данные
        Выходные данные:
            PyPlot figure
        '''
        df = self.data.copy()
        
        # Фильтруем данные по году, если указан
        if year is not None:
            df = df[df.index.year == year]
        
        df['mood_score_ma'] = df['mood_score'].rolling(window=window_size, min_periods=1).mean()
        
        plt.figure(figsize=(15, 6))
        
        # Определяем границы для цветовых зон
        mood_zones = {
            'awful': (0, 1),
            'bad': (1, 2),
            'meh': (2, 3),
            'good': (3, 4),
            'great': (4, 5)
        }
        
        # Цвета для каждой зоны
        colors = {
            'awful': '#FF0000',  # Красный
            'bad': '#FFA500',    # Оранжевый
            'meh': '#FFFF00',    # Желтый
            'good': '#90EE90',   # Светло-зеленый
            'great': '#008000'   # Зеленый
        }
        
        # Создаем фон для каждой зоны настроения
        for mood, (min_val, max_val) in mood_zones.items():
            plt.fill_between(df.index, min_val, max_val, 
                           color=colors[mood], alpha=0.2)
        
        # Рисуем линию тренда
        plt.plot(df.index, df['mood_score_ma'], linewidth=2, color='blue')
        
        # Формируем заголовок в зависимости от того, указан ли год
        if year is not None:
            plt.title(f'Тренд настроения за {year} год (Скользящее среднее, окно {window_size} дней)')
        else:
            plt.title(f'Тренд настроения (Скользящее среднее, окно {window_size} дней)')
            
        plt.xlabel('Дата')
        plt.ylabel('Оценка настроения')
        
        # Настраиваем сетку
        plt.grid(True, alpha=0.3)
        
        # Настраиваем формат дат на оси X
        from matplotlib.dates import DateFormatter, MonthLocator
        import locale
        
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
        # Создаем форматтер для дат в формате "месяц год"
        date_format = DateFormatter('%b %y')  # %b для сокращенного названия месяца, %y для двухзначного года
        
        ax = plt.gca()
        
        # Устанавливаем locator для линий сетки и подписей
        ax.xaxis.set_major_locator(MonthLocator())
        ax.xaxis.set_major_formatter(date_format)
        
        # Добавляем вертикальные линии для каждого месяца
        ax.grid(True, axis='x', linestyle='-', alpha=0.8, color='gray')
        
        # Добавляем легенду для цветовых зон
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor=colors[mood], alpha=0.2, label=mood) 
                         for mood in self.ordered_moods]
        plt.legend(handles=legend_elements, loc='upper right')
        
        # Настраиваем отступы для предотвращения обрезания подписей
        plt.tight_layout()
        
        return plt 