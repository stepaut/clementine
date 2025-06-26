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
from modules.mood.DaylioJournal import DaylioJournal
from modules.timedata.TimeData import TimeData
from modules.dailydata.DailyData import DailyData

app = Flask(__name__)

current_year = datetime.now().year

# Initialize data handlers as None
mood_data = None
time_data = None
daily_data = None

# Create a temporary directory for uploaded files
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'clementine_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    """Main page with file upload form"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads"""
    global mood_data, time_data, daily_data
    
    try:
        # Process mood file
        if 'mood_file' in request.files and request.files['mood_file'].filename:
            mood_file = request.files['mood_file']
            mood_path = os.path.join(UPLOAD_FOLDER, 'mood.csv')
            mood_file.save(mood_path)
            mood_data = DaylioJournal(mood_path)
            return jsonify({
                'status': 'success',
                'message': 'Mood data uploaded successfully',
                'redirect': url_for('mood_dashboard')
            })
        
        # Process time file and color dictionary
        if 'time_file' in request.files and 'color_file' in request.files:
            time_file = request.files['time_file']
            color_file = request.files['color_file']
            
            if time_file.filename and color_file.filename:
                # Save time file
                time_path = os.path.join(UPLOAD_FOLDER, 'time.csv')
                time_file.save(time_path)
                
                # Save and process color dictionary
                color_path = os.path.join(UPLOAD_FOLDER, 'color.csv')
                color_file.save(color_path)
                
                try:
                    # Read color dictionary
                    color_df = pd.read_csv(color_path)
                    
                    # Check if required columns exist
                    required_columns = ['Activity', 'Color']
                    missing_columns = [col for col in required_columns if col not in color_df.columns]
                    
                    if missing_columns:
                        return jsonify({
                            'status': 'error',
                            'message': f'Color dictionary file must contain columns: {", ".join(missing_columns)}'
                        }), 400
                    
                    # Initialize TimeData with path and color dictionary
                    time_data = TimeData(time_path, color_path)
                    return jsonify({
                        'status': 'success',
                        'message': 'Time data uploaded successfully',
                        'redirect': url_for('time_dashboard')
                    })
                except Exception as e:
                    return jsonify({
                        'status': 'error',
                        'message': f'Error processing color dictionary: {str(e)}'
                    }), 400
            elif time_file.filename or color_file.filename:
                return jsonify({
                    'status': 'error',
                    'message': 'Time Data and Color Dictionary files must be uploaded together'
                }), 400
        
        # Process daily file
        if 'daily_file' in request.files and request.files['daily_file'].filename:
            daily_file = request.files['daily_file']
            daily_path = os.path.join(UPLOAD_FOLDER, 'daily.csv')
            daily_file.save(daily_path)
            daily_data = DailyData(daily_path)
            return jsonify({
                'status': 'success',
                'message': 'Daily data uploaded successfully',
                'redirect': url_for('daily_dashboard')
            })
        
        return jsonify({
            'status': 'error',
            'message': 'No files were uploaded'
        }), 400
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/mood')
def mood_dashboard():
    """Mood tracking dashboard"""
    if mood_data is None:
        return redirect(url_for('index'))
    
    try:
        # Get unique years from the data
        years = sorted(mood_data.data.index.year.unique())
        
        # Generate plots for each year
        year_plots = {}
        for year in years:
            plot = mood_data.gen_plot(year=year)
            trend_line = mood_data.gen_mood_trend_line(year=year)

            year_plots[year] = {
                'plot': get_plot_as_base64(plot),
                'trend_line': get_plot_as_base64(trend_line),
            }
        
        return render_template('mood.html', year_plots=year_plots, years=years)
    except Exception as e:
        return f"Ошибка при генерации графиков: {str(e)}", 500

@app.route('/time')
def time_dashboard():
    """Time tracking dashboard"""
    if time_data is None:
        return redirect(url_for('index'))
    
    try:      
        
        daily = time_data.plot_daily()

        plot1 = time_data.draw_plot("week", False)

        return render_template('time.html',
                               pie_img=get_plot_as_base64(daily),
                               bar_img=get_plot_as_base64(daily),
                               heatmap_img=get_plot_as_base64(plot1))
    except Exception as e:
        return f"Ошибка при генерации графиков: {str(e)}", 500

@app.route('/daily')
def daily_dashboard():
    """Daily data dashboard"""
    if daily_data is None:
        return redirect(url_for('index'))
    
    try:
        # Generate all plots from DailyData
        figs = daily_data.plot_all()
        
        # Convert all figures to base64 images
        images = []
        for fig in figs:
            img = get_plot_as_base64(fig)
            images.append(img)
        
        return render_template('daily.html', plot_images=images)
    except Exception as e:
        return f"Ошибка при генерации графиков: {str(e)}", 500

@app.route('/time/report')
def time_report():
    """Генерация и скачивание html-отчета по времени"""
    if time_data is None:
        return redirect(url_for('index'))
    try:
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

if __name__ == '__main__':
    app.run(debug=True) 