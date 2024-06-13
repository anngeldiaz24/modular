from flask import Flask, render_template
import datetime
import os
from . import db

def create_app():
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY='Cucei_Udg',
        DATABASE_HOST=os.environ.get('FLASK_DATABASE_HOST'),
        DATABASE_PASSWORD=os.environ.get('FLASK_DATABASE_PASSWORD'),
        DATABASE_USER=os.environ.get('FLASK_DATABASE_USER'),
        DATABASE=os.environ.get('FLASK_DATABASE'),
        DATABASE_PORT=os.environ.get('FLASK_PORT'),
    )

    db.init_app(app)

    @app.route('/admin-dashboard')
    def admin_dashboard():
        return render_template('admin-dashboard.html')

    @app.route('/')
    def index():
        return render_template('auth/login.html')

    @app.route('/register')
    def register():
        current_year = datetime.datetime.now().year
        return render_template('auth/register.html', current_year=current_year)

    return app
