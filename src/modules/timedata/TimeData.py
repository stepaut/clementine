import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.collections import PolyCollection
import altair as alt
import calendar
import matplotlib.colors

unfinded_color = "lightgray"


def get_fake_time(x: str, morning: bool):
    dt = datetime.strptime(x, u'%Y-%m-%d %H:%M:%S')
    if morning:
        dt = dt.replace(hour=0, minute=0, second=0)
    else:
        dt = dt.replace(hour=23, minute=59, second=59)
    return dt

class TimeData:
    def __init__(self,
                 path_to_csv: str,
                 path_color_dict: str):
        cdf = pd.read_csv(path_color_dict)
        self.color_dict = dict(cdf.values)
        df = pd.read_csv(path_to_csv, on_bad_lines="warn", sep=",")
        self.activities = df.Activity.unique()

        df['Start0'] = df['Start'].apply(lambda x: get_fake_time(x, True))
        df['End0'] = df['End'].apply(lambda x: get_fake_time(x, False))
        df['Start'] = pd.to_datetime(df['Start'])
        df['End'] = pd.to_datetime(df['End'])
        df['Activity'] = df['Activity'].replace(' ', '', regex=True)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # удалаяем битые столбцы
        self.df = df

        df_groupped = df.copy()
        df_groupped['Activity'] = df_groupped['Activity'].apply(
            lambda x: 'Work' if 'Work:' in x else x
        ).apply(
            lambda x: 'Games' if 'Games:' in x else x
        ).apply(
            lambda x: 'PetProjects' if 'PetProjects:' in x else x
        ).replace(':', '', regex=True)
        self.df_groupped = df_groupped

        self.year = df.Start.min().year


    def get_by_week(self, work: bool):
        weeks = range(1, 54)
        dfy = pd.DataFrame(0, index=np.arange(len(weeks)),
                        columns=np.hstack(['week', self.activities]))
        dfy['week'] = weeks
        dfy = dfy.set_index('week')

        dfy["Work"] = 0

        for index, row in self.df.iterrows():
            if "Work" in row.Activity:
                if not work:
                    continue
                dfy["Work"].iloc[row.Start.week - 1] += row.Total
                continue

            # Проверяем, существует ли столбец для данной активности
            if row.Activity in dfy.columns:
                dfy[row.Activity].iloc[row.Start.week - 1] += row.Total
            else:
                # Если столбца нет, добавляем его
                dfy[row.Activity] = 0
                dfy[row.Activity].iloc[row.Start.week - 1] += row.Total

        # удаляем столбцы, в которых все нули
        dfy = dfy.loc[:, (dfy != 0).any(axis=0)]
        dfy.iloc[:, :] = dfy.iloc[:, :].div(60, axis=0)  # minutes to hours

        colors = []

        for c in dfy.columns:
            if c in self.color_dict:
                colors.append(self.color_dict[c])
            else:
                colors.append(unfinded_color)

        return dfy, colors


    def get_by_month(self, work: bool):
        months = range(1, 13)
        dfy = pd.DataFrame(0, index=np.arange(len(months)),
                           columns=np.hstack(['month', self.activities]))
        dfy['month'] = months
        dfy = dfy.set_index('month')

        dfy["Work"] = 0

        for index, row in self.df.iterrows():
            if "Work" in row.Activity:
                if not work:
                    continue
                dfy["Work"].iloc[row.Start.month - 1] += row.Total
                continue

            # Проверяем, существует ли столбец для данной активности
            if row.Activity in dfy.columns:
                dfy[row.Activity].iloc[row.Start.month - 1] += row.Total
            else:
                # Если столбца нет, добавляем его
                dfy[row.Activity] = 0
                dfy[row.Activity].iloc[row.Start.month - 1] += row.Total

        # удаляем столбцы, в которых все нули
        dfy = dfy.loc[:, (dfy != 0).any(axis=0)]
        dfy.iloc[:, :] = dfy.iloc[:, :].div(60, axis=0)  # minutes to hours

        colors = []

        for c in dfy.columns:
            if c in self.color_dict:
                colors.append(self.color_dict[c])
            else:
                colors.append(unfinded_color)

        return dfy, colors


    def draw_plot(self, level:str, work:bool):
        if level == "week":
            dfy, colors = self.get_by_week(work)
        elif level == "month":
            dfy, colors = self.get_by_month(work)
        else:
            raise Exception
        
        ax = dfy.plot(kind='area', stacked=False, figsize=(20, 10), color=colors, linewidth=0)
        plt.title(self.year)
        plt.ylabel('hours')
        plt.xlabel('week')
        plt.show()
        fig = ax.get_figure()
        return fig


    def draw_linegraph(self):
        alt.Chart(self.df_groupped).mark_bar().encode(
            x='Start0',
            x2='End0',
            y='Activity',
            color=alt.Color('Activity', scale=alt.Scale(scheme='dark2'))
        ).properties(
            width=600,
            height=300
        )


    def plot_daily(self, level=None, month=None, week=None, custom_colors=None):
        """
        Создает визуализацию активностей по дням.
        
        Parameters:
        -----------
        df : pandas.DataFrame
            DataFrame с колонками 'Start', 'End', 'Activity', где:
            - Start: datetime, время начала активности
            - End: datetime, время окончания активности
            - Activity: str, название активности
        level : str, optional
            Уровень отображения данных ('month', 'week' или None). 
            При None отображаются все данные. По умолчанию None
        month : int, optional
            Номер месяца (1-12) для фильтрации данных. Используется при level='month'
        week : int, optional
            Номер недели (1-53) для фильтрации данных. Используется при level='week'
        custom_colors : dict, optional
            Пользовательский словарь цветов для активностей
        """
        # Проверяем наличие необходимых колонок
        required_columns = {'Start', 'End', 'Activity'}
        if not all(col in self.df_groupped.columns for col in required_columns):
            raise ValueError(
                f"DataFrame должен содержать колонки: {required_columns}")

        # Создаем копию DataFrame для фильтрации
        df_filtered = self.df_groupped.copy()

        # Фильтруем данные по месяцу или неделе только если указан level
        if level == 'month' and month is not None:
            if not 1 <= month <= 12:
                raise ValueError("Номер месяца должен быть от 1 до 12")
            mask = (df_filtered['Start'].dt.month == month) | (
                df_filtered['End'].dt.month == month)
            df_filtered = df_filtered[mask]
            period_str = f"за {calendar.month_name[month]}"
        elif level == 'week' and week is not None:
            if not 1 <= week <= 53:
                raise ValueError("Номер недели должен быть от 1 до 53")
            mask = (df_filtered['Start'].dt.isocalendar().week == week) | (
                df_filtered['End'].dt.isocalendar().week == week)
            df_filtered = df_filtered[mask]
            period_str = f"за {week}-ю неделю"
        else:
            period_str = "за весь период"

        if df_filtered.empty:
            raise ValueError(f"Нет данных {period_str}")

        # Создаем фигуру и оси
        fig, ax = plt.subplots(figsize=(15, 8))

        # Получаем уникальные даты для настройки оси X (включая даты начала и окончания)
        start_dates = set(df_filtered['Start'].dt.date)
        end_dates = set(df_filtered['End'].dt.date)
        unique_dates = sorted(start_dates.union(end_dates))

        # Создаем словарь для маппинга дат на целые числа
        date_to_num = {date: i for i, date in enumerate(unique_dates)}

        # Создаем словарь для хранения уникальных активностей и их цветов
        unique_activities = df_filtered['Activity'].unique()

        # Используем предопределенные цвета или создаем новые для неизвестных активностей
        activity_colors = custom_colors if custom_colors else self.color_dict.copy()

        # Для активностей, которых нет в словаре, генерируем новые цвета
        unknown_activities = set(unique_activities) - set(activity_colors.keys())
        if unknown_activities:
            new_colors = plt.cm.tab20(np.linspace(0, 1, len(unknown_activities)))
            for activity, color in zip(unknown_activities, new_colors):
                activity_colors[activity] = matplotlib.colors.rgb2hex(color)
        
        # Убеждаемся, что все активности имеют цвета
        for activity in unique_activities:
            if activity not in activity_colors:
                activity_colors[activity] = unfinded_color

        # Для каждой активности создаем прямоугольник
        for idx, row in df_filtered.iterrows():
            start_date = row['Start'].date()
            end_date = row['End'].date()

            # Если активность заканчивается на следующий день
            if start_date != end_date:
                # Первая часть активности (до полуночи)
                x_pos = date_to_num[start_date]
                start_time = row['Start'].hour + row['Start'].minute / 60
                ax.bar(x_pos, 24 - start_time, bottom=start_time, width=1.0,
                    color=activity_colors[row['Activity']],
                    label=row['Activity'] if idx == 0 else "", alpha=0.7)

                # Вторая часть активности (после полуночи)
                x_pos = date_to_num[end_date]
                end_time = row['End'].hour + row['End'].minute / 60
                ax.bar(x_pos, end_time, bottom=0, width=1.0,
                    color=activity_colors[row['Activity']], alpha=0.7)
            else:
                # Обычная активность в пределах одного дня
                x_pos = date_to_num[start_date]
                start_time = row['Start'].hour + row['Start'].minute / 60
                end_time = row['End'].hour + row['End'].minute / 60
                ax.bar(x_pos, end_time - start_time, bottom=start_time, width=1.0,
                    color=activity_colors[row['Activity']],
                    label=row['Activity'] if idx == 0 else "", alpha=0.7)

        # Настраиваем оси
        ax.set_ylim(24, 0)  # Инвертируем ось Y
        ax.set_ylabel('Время (часы)')
        ax.set_xlabel('Дата')

        # Устанавливаем метки времени на оси Y
        hours = range(0, 24, 2)
        ax.set_yticks(hours)
        ax.set_yticklabels([f'{hour:02d}:00' for hour in hours])

        # Настраиваем ось X
        ax.set_xticks(range(len(unique_dates)))
        ax.set_xticklabels([date.strftime('%Y-%m-%d')
                        for date in unique_dates], rotation=45)

        # Устанавливаем пределы оси X, чтобы убрать отступы
        ax.set_xlim(-0.5, len(unique_dates) - 0.5)

        # Добавляем сетку
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)

        # Добавляем легенду с уникальными активностями
        handles, labels = [], []
        for activity in unique_activities:
            handle = plt.Rectangle(
                (0, 0), 1, 1, color=activity_colors[activity], alpha=0.7)
            handles.append(handle)
            labels.append(activity)
        plt.legend(handles, labels, bbox_to_anchor=(1.05, 1), loc='upper left')

        # Добавляем заголовок
        plt.title(f'График активностей {period_str}')

        # Настраиваем отступы
        plt.tight_layout()

        # Показываем график
        plt.show()

        return fig

    def generate_report(self, by='week', years=None, to_csv=None, to_excel=None, work=True):
        """
        Генерирует отчеты по неделям или месяцам для каждого года.
        Возвращает словарь: {год: DataFrame}
        by: 'week' или 'month'
        years: список лет (по умолчанию все года в данных)
        to_csv: путь к папке для сохранения csv (если None, не сохраняет)
        to_excel: путь к файлу для сохранения excel (если None, не сохраняет)
        work: учитывать ли Work-активности
        """
        df = self.df.copy()
        df['Year'] = df['Start'].dt.year
        all_years = sorted(df['Year'].unique())
        if years is None:
            years = all_years
        reports = {}
        excel_writer = None
        if to_excel:
            excel_writer = pd.ExcelWriter(to_excel, engine='xlsxwriter')
        for year in years:
            dfy = df[df['Year'] == year]
            if by == 'week':
                dfy['Period'] = dfy['Start'].dt.isocalendar().week
                periods = range(1, 54)
                period_name = 'week'
            elif by == 'month':
                dfy['Period'] = dfy['Start'].dt.month
                periods = range(1, 13)
                period_name = 'month'
            else:
                raise ValueError("by должен быть 'week' или 'month'")
            # Группировка по типу
            def get_type(activity):
                if activity.startswith(':'):
                    return activity.split(':')[1]
                if ':' in activity:
                    return activity.split(':', 1)[0]
                return activity
            dfy['Type'] = dfy['Activity'].apply(get_type)
            types = sorted(dfy['Type'].unique())
            data = []
            for t in types:
                row = []
                for period in periods:
                    mask = (dfy['Type'] == t) & (dfy['Period'] == period)
                    total = dfy.loc[mask, 'Total'].sum() / 60  # часы
                    row.append(total)
                data.append(row)
            report_df = pd.DataFrame(data, index=types, columns=[f'{period_name}_{p}' for p in periods])
            reports[year] = report_df
            if to_csv:
                report_df.to_csv(f"{to_csv}/report_{by}_{year}.csv", encoding='utf-8')
            if excel_writer:
                report_df.to_excel(excel_writer, sheet_name=f'{by}_{year}')
        if excel_writer:
            excel_writer.save()
        return reports
