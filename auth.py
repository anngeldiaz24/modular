from functools import wraps
import datetime
import re 
from flask import (
    Blueprint, flash, g, render_template, request, url_for, session, redirect, abort
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
        acepto_terminos = request.form.get('acepto_terminos') == 'on'

        db, c = get_db()
        error = None

        if not isinstance(nombre, str) or not nombre or len(nombre) < 3:
            error = 'El nombre es requerido y debe ser una cadena de al menos 3 caracteres.'
        elif not isinstance(apellidos, str) or not apellidos or len(apellidos) < 3:
            error = 'Los apellidos son requeridos y deben ser una cadena de al menos 3 caracteres.'
        elif not isinstance(email, str) or not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            error = 'El email es requerido y debe ser una dirección de correo electrónico válida.'
        elif not isinstance(password, str) or not password or len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password) or not any(char in "!@#$%^&*()-_=+{}[]|;:<>,.?/" for char in password):
            error = 'La contraseña es requerida y debe tener al menos 8 caracteres, incluir números y caracteres especiales.'
        elif not isinstance(confirmar_contrasena, str) or not confirmar_contrasena or len(confirmar_contrasena) < 8:
            error = 'La confirmación de contraseña es requerida.'
        elif password != confirmar_contrasena:
            error = 'Las contraseñas no coinciden.'
        elif not isinstance(telefono, str) or not telefono or len(telefono) > 13:
            error = 'El teléfono es requerido y no puede tener más de 13 dígitos.'
        elif not acepto_terminos or acepto_terminos not in [True, False]:
            error = 'Debes aceptar los Términos y Condiciones.'

        if error is None:
            c.execute('SELECT id FROM users WHERE email = %s', (email,))
            user = c.fetchone()
            if user is not None:
                error = 'Ya existe un correo electrónico registrado. Inicia sesión o recupera tu contraseña.'
            else:
                c.execute('SELECT id FROM codigos_acceso WHERE codigo = %s AND disponible = TRUE', (codigo_acceso,))
                codigo = c.fetchone()
                if codigo is not None:
                    try:
                        hashed_password = generate_password_hash(password)
                        c.execute(
                            'INSERT INTO users (nombre, apellidos, email, password, telefono, rol, codigo_acceso, acepto_terminos, hogar_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                            (nombre, apellidos, email, hashed_password, telefono, rol, codigo['id'], acepto_terminos, None)
                        )
                        c.execute('UPDATE codigos_acceso SET disponible = FALSE WHERE id = %s', (codigo['id'],))
                        db.commit()
                    except MySQLError as e:
                        error = f'Error en la base de datos: {str(e)}'
                    else:
                        flash('¡Cuenta creada exitosamente! Por favor inicia sesión.', 'success')
                        return redirect(url_for('auth.login')) 
    
                else:
                    error = 'El código de acceso no es válido o no está disponible.'

        flash(error, 'error')
        return render_template('auth/register.html', current_year=datetime.datetime.now().year, nombre=nombre, apellidos=apellidos, email=email, telefono=telefono, codigo_acceso=codigo_acceso, acepto_terminos=acepto_terminos)

    return render_template('auth/register.html', current_year=datetime.datetime.now().year)

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
            if user['rol'] == 'Admin':
                return redirect(url_for('admin.admin_index'))
            else:
                return redirect(url_for('user.user_index'))
    
        flash(error, 'error')
    
    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    print(user_id)
    
    if user_id is None:
        g.user = None
    else:
        db, c = get_db()
        c.execute(
            'SELECT * FROM users WHERE id = %s', (user_id,)
        )
        g.user = c.fetchone()

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view

def user_role_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        if g.user['rol'] not in ['User', 'Owner']:
            abort(403)
        return view(**kwargs)
    return wrapped_view

def admin_role_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        if g.user['rol'] != 'Admin':
            abort(403)
        return view(**kwargs)
    return wrapped_view


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

