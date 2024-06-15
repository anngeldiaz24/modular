from flask import Flask, render_template, redirect, url_for
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
    
    from . import auth
    
    app.register_blueprint(auth.bp)

    @app.route('/admin-dashboard')
    def admin_dashboard():
        return render_template('admin-dashboard.html')
    
    @app.route('/user-dashboard')
    def user_dashboard():
        return render_template('user-dashboard.html')

    @app.route('/home')
    def home():
        return render_template('home.html')
    
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app