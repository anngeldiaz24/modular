from flask import Flask, render_template
import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('admin-dashboard.html')

@app.route('/register')
def register():
    current_year = datetime.datetime.now().year
    return render_template('auth/register.html', current_year=current_year)
