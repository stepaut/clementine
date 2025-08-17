from flask import Flask, render_template, jsonify, request, redirect, url_for, Response
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import tempfile
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
from modules.DataManager import DataManager

# Импортируем конфигурацию
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import STATISTICS_FOLDER, COLOR_FILE

app = Flask(__name__)

# Инициализируем менеджер данных при запуске приложения
print("Загружаем данные из папки статистики...")
data_manager = DataManager(STATISTICS_FOLDER, COLOR_FILE)
print("Загрузка данных завершена!")

def format_date(date):
    """Format date for JSON serialization"""
    if isinstance(date, pd.Timestamp):
        return date.strftime('%Y-%m-%d')
    return date

def get_plot_as_base64(fig):
    """Convert matplotlib plot to base64 string"""
    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close(fig)
    return base64.b64encode(img.getvalue()).decode()

@app.route('/')
def index():
    """Главная страница с обзором доступных данных"""
    summary = data_manager.get_data_summary()
    return render_template('index.html', summary=summary)

@app.route('/mood')
def mood_dashboard():
    """Дашборд настроения"""
    if not data_manager.has_mood_data():
        return render_template('no_data.html', data_type="настроения")
    
    try:
        # Получаем все доступные годы для настроения
        mood_years = sorted(data_manager.mood_data.keys())
        
        # Генерируем графики для каждого года
        year_plots = {}
        for year in mood_years:
            mood_data = data_manager.get_mood_data(year)
            plot = mood_data.gen_plot(year=year)
            trend_line = mood_data.gen_mood_trend_line(year=year)

            year_plots[year] = {
                'plot': get_plot_as_base64(plot),
                'trend_line': get_plot_as_base64(trend_line),
            }
        
        return render_template('mood.html', year_plots=year_plots, years=mood_years)
    except Exception as e:
        return f"Ошибка при генерации графиков настроения: {str(e)}", 500

@app.route('/time')
def time_dashboard():
    """Дашборд времени"""
    if not data_manager.has_time_data():
        return render_template('no_data.html', data_type="времени")
    
    try:
        # Получаем последние доступные данные времени
        time_data = data_manager.get_time_data()
        
        daily = time_data.plot_daily()
        plot1 = time_data.draw_plot("week", False)

        return render_template('time.html',
                               pie_img=get_plot_as_base64(daily),
                               bar_img=get_plot_as_base64(daily),
                               heatmap_img=get_plot_as_base64(plot1))
    except Exception as e:
        return f"Ошибка при генерации графиков времени: {str(e)}", 500

@app.route('/daily')
def daily_dashboard():
    """Дашборд ежедневных данных"""
    if not data_manager.has_daily_data():
        return render_template('no_data.html', data_type="ежедневных данных")
    
    try:
        # Получаем последние доступные ежедневные данные
        daily_data = data_manager.get_daily_data()
        
        # Генерируем все графики из DailyData
        figs = daily_data.plot_all()
        
        # Конвертируем все фигуры в base64 изображения
        images = []
        for fig in figs:
            img = get_plot_as_base64(fig)
            images.append(img)
        
        return render_template('daily.html', plot_images=images)
    except Exception as e:
        return f"Ошибка при генерации графиков ежедневных данных: {str(e)}", 500

@app.route('/time/report')
def time_report():
    """Генерация и скачивание html-отчета по времени"""
    if not data_manager.has_time_data():
        return redirect(url_for('index'))
    
    try:
        time_data = data_manager.get_time_data()
        
        # Генерируем отчеты по неделям и месяцам
        week_reports = time_data.generate_report(by='week')
        month_reports = time_data.generate_report(by='month')
        
        html = '<html><head><meta charset="utf-8"><title>Time Report</title></head><body>'
        html += '<h1>Time Report</h1>'
        
        for year, df in week_reports.items():
            html += f'<h2>Недели {year}</h2>'
            html += df.T.to_html(float_format="{:.2f}".format, border=1)
        
        for year, df in month_reports.items():
            html += f'<h2>Месяцы {year}</h2>'
            html += df.T.to_html(float_format="{:.2f}".format, border=1)
        
        html += '</body></html>'
        
        return Response(html, mimetype='text/html', headers={
            'Content-Disposition': 'attachment;filename=time_report.html'
        })
    except Exception as e:
        return f"Ошибка при генерации отчета: {str(e)}", 500

@app.route('/api/summary')
def api_summary():
    """API endpoint для получения сводки данных"""
    return jsonify(data_manager.get_data_summary())

if __name__ == '__main__':
    app.run(debug=True) 