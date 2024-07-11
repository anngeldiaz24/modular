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
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(user.bp)
    
    @app.route('/graph')
    def graph():
        data = [
            ("01-01-2020", 1597),
            ("02-01-2020", 1456),
            ("03-01-2020", 1908),
            ("04-01-2020", 896),
            ("05-01-2020", 755),
            ("06-01-2020", 453),
            ("07-01-2020", 1100),
            ("08-01-2020", 1235),
            ("09-01-2020", 1478),
        ]
        
        labels = [row[0] for row in data]
        values = [row[1] for row in data]
        
        return render_template("user-domotica.html", labels=labels, values=values, user=g.user)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    @app.route('/home')
    def home():
        return render_template('home.html', user=g.user)
    
    @app.route('/user-domotica')
    def user_domotica():
        db, c = get_db()
        
        print(g.user)
        
        hogar_id = g.user['hogar_id']
        
        query = """
        SELECT e.nombre, COUNT(r.id) as total
        FROM registros_eventos r
        JOIN eventos e ON r.evento_id = e.id
        WHERE r.hogar_id = %s
        GROUP BY e.nombre
        """
        
        # Ejecutar la consulta y obtener los resultados
        c.execute(query, (hogar_id,))
        data = c.fetchall()
        
        labels = [row['nombre'] for row in data]
        values = [row['total'] for row in data]
        return render_template('user-domotica.html', user=g.user, labels=labels, values=values)
    
    
    # Manejador de error 404 [Rutas no definidas]
    @app.errorhandler(404)
    def pagina_no_encontrada(error):
        return render_template('404.html', user=g.user), 404

    return app
