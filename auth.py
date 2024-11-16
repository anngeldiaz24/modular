from functools import wraps
from flask import Flask, current_app
import smtplib 
from email.mime.text import MIMEText
import datetime
import re 
import os
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask import (
    Blueprint, flash, g, render_template, request, url_for, session, redirect, abort, jsonify, Response
)

from mysql.connector import Error as MySQLError
from werkzeug.security import check_password_hash, generate_password_hash
import cv2

from .db import get_db, close_db

bp = Blueprint('auth', __name__, url_prefix='/auth')
# Cargar las variables desde el archivo .env
load_dotenv()

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
        
        # Consulta para obtener los detalles del usuario y su hogar
        c.execute("""
            SELECT u.*, h.estatus
            FROM users u
            LEFT JOIN hogares h ON u.hogar_id = h.id
            WHERE u.email = %s
        """, (email,))
        user = c.fetchone()
        
        if user is None:
            error = 'Email o contraseña inválidas.'
        elif not check_password_hash(user['password'], password):
            error = 'Email o contraseña inválidas.'
        elif user['estatus'] == 'cancelado':
            error = 'Tu cuenta ha sido cancelada, para más información contacte a soporte: safezonesamsung@gmail.com'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            if user['rol'] == 'Admin':
                return redirect(url_for('admin.admin_index'))
            else:
                if user['hogar_id'] is None:
                    return redirect(url_for('user.user_welcome'))
                else:
                    flash(f'¡Bienvenido, {user["nombre"]}!', 'success')
                    return redirect(url_for('user.home'))
    
        flash(error, 'error')
    
    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    
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

@bp.route('/recuperar-contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    db, c = get_db()
    
    if request.method == 'POST':
        correo = request.form['correo_electronico']
        
        error = None

        # Validar el formato del correo electrónico
        if not isinstance(correo, str) or not correo or not re.match(r"[^@]+@[^@]+\.[^@]+", correo):
            error = 'El correo es requerido y debe ser válido.'
        
        # Verificar si el correo electrónico está registrado en la base de datos
        if error is None:
            c.execute('SELECT id FROM users WHERE email = %s', (correo,))
            user = c.fetchone()
            if user is None:
                error = 'El correo no está registrado.'
            else:
                user_id = user['id']
                # Enviar correo electrónico
                try:
                    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
                    token = serializer.dumps(user_id, salt='password-reset-salt')
                    
                    # Crear la URL de restablecimiento de contraseña
                    reset_url = url_for('auth.reestablecer_contrasena', token=token, _external=True)
                    
                    # Renderizar el contenido del correo electrónico usando la plantilla
                    html_content = render_template('email/email-recuperar-password.html', reset_url=reset_url)
                    
                    msg = MIMEText(html_content, "html")
                    msg["From"] = "safezonesamsung@gmail.com"
                    msg["To"] = correo
                    msg["Subject"] = "Reestablecer contraseña"
                    
                    servidor = smtplib.SMTP("smtp.gmail.com", 587)
                    servidor.starttls()
                    servidor.login("safezonesamsung@gmail.com", "mobn gykt qtwp vnob")
                    servidor.sendmail("safezonesamsung@gmail.com", correo, msg.as_string())
                    servidor.quit()
                    
                    flash('Se ha enviado un correo electrónico con instrucciones para reestablecer tu contraseña.', 'success')
                except Exception as e:
                    error = f'Error enviando el correo: {str(e)}'

        if error:
            flash(error, 'error')
        else:
            return redirect(url_for('auth.recuperar_contrasena'))

    return render_template('auth/recuperar-contrasena.html', current_year=datetime.datetime.now().year)

@bp.route('/reestablecer-contrasena', methods=['GET', 'POST'])
def reestablecer_contrasena():
    token = request.args.get('token')
    if not token:
        flash('El token es requerido.', 'error')
        return redirect(url_for('auth.recuperar_contrasena'))

    try:
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        user_id = serializer.loads(token, salt='password-reset-salt', max_age=300)  # Token válido por 5 minutos
    except (SignatureExpired, BadSignature):
        flash('El enlace de restablecimiento de contraseña es inválido o ha expirado.', 'error')
        return redirect(url_for('auth.recuperar_contrasena'))

    if request.method == 'POST':
        password = request.form['password']
        confirmar_contrasena = request.form['confirm_password']
        
        db, c = get_db()
        error = None
        
        # Validar la contraseña
        if not isinstance(password, str) or not password or len(password) < 8 or \
            not any(char.isdigit() for char in password) or \
            not any(char.isalpha() for char in password) or \
            not any(char in "!@#$%^&*()-_=+{}[]|;:<>,.?/" for char in password):
                error = 'La contraseña es requerida y debe tener al menos 8 caracteres, incluir números y caracteres especiales.'
        elif not isinstance(confirmar_contrasena, str) or not confirmar_contrasena or len(confirmar_contrasena) < 8:
            error = 'La confirmación de contraseña es requerida.'
        elif password != confirmar_contrasena:
            error = 'Las contraseñas no coinciden.'
        
        if error is None:
            try:
                hashed_password = generate_password_hash(password)
                
                c.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_password, user_id))
                db.commit()
                
                flash('Tu contraseña ha sido reestablecida con éxito.', 'success')
                return redirect(url_for('auth.login')) 
            except Exception as e:
                error = f'Error actualizando la contraseña: {str(e)}'
        
        if error:
            flash(error, 'error')
    
    return render_template('auth/reestablecer-contrasena.html', current_year=datetime.datetime.now().year)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@bp.route('/buscar-correo-electronico', methods=['POST'])
def buscar_correo_electronico():
    db, c = get_db()
    try:
        # Obtener el correo del formulario
        correo_electronico = request.json.get('correoElectronico')

        # Buscar el correo en la base de datos
        query = "SELECT * FROM users WHERE email = %s"
        c.execute(query, (correo_electronico,))
        usuario = c.fetchone()
        
        if usuario:
            # Si el usuario existe, puedes redirigir o abrir otro modal
            return jsonify({'existe': True})
        else:
            # Si el usuario no existe, devolver un mensaje de error
            return jsonify({'existe': False, 'error': 'No se encontró un usuario con este correo electrónico.'})
    except Exception as e:
        # Manejar errores y devolver un mensaje de error genérico
        print(f"Error al buscar el correo: {e}")
        return jsonify({'existe': False, 'error': 'Hubo un problema al procesar tu solicitud. Inténtalo de nuevo más tarde.'}), 500
    
    finally:
        close_db()
        
def cargar_modelo_y_datos():
    # Ruta de los modelos y datos
    PATH = os.getenv('DATA_PATH')
    dataPath = os.path.join(PATH, 'Data')
    model_path = os.path.join(PATH, 'Data', 'Modelo', 'modeloLBPHFace.xml')

    # Cargar el modelo de reconocimiento facial
    face_recognizer = cv2.face.LBPHFaceRecognizer_create()
    face_recognizer.read(model_path)

    # Cargar el clasificador de rostros
    faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Mapeo de etiquetas a nombres de usuario
    user_dict = {}
    label = 0
    for hogar_id in os.listdir(dataPath):
        hogar_path = os.path.join(dataPath, hogar_id)
        if os.path.isdir(hogar_path):
            for usuario in os.listdir(hogar_path):
                user_dict[label] = usuario
                label += 1
    
    return face_recognizer, faceClassif, user_dict


def reconocer_rostro_en_video(video_path):
    # Cargar el modelo y los datos
    face_recognizer, faceClassif, user_dict = cargar_modelo_y_datos()

    # Captura de video (puede ser desde cámara o un archivo de video)
    cap = cv2.VideoCapture(video_path)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        auxFrame = gray.copy()

        # Detectar rostros en el frame
        faces = faceClassif.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            rostro = auxFrame[y:y + h, x:x + w]
            rostro = cv2.resize(rostro, (150, 150), interpolation=cv2.INTER_CUBIC)
            result = face_recognizer.predict(rostro)

            # Verificar si el rostro pertenece a alguien conocido
            if result[1] < 72:  # Ajusta el umbral según tu modelo
                user_name = user_dict.get(result[0], "Desconocido")
                cap.release()  # Liberar el video
                return user_name  # Retornar el nombre del usuario reconocido
            else:
                continue

    cap.release()
    return None  # Si no se reconoce ningún rostro


@bp.route('/login-faceid', methods=['POST'])
def login_faceid():
    import time
    if 'video' not in request.files:
        return jsonify({'message': 'No se recibió ningún video.'}), 400

    video_file = request.files['video']
    email = request.form['correoElectronico']  # El email se recibe desde el formulario
    
    # Define la ruta raíz del proyecto
    root_path = os.path.dirname(os.path.abspath(__file__))
    # Ruta de la carpeta donde se guardará el video en la raíz del proyecto
    dir_path = os.path.join(root_path, 'static', 'videos')

    # Crear la carpeta 'videos' si no existe
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Generar un nombre temporal basado en la marca de tiempo
    temp_filename = f'temp_{int(time.time())}.webm'

    # Ruta completa del archivo
    webm_path = os.path.join(dir_path, temp_filename)

    # Guardar el video con el nombre temporal
    video_file.save(webm_path)
    
    # Reconocer el rostro en el video guardado
    recognized_user = reconocer_rostro_en_video(webm_path)
    print(recognized_user)
    
    # Si el usuario es reconocido
    if recognized_user:
        try:
            # Eliminar el archivo temporal
            os.remove(webm_path)
            
            # Conectar a la base de datos
            db, c = get_db()
            error = None
            
            # Consulta para obtener los detalles del usuario y su hogar
            c.execute("""
                SELECT u.*, h.estatus
                FROM users u
                LEFT JOIN hogares h ON u.hogar_id = h.id
                WHERE u.email = %s
            """, (email,))
            user = c.fetchone()
            
            if user is None:
                return jsonify({'message': 'Usuario no encontrado.'}), 404

            # Limpiar sesión y establecer user_id
            session.clear()
            session['user_id'] = user['id']
            
            # Retornar la información del usuario y redirigir según su rol o estado del hogar
            flash(f'¡Bienvenido, {user["nombre"]}!', 'success')
            return jsonify({'redirect_url': url_for('user.home')}), 200

        except OSError as e:
            print(f"Error al eliminar el archivo: {e}")
            return jsonify({'message': 'Error al procesar el video.'}), 500
    
    # Si el usuario no es reconocido, eliminar el archivo y devolver error
    try:
        os.remove(webm_path)
        print("Video temporal eliminado debido a fallo en el reconocimiento.")
    except OSError as e:
        print(f"Error al eliminar el archivo: {e}")

    return jsonify({'message': 'Rostro no reconocido, video eliminado.'}), 400
