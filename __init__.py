from flask import Flask, render_template, redirect, url_for, jsonify, g
import os
import json
from . import db
from .raspberry import funciones
from .raspberry import llamada_policia
from .db import get_db


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
    from . import admin
    from . import user
    from . import domotica
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(domotica.bp)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    # Manejador de error 404 [Rutas no definidas]
    @app.errorhandler(404)
    def pagina_no_encontrada(error):
        return render_template('errors/404.html', user=g.user), 404
    
    # Manejador de error 403 [Accion no autorizada]
    @app.errorhandler(403)
    def accion_no_autorizada(error):
        return render_template('errors/403.html', user=g.user), 403


    return app
