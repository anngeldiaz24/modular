import functools
import datetime
from flask import (
    Blueprint, flash, g, render_template, request, url_for, session, redirect
)

from mysql.connector import Error as MySQLError
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellidos = request.form['apellidos']
        email = request.form['email']
        password = request.form['password']
        confirmar_contrasena = request.form['confirmar_contrasena']
        telefono = request.form['telefono']
        rol = 'Owner'
        codigo_acceso = request.form['codigo_acceso']

        db, c = get_db()
        error = None

        if not nombre:
            error = 'Nombre es requerido.'
        elif not apellidos:
            error = 'Apellido es requerido.'
        elif not email:
            error = 'Email es requerido.'
        elif not password:
            error = 'Contraseña es requerida.'
        elif not telefono:
            error = 'Teléfono es requerido.'
        elif password != confirmar_contrasena:
            error = 'Las contraseñas no coinciden.'

        if error is None:
            c.execute('SELECT id FROM users WHERE email = %s', (email,))
            user = c.fetchone()
            if user is not None:
                error = 'Ya existe un correo electrónico registrado. Inicia sesión o recupera tu contraseña.'
            else:
                try:
                    hashed_password = generate_password_hash(password)
                    c.execute(
                        'INSERT INTO users (nombre, apellidos, email, password, telefono, rol, codigo_acceso) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (nombre, apellidos, email, hashed_password, telefono, rol, codigo_acceso)
                    )
                    db.commit()
                except MySQLError as e:
                    error = f'Error en la base de datos: {str(e)}'
                else:
                    return redirect(url_for('auth.login'))

        flash(error)

    current_year = datetime.datetime.now().year
    return render_template('auth/register.html', current_year=current_year)

@bp.route('/login', methods=['GET', 'POST']) 
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        db, c = get_db()
        error = None
        c.execute(
            'SELECT * FROM users WHERE email = %s', (email,)
        )
        user = c.fetchone()
        
        if user is None:
            error = 'Email o contraseña inválidas.'
            print('Usuario no existe')
        elif not check_password_hash(user['password'], password):
            error = 'Email o contraseña inválidas.'
            print(user['password'])
            print(password)
            
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('user_dashboard')) 
    
        flash(error)
    
    return render_template('auth/login.html')