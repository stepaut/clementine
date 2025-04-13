from flask import Flask, render_template, jsonify, request, redirect, url_for
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
                
                # Initialize TimeData with both files
                time_data = TimeData(time_path, color_path)
                return jsonify({
                    'status': 'success',
                    'message': 'Time data uploaded successfully',
                    'redirect': url_for('time_dashboard')
                })
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
    """Mood data dashboard"""
    if mood_data is None:
        return redirect(url_for('index'))
    
    try:
        # Generate histogram
        hist_fig = mood_data.gen_hist()
        hist_img = get_plot_as_base64(hist_fig)
        
        # Generate calendar plot
        current_year = datetime.now().year
        calendar_fig = mood_data.gen_plot(current_year)
        calendar_img = get_plot_as_base64(calendar_fig)
        
        # Generate dots plot
        dots_fig = mood_data.gen_dots()
        dots_img = get_plot_as_base64(dots_fig)
        
        return render_template('mood.html', 
                            hist_img=hist_img,
                            calendar_img=calendar_img,
                            dots_img=dots_img)
    except Exception as e:
        return f"Ошибка при генерации графиков: {str(e)}", 500

@app.route('/time')
def time_dashboard():
    """Time tracking dashboard"""
    if time_data is None:
        return redirect(url_for('index'))
    return render_template('time.html')

@app.route('/daily')
def daily_dashboard():
    """Daily data dashboard"""
    if daily_data is None:
        return redirect(url_for('index'))
    return render_template('daily.html')

@app.route('/api/mood')
def mood_api():
    """API endpoint for mood data"""
    if mood_data is None:
        return jsonify({'error': 'No mood data available'}), 400
    
    data = mood_data.data
    return jsonify({
        'dates': [format_date(d) for d in data.index],
        'mood_levels': data['mood_num'].tolist(),
        'stats': {
            'average': float(data['mood_num'].mean()),
            'median': float(data['mood_num'].median()),
            'std': float(data['mood_num'].std())
        }
    })

@app.route('/api/time')
def time_api():
    """API endpoint for time data"""
    if time_data is None:
        return jsonify({'error': 'No time data available'}), 400
    data = time_data.get_data()
    return jsonify({
        'categories': data['categories'].tolist(),
        'durations': data['durations'].tolist(),
        'hours': data['hours'].tolist(),
        'activity': data['activity'].tolist(),
        'stats': {
            'total_time': str(data['durations'].sum()),
            'avg_time': str(data['durations'].mean()),
            'peak_hours': data['hours'][data['activity'].argmax()]
        }
    })

@app.route('/api/daily')
def daily_api():
    """API endpoint for daily data"""
    if daily_data is None:
        return jsonify({'error': 'No daily data available'}), 400
    data = daily_data.get_data()
    return jsonify({
        'dates': [format_date(d) for d in data['dates']],
        'activity_levels': data['activity_levels'].tolist(),
        'stats': {
            'average': float(data['activity_levels'].mean()),
            'peak_days': [format_date(d) for d in data['dates'][data['activity_levels'].nlargest(3).index]],
            'trend': 'растущий' if data['activity_levels'].iloc[-1] > data['activity_levels'].iloc[0] else 'падающий'
        }
    })

if __name__ == '__main__':
    app.run(debug=True) 