import pandas as pd


def create_temp_timedata_from_TouchTime(file: str):
    df = pd.read_csv(file)
    df['Start'] = pd.to_datetime(df['Start'])
    df['End'] = pd.to_datetime(df['End'])
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # удалаяем битые столбцы
    df['Total'] = ((df['End']-df['Start']).dt.total_seconds() / 60).astype(int)

    years = df['Start'].dt.year.unique()
    for year in years:
        dfy = df[df['Start'].dt.year == year]
        dfy.to_csv(f'temp/time_{year}_0.csv')
