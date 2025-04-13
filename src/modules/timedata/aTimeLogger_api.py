import pandas as pd
from datetime import datetime

def timeToDay(x: str):
    return datetime.strptime(x, u'%Y-%m-%d %H:%M')

def add_group(x: str):
    if len(x) == 0:
        return ""

    return x + ":"

def create_temp_timedata_from_aTimeLogger(file: str):
    df = pd.read_csv(file, on_bad_lines="warn", sep=",")
    df = df.fillna('')
    df['Start'] = df['Начало'].apply(lambda x: timeToDay(x))
    df['End'] = df['Конец'].apply(lambda x: timeToDay(x))
    df['Group'] = df["Group"].apply(lambda x: add_group(x))
    df['Group'] = df['Group'] + df["Group.1"]
    df['Activity'] = df['Group'] + ":" + df['Тип']
    df['Total'] = ((df['End']-df['Start']).dt.total_seconds() / 60).astype(int)

    df = df.drop(columns=["Комментарий", "Тип", "Начало",
                "Конец", "Продолжительность", "Group", "Group.1"])
    
    years = df['Start'].dt.year.unique()
    for year in years:
        dfy = df[df['Start'].dt.year == year]
        dfy.to_csv(f'temp/time_{year}_1.csv')
