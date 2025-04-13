import pandas as pd
import os.path

def merge_timedata(years=[2025], parts=[0, 1]):
    for year in years:
        cdf = None
        for part in parts:
            file = f'temp/time_{year}_{part}.csv'
            if os.path.isfile(file):
                df = pd.read_csv(file, on_bad_lines="warn", sep=",")
                if cdf is not None:
                    cdf = pd.concat([df, cdf])
                else:
                    cdf = df
        cdf = cdf.reset_index()
        cdf = cdf.sort_values('Start')
        cdf = cdf.drop(columns="Unnamed: 0")
        cdf = cdf.drop(columns="index")
        cdf.to_csv(f'temp/time_{year}.csv')
