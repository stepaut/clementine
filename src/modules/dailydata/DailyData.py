import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import calmap


greens = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
green_palette = mpl.colors.LinearSegmentedColormap.from_list(
    "green_palette", greens, len(greens))

yellows3 = ["#ebedf0", "#ffd900", "#ff4d00", "#000000"]
yellow_palette3 = mpl.colors.LinearSegmentedColormap.from_list(
    "yellow_palette3", yellows3, len(yellows3))

yellows2 = ["#ebedf0", "#ffd900", "#ff4d00"]
yellow_palette2 = mpl.colors.LinearSegmentedColormap.from_list(
    "yellow_palette2", yellows2, len(yellows2))

mood = ["#ef2725", "#ef8c25", "#ffd900", "#93c47d", "#38761d"]
mood_palette = mpl.colors.LinearSegmentedColormap.from_list(
    "mood_palette", mood, len(mood))

maps = {
    "Do": yellow_palette3,
    "Do2": green_palette,
    "Mood": mood_palette,
}

default_map = green_palette
cmap = mood_palette


class DailyData:
    def __init__(self,
                 path_to_csv):
        df = pd.read_csv(path_to_csv)
        # Робастный парсинг дат: поддержка смешанных форматов
        date_series = df['Date'].astype(str).str.strip()
        # Первая попытка: mixed + dayfirst=True
        parsed = pd.to_datetime(date_series, format='mixed', dayfirst=True, errors='coerce')
        # Вторая попытка для неразобранных: mixed + dayfirst=False
        mask_na = parsed.isna()
        if mask_na.any():
            parsed2 = pd.to_datetime(date_series[mask_na], format='mixed', dayfirst=False, errors='coerce')
            parsed.loc[mask_na] = parsed2
        # Третья попытка: общий парсер без формата (на случай ISO и пр.)
        mask_na = parsed.isna()
        if mask_na.any():
            parsed3 = pd.to_datetime(date_series[mask_na], errors='coerce')
            parsed.loc[mask_na] = parsed3
        # Если остались некорректные даты — бросаем осмысленную ошибку
        if parsed.isna().any():
            bad_examples = date_series[parsed.isna()].unique()[:5]
            raise ValueError(f"Некорректные значения дат: {bad_examples}")
        df['Date'] = parsed
        df = df.set_index('Date')
        self.df = df

    def plot(self, col):
        cmap = maps.get(col, default_map)
        plt.figure(figsize=(20, 10))
        max_level = self.df[col].max()
        ax = calmap.yearplot(self.df[col], cmap=cmap, daylabels='MTWTFSS', dayticks=[0, 2, 4, 6],
                            linewidth=2.5)
        plt.title(col, fontsize=36)
        fig = ax.get_figure()
        return fig

    def plot_all(self):
        figs = []
        for col in self.df.columns:
            figs.append(self.plot(col))

        return figs
