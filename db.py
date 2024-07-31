import mysql.connector
import os

#Ejecutar comandos en la terminal
import click
import calendar
import random
from datetime import datetime, timedelta
#Current mantiene la aplicacion que se ejecuta y 
#con g podemos acceder a variables e ir asignandolas a distintas cosas
from flask import current_app, g
#Nos sirve para ejecutar el script de la base de datos (host, base de datos, password)
from flask.cli import with_appcontext

from .schema import instructions
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv # para cargar las variables del .env

def generate_periodos():
    start_year = 2023
    end_year = 2024
    end_month = 7
    periodos = []

    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            if year == end_year and month > end_month:
                break
            nombre = f'{calendar.month_name[month]} {year}'
            inicio = datetime(year, month, 1).strftime('%Y-%m-%d')
            fin = (datetime(year, month, 1) + timedelta(days=calendar.monthrange(year, month)[1] - 1)).strftime('%Y-%m-%d')
            periodos.append({'nombre': nombre, 'inicio': inicio, 'fin': fin})

    return periodos

def init_app(app):
    # Carga las variables de entorno desde el archivo .env
    load_dotenv()
    
    #ejecuta funciones que nosotros le pasamos como argumento
    #Cerramos la conexión a la BD
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(drop_tables_command)
    app.cli.add_command(seed_database_command)
    app.cli.add_command(seed_registros_eventos_command)
    
    # Configuración de la base de datos
    app.config['DATABASE_HOST'] = os.getenv('DATABASE_HOST')
    app.config['DATABASE_USER'] = os.getenv('DATABASE_USER')
    app.config['DATABASE_PASSWORD'] = os.getenv('DATABASE_PASSWORD')
    app.config['DATABASE'] = os.getenv('DATABASE')
    app.config['DATABASE_PORT'] = os.getenv('DATABASE_PORT')

def get_db():
    
    #Si ni se encuentra el atributo db dentro de g
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host=current_app.config['DATABASE_HOST'],
            user=current_app.config['DATABASE_USER'],
            password=current_app.config['DATABASE_PASSWORD'],
            database=current_app.config['DATABASE'],
            port=current_app.config['DATABASE_PORT']
        )
        g.c = g.db.cursor(dictionary=True)
    #retornamos la bd y el cursor 
    return g.db, g.c

def close_db(e = None):
    #Le quitamos la propiedad de la base de datos a g
    db = g.pop('DB', None)

    if db is not None:
        #Se cierra
        db.close()
        
def init_db():
    try:
        db, c = get_db()

        # Como sql solo deja ejecutar un comando a la vez
        # ejecutamos e iteramos las instrucciones con un for
        for i in instructions:
            c.execute(i)
            c.fetchall()  # Consumir los resultados de la consulta
        # Se ejecutan   
        db.commit()
    except Exception as e:
        click.echo(f'Error al inicializar la base de datos: {str(e)}')
        return

@click.command('init-db')
@with_appcontext

def init_db_command():
    init_db()
    click.echo('Base de datos inicializada')
        
def drop_tables():
    db, c = get_db()
    
    # Obtener el nombre de todas las tablas
    c.execute("SHOW TABLES")
    tables = c.fetchall()
    
    try:
        # Deshabilitar las restricciones de clave externa temporalmente
        c.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        # Dropear cada tabla
        for table in tables:
            table_name = table['Tables_in_' + current_app.config['DATABASE']]
            c.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # Volver a habilitar las restricciones de clave externa
        c.execute("SET FOREIGN_KEY_CHECKS = 1;")
        
        db.commit()
    except Exception as e:
        click.echo(f'Error al dropear las tablas: {str(e)}')
        return

@click.command('drop-tables')
@with_appcontext
def drop_tables_command():
    drop_tables()
    click.echo('Todas las tablas han sido dropeadas')
    
def seed_database():
    # Definición del número de miembros por hogar
    miembros_por_hogar = {
        1: 3,  # Hogar 1 tiene 3 miembros
        2: 5,  # Hogar 2 tiene 5 miembros
        3: 1,  # Hogar 3 tiene 1 miembro
        4: 3,  # Hogar 4 tiene 3 miembros
        5: 2   # Hogar 5 tiene 2 miembros
    }
    
    # Definir tipos de dispositivo y posibles estados
    tipos_dispositivo = ['celular', 'computadora', 'tablet']
    estados_dispositivo = ['conectado', 'desconectado']
    
    # Distribución de usuario_id y hogar_id como se proporcionó
    usuarios_por_hogar = {
        1: [2, 3, 4],
        2: [5, 6, 7, 8, 9],
        3: [10],
        4: [11, 12, 13],
        5: [14, 15]
    }
    
    # Obtiene la conexión a la base de datos y el cursor
    db, c = get_db()

    codigos = [
        {'codigo': 'CODE-1AB', 'paquete': 'Básico', 'disponible': False},
        {'codigo': 'CODE-2BC', 'paquete': 'Básico', 'disponible': False},
        {'codigo': 'CODE-3CD', 'paquete': 'Premium', 'disponible': False},
        {'codigo': 'CODE-4DE', 'paquete': 'Premium', 'disponible': False},
        {'codigo': 'CODE-5EF', 'paquete': 'Deluxe', 'disponible': False},
        {'codigo': 'CODE-6FG', 'paquete': 'Deluxe', 'disponible': True},
        {'codigo': 'CODE-7GH', 'paquete': 'Básico', 'disponible': True},
        {'codigo': 'CODE-8HI', 'paquete': 'Premium', 'disponible': True},
        {'codigo': 'CODE-9IJ', 'paquete': 'Deluxe', 'disponible': True},
        {'codigo': 'CODE-0JK', 'paquete': 'Básico', 'disponible': True}
    ]

    estados = [
        'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 
        'Coahuila', 'Colima', 'Durango', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Estado de México', 
        'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 
        'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 
        'Zacatecas'
    ]

    usuarios = [
        {'nombre': 'Juan', 'apellidos': 'Pérez', 'email': 'juan.perez@example.com', 'password': generate_password_hash('password'), 'telefono': '1234567890', 'rol': 'Admin', 'codigo_acceso': None, 'acepto_terminos': True, 'hogar_id': None},
        {'nombre': 'Ana', 'apellidos': 'García', 'email': 'ana.garcia@example.com', 'password': generate_password_hash('password'), 'telefono': '0987654321', 'rol': 'Owner', 'codigo_acceso': 1, 'acepto_terminos': True, 'hogar_id':1},
        {'nombre': 'Luis', 'apellidos': 'Martínez', 'email': 'luis.martinez@example.com', 'password': generate_password_hash('password'), 'telefono': '1122334455', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True, 'hogar_id':1},
        {'nombre': 'Carlos', 'apellidos': 'Hernández', 'email': 'carlos.hernandez@example.com', 'password': generate_password_hash('password'), 'telefono': '5566778899', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True, 'hogar_id':1},
        {'nombre': 'María', 'apellidos': 'López', 'email': 'maria.lopez@example.com', 'password': generate_password_hash('password'), 'telefono': '6677889900', 'rol': 'Owner', 'codigo_acceso': 2, 'acepto_terminos': True,'hogar_id':2},
        {'nombre': 'Miguel', 'apellidos': 'Rodríguez', 'email': 'miguel.rodriguez@example.com', 'password': generate_password_hash('password'), 'telefono': '7788990011', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True,'hogar_id':2},
        {'nombre': 'Laura', 'apellidos': 'Gómez', 'email': 'laura.gomez@example.com', 'password': generate_password_hash('password'), 'telefono': '8899001122', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True,'hogar_id':2},
        {'nombre': 'David', 'apellidos': 'Díaz', 'email': 'david.diaz@example.com', 'password': generate_password_hash('password'), 'telefono': '9900112233', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True,'hogar_id':2},
        {'nombre': 'Sofía', 'apellidos': 'Fernández', 'email': 'sofia.fernandez@example.com', 'password': generate_password_hash('password'), 'telefono': '0011223344', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True,'hogar_id':2},
        {'nombre': 'Jorge', 'apellidos': 'Morales', 'email': 'jorge.morales@example.com', 'password': generate_password_hash('password'), 'telefono': '1122334455', 'rol': 'Owner', 'codigo_acceso': 3, 'acepto_terminos': True,'hogar_id':3},
        {'nombre': 'Patricia', 'apellidos': 'Ramírez', 'email': 'patricia.ramirez@example.com', 'password': generate_password_hash('password'), 'telefono': '2233445566', 'rol': 'Owner', 'codigo_acceso': 4, 'acepto_terminos': True,'hogar_id':4},
        {'nombre': 'Manuel', 'apellidos': 'Cruz', 'email': 'manuel.cruz@example.com', 'password': generate_password_hash('password'), 'telefono': '3344556677', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True,'hogar_id':4},
        {'nombre': 'Gabriela', 'apellidos': 'Sánchez', 'email': 'gabriela.sanchez@example.com', 'password': generate_password_hash('password'), 'telefono': '4455667788', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True,'hogar_id':4},
        {'nombre': 'Fernando', 'apellidos': 'Ortiz', 'email': 'fernando.ortiz@example.com', 'password': generate_password_hash('password'), 'telefono': '5566778899', 'rol': 'Owner', 'codigo_acceso': 5, 'acepto_terminos': True,'hogar_id':5},
        {'nombre': 'Elena', 'apellidos': 'Vargas', 'email': 'elena.vargas@example.com', 'password': generate_password_hash('password'), 'telefono': '6677889900', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True, 'hogar_id':5}
    ]

    hogares = [
        {'codigo_postal': '01000', 'calle': 'Calle Falsa', 'numero_exterior': '123', 'numero_interior': 'A', 'colonia': 'Centro', 'municipio': 'Ciudad de México', 'estado': 'Ciudad de México', 'informacion_adicional': 'Cerca del parque', 'estatus': 'activo'},
        {'codigo_postal': '02000', 'calle': 'Avenida Siempre Viva', 'numero_exterior': '742', 'numero_interior': '', 'colonia': 'Primavera', 'municipio': 'Monterrey', 'estado': 'Nuevo León', 'informacion_adicional': '', 'estatus': 'activo'},
        {'codigo_postal': '03000', 'calle': 'Callejón sin Salida', 'numero_exterior': '666', 'numero_interior': 'B', 'colonia': 'Fantasma', 'municipio': 'Guadalajara', 'estado': 'Jalisco', 'informacion_adicional': 'Al lado del cementerio', 'estatus': 'activo'},
        {'codigo_postal': '04000', 'calle': 'Camino Real', 'numero_exterior': '789', 'numero_interior': '', 'colonia': 'San Juan', 'municipio': 'Puebla', 'estado': 'Puebla', 'informacion_adicional': '', 'estatus': 'activo'},
        {'codigo_postal': '05000', 'calle': 'Av. Revolución', 'numero_exterior': '101', 'numero_interior': 'C', 'colonia': 'Las Flores', 'municipio': 'Querétaro', 'estado': 'Querétaro', 'informacion_adicional': 'Frente a la plaza', 'estatus': 'activo'}
    ]
    
    eventos = [
        {'nombre': 'activacion_alarma'},
        {'nombre': 'desactivacion_alarma'},
        {'nombre': 'encendido_luces'},
        {'nombre': 'apagado_luces'},
        {'nombre': 'bloqueo_puerta'},
        {'nombre': 'desbloqueo_puerta'},
        {'nombre': 'monitoreo_camara'},
        {'nombre': 'alerta'},
        {'nombre': 'modo_seguro'}
    ]
    
    periodos = generate_periodos()
    
    registros_eventos = [
        {'hogar_id': 1, 'usuario_id': 2, 'evento_id': 9, 'periodo_id': 1},
        {'hogar_id': 1, 'usuario_id': 3, 'evento_id': 9, 'periodo_id': 1},
        {'hogar_id': 1, 'usuario_id': 4, 'evento_id': 9, 'periodo_id': 1},
        {'hogar_id': 1, 'usuario_id': 2, 'evento_id': 9, 'periodo_id': 2},
        {'hogar_id': 1, 'usuario_id': 3, 'evento_id': 9, 'periodo_id': 2},
        {'hogar_id': 1, 'usuario_id': 4, 'evento_id': 9, 'periodo_id': 2},
        {'hogar_id': 1, 'usuario_id': 2, 'evento_id': 9, 'periodo_id': 3},
        {'hogar_id': 1, 'usuario_id': 3, 'evento_id': 9, 'periodo_id': 3},
        {'hogar_id': 1, 'usuario_id': 4, 'evento_id': 9, 'periodo_id': 3},
        {'hogar_id': 1, 'usuario_id': 2, 'evento_id': 9, 'periodo_id': 4},
        {'hogar_id': 1, 'usuario_id': 3, 'evento_id': 9, 'periodo_id': 4},
        {'hogar_id': 1, 'usuario_id': 4, 'evento_id': 9, 'periodo_id': 4},
        {'hogar_id': 1, 'usuario_id': 2, 'evento_id': 9, 'periodo_id': 5},
        {'hogar_id': 1, 'usuario_id': 3, 'evento_id': 9, 'periodo_id': 5},
        {'hogar_id': 1, 'usuario_id': 4, 'evento_id': 9, 'periodo_id': 5},
        {'hogar_id': 1, 'usuario_id': 2, 'evento_id': 9, 'periodo_id': 6},
        {'hogar_id': 1, 'usuario_id': 3, 'evento_id': 9, 'periodo_id': 6},
        {'hogar_id': 1, 'usuario_id': 4, 'evento_id': 9, 'periodo_id': 6},
        {'hogar_id': 1, 'usuario_id': 2, 'evento_id': 9, 'periodo_id': 13},
        {'hogar_id': 1, 'usuario_id': 3, 'evento_id': 9, 'periodo_id': 13},
        {'hogar_id': 1, 'usuario_id': 4, 'evento_id': 9, 'periodo_id': 14},
        {'hogar_id': 1, 'usuario_id': 2, 'evento_id': 9, 'periodo_id': 14},
        {'hogar_id': 1, 'usuario_id': 3, 'evento_id': 9, 'periodo_id': 15},
        {'hogar_id': 1, 'usuario_id': 4, 'evento_id': 9, 'periodo_id': 15},
        {'hogar_id': 1, 'usuario_id': 2, 'evento_id': 9, 'periodo_id': 16},
        {'hogar_id': 1, 'usuario_id': 3, 'evento_id': 9, 'periodo_id': 16},
        {'hogar_id': 1, 'usuario_id': 4, 'evento_id': 9, 'periodo_id': 17},
        {'hogar_id': 1, 'usuario_id': 2, 'evento_id': 9, 'periodo_id': 17},
        {'hogar_id': 1, 'usuario_id': 3, 'evento_id': 9, 'periodo_id': 18},
        {'hogar_id': 1, 'usuario_id': 4, 'evento_id': 9, 'periodo_id': 18},
        {'hogar_id': 2, 'usuario_id': 5, 'evento_id': 9, 'periodo_id': 7},
        {'hogar_id': 2, 'usuario_id': 6, 'evento_id': 9, 'periodo_id': 7},
        {'hogar_id': 2, 'usuario_id': 7, 'evento_id': 9, 'periodo_id': 7},
        {'hogar_id': 2, 'usuario_id': 8, 'evento_id': 9, 'periodo_id': 8},
        {'hogar_id': 2, 'usuario_id': 9, 'evento_id': 9, 'periodo_id': 8},
        {'hogar_id': 2, 'usuario_id': 5, 'evento_id': 9, 'periodo_id': 8},
        {'hogar_id': 2, 'usuario_id': 6, 'evento_id': 9, 'periodo_id': 9},
        {'hogar_id': 2, 'usuario_id': 7, 'evento_id': 9, 'periodo_id': 9},
        {'hogar_id': 2, 'usuario_id': 8, 'evento_id': 9, 'periodo_id': 9},
        {'hogar_id': 2, 'usuario_id': 9, 'evento_id': 9, 'periodo_id': 9},
        {'hogar_id': 2, 'usuario_id': 5, 'evento_id': 9, 'periodo_id': 10},
        {'hogar_id': 2, 'usuario_id': 6, 'evento_id': 9, 'periodo_id': 10},
        {'hogar_id': 2, 'usuario_id': 7, 'evento_id': 9, 'periodo_id': 10},
        {'hogar_id': 2, 'usuario_id': 8, 'evento_id': 9, 'periodo_id': 11},
        {'hogar_id': 2, 'usuario_id': 9, 'evento_id': 9, 'periodo_id': 11},
        {'hogar_id': 2, 'usuario_id': 5, 'evento_id': 9, 'periodo_id': 11},
        {'hogar_id': 2, 'usuario_id': 6, 'evento_id': 9, 'periodo_id': 12},
        {'hogar_id': 2, 'usuario_id': 7, 'evento_id': 9, 'periodo_id': 12},
        {'hogar_id': 2, 'usuario_id': 8, 'evento_id': 9, 'periodo_id': 12},
        {'hogar_id': 2, 'usuario_id': 9, 'evento_id': 9, 'periodo_id': 12},
        {'hogar_id': 2, 'usuario_id': 5, 'evento_id': 9, 'periodo_id': 13},
        {'hogar_id': 2, 'usuario_id': 6, 'evento_id': 9, 'periodo_id': 13},
        {'hogar_id': 2, 'usuario_id': 7, 'evento_id': 9, 'periodo_id': 14},
        {'hogar_id': 2, 'usuario_id': 8, 'evento_id': 9, 'periodo_id': 14},
        {'hogar_id': 2, 'usuario_id': 9, 'evento_id': 9, 'periodo_id': 15},
        {'hogar_id': 2, 'usuario_id': 5, 'evento_id': 9, 'periodo_id': 15},
        {'hogar_id': 2, 'usuario_id': 6, 'evento_id': 9, 'periodo_id': 16},
        {'hogar_id': 2, 'usuario_id': 7, 'evento_id': 9, 'periodo_id': 16},
        {'hogar_id': 2, 'usuario_id': 8, 'evento_id': 9, 'periodo_id': 16},
        {'hogar_id': 2, 'usuario_id': 9, 'evento_id': 9, 'periodo_id': 17},
        {'hogar_id': 2, 'usuario_id': 5, 'evento_id': 9, 'periodo_id': 17},
        {'hogar_id': 2, 'usuario_id': 6, 'evento_id': 9, 'periodo_id': 17},
        {'hogar_id': 2, 'usuario_id': 7, 'evento_id': 9, 'periodo_id': 18},
        {'hogar_id': 2, 'usuario_id': 8, 'evento_id': 9, 'periodo_id': 18},
        {'hogar_id': 2, 'usuario_id': 9, 'evento_id': 9, 'periodo_id': 18},
        {'hogar_id': 2, 'usuario_id': 5, 'evento_id': 9, 'periodo_id': 19},
        {'hogar_id': 2, 'usuario_id': 6, 'evento_id': 9, 'periodo_id': 19},
        {'hogar_id': 2, 'usuario_id': 7, 'evento_id': 9, 'periodo_id': 19},
        {'hogar_id': 2, 'usuario_id': 8, 'evento_id': 9, 'periodo_id': 19},
        {'hogar_id': 2, 'usuario_id': 9, 'evento_id': 9, 'periodo_id': 19},
        {'hogar_id': 3, 'usuario_id': 10, 'evento_id': 9, 'periodo_id': 5},
        {'hogar_id': 3, 'usuario_id': 10, 'evento_id': 9, 'periodo_id': 6},
        {'hogar_id': 3, 'usuario_id': 10, 'evento_id': 9, 'periodo_id': 7},
        {'hogar_id': 3, 'usuario_id': 10, 'evento_id': 9, 'periodo_id': 7},
        {'hogar_id': 3, 'usuario_id': 10, 'evento_id': 9, 'periodo_id': 7},
        {'hogar_id': 3, 'usuario_id': 10, 'evento_id': 9, 'periodo_id': 8},
        {'hogar_id': 3, 'usuario_id': 10, 'evento_id': 9, 'periodo_id': 9},
        {'hogar_id': 3, 'usuario_id': 10, 'evento_id': 9, 'periodo_id': 9},
        {'hogar_id': 3, 'usuario_id': 10, 'evento_id': 9, 'periodo_id': 10},
        {'hogar_id': 3, 'usuario_id': 10, 'evento_id': 9, 'periodo_id': 10},
        {'hogar_id': 3, 'usuario_id': 10, 'evento_id': 9, 'periodo_id': 10},
        {'hogar_id': 3, 'usuario_id': 10, 'evento_id': 9, 'periodo_id': 11},
        {'hogar_id': 4, 'usuario_id': 11, 'evento_id': 9, 'periodo_id': 7},
        {'hogar_id': 4, 'usuario_id': 12, 'evento_id': 9, 'periodo_id': 7},
        {'hogar_id': 4, 'usuario_id': 13, 'evento_id': 9, 'periodo_id': 7},
        {'hogar_id': 4, 'usuario_id': 11, 'evento_id': 9, 'periodo_id': 8},
        {'hogar_id': 4, 'usuario_id': 12, 'evento_id': 9, 'periodo_id': 8},
        {'hogar_id': 4, 'usuario_id': 11, 'evento_id': 9, 'periodo_id': 12},
        {'hogar_id': 4, 'usuario_id': 12, 'evento_id': 9, 'periodo_id': 12},
        {'hogar_id': 4, 'usuario_id': 13, 'evento_id': 9, 'periodo_id': 12},
        {'hogar_id': 4, 'usuario_id': 11, 'evento_id': 9, 'periodo_id': 13},
        {'hogar_id': 4, 'usuario_id': 12, 'evento_id': 9, 'periodo_id': 13},
        {'hogar_id': 4, 'usuario_id': 13, 'evento_id': 9, 'periodo_id': 13},
        {'hogar_id': 4, 'usuario_id': 13, 'evento_id': 9, 'periodo_id': 14},
        {'hogar_id': 4, 'usuario_id': 11, 'evento_id': 9, 'periodo_id': 14},
        {'hogar_id': 4, 'usuario_id': 12, 'evento_id': 9, 'periodo_id': 15},
        {'hogar_id': 4, 'usuario_id': 13, 'evento_id': 9, 'periodo_id': 15},
        {'hogar_id': 5, 'usuario_id': 14, 'evento_id': 9, 'periodo_id': 9},
        {'hogar_id': 5, 'usuario_id': 15, 'evento_id': 9, 'periodo_id': 9},
        {'hogar_id': 5, 'usuario_id': 14, 'evento_id': 9, 'periodo_id': 10},
        {'hogar_id': 5, 'usuario_id': 15, 'evento_id': 9, 'periodo_id': 10},
        {'hogar_id': 5, 'usuario_id': 14, 'evento_id': 9, 'periodo_id': 11},
        {'hogar_id': 5, 'usuario_id': 15, 'evento_id': 9, 'periodo_id': 11},
        {'hogar_id': 5, 'usuario_id': 14, 'evento_id': 9, 'periodo_id': 12},
        {'hogar_id': 5, 'usuario_id': 15, 'evento_id': 9, 'periodo_id': 12},
        {'hogar_id': 5, 'usuario_id': 14, 'evento_id': 9, 'periodo_id': 12},
        {'hogar_id': 5, 'usuario_id': 15, 'evento_id': 9, 'periodo_id': 12}
    ]
    
    consumo_energia_hogares = []
    
    for hogar_id in miembros_por_hogar.keys():
            for periodo_id in range(1, 20):  # Considerando periodos del 1 al 19
                consumo_kwh = random.randint(100, 400)
                
                if consumo_kwh <= 300:
                    tarifa = 'básico'
                    precio_energia = 0.595
                elif 301 <= consumo_kwh <= 750:
                    tarifa = 'intermedio-bajo'
                    precio_energia = 0.741
                elif 751 <= consumo_kwh <= 900:
                    tarifa = 'intermedio-alto'
                    precio_energia = 0.967
                else:
                    tarifa = 'excedente'
                    precio_energia = 2.859
                    
                precio_total = consumo_kwh * precio_energia
                
                consumo_energia_hogares.append({
                    'hogar_id': hogar_id, 
                    'periodo_id': periodo_id, 
                    'consumo_kwh': consumo_kwh,
                    'tarifa': tarifa,
                    'precio_energia': precio_energia,
                    'precio_total': precio_total
                })
                
    consumo_agua_hogares = []
    
    for hogar_id, miembros in miembros_por_hogar.items():
            for periodo_id in range(1, 20):  # Considerando periodos del 1 al 19
                consumo_litros = round(random.uniform(50, 150) * miembros * 30, 2)
                consumo_agua_hogares.append({'hogar_id': hogar_id, 'periodo_id': periodo_id, 'consumo_litros': consumo_litros})
                
    dispositivos = []
    
    for hogar_id, user_ids in usuarios_por_hogar.items():
        for user_id in user_ids:
            tipo = random.choice(tipos_dispositivo)
            estado = random.choice(estados_dispositivo)
            dispositivos.append({'hogar_id': hogar_id, 'user_id': user_id, 'tipo': tipo, 'estado': estado})
    
    try:
        for codigo in codigos:
            c.execute(
                '''INSERT INTO codigos_acceso (codigo, paquete, disponible)
                VALUES (%s, %s, %s)''',
                (codigo['codigo'], codigo['paquete'], codigo['disponible'])
            )
        
        for estado in estados:
            c.execute(
                '''INSERT INTO estados (nombre)
                VALUES (%s)''',
                (estado,)
            )
        
        for hogar in hogares:
            c.execute(
                '''INSERT INTO hogares (codigo_postal, calle, numero_exterior, numero_interior, colonia, municipio, estado, informacion_adicional, estatus)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (hogar['codigo_postal'], hogar['calle'], hogar['numero_exterior'], hogar['numero_interior'], hogar['colonia'], hogar['municipio'], hogar['estado'], hogar['informacion_adicional'], hogar['estatus'])
            )
        
        for usuario in usuarios:
            c.execute(
                '''INSERT INTO users (nombre, apellidos, email, password, telefono, rol, codigo_acceso, acepto_terminos, hogar_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (usuario['nombre'], usuario['apellidos'], usuario['email'], usuario['password'], usuario['telefono'], usuario['rol'], usuario['codigo_acceso'], usuario['acepto_terminos'], usuario['hogar_id'])
            )
            
        for evento in eventos:
            c.execute(
                '''INSERT INTO eventos (nombre)
                VALUES (%s)''',
                (evento['nombre'],)
            )
            
        for periodo in periodos:
            c.execute(
                '''INSERT INTO periodos (nombre, inicio, fin)
                VALUES (%s, %s, %s)''',
                (periodo['nombre'], periodo['inicio'], periodo['fin'])
            )
            
        for registro_evento in registros_eventos:
            c.execute(
                '''INSERT INTO registros_eventos (hogar_id, usuario_id, evento_id, periodo_id)
                VALUES (%s, %s, %s, %s)''',
                (registro_evento['hogar_id'], registro_evento['usuario_id'], registro_evento['evento_id'], registro_evento['periodo_id'])
            )
            
        for consumo_energia in consumo_energia_hogares:
            c.execute(
                '''INSERT INTO consumo_energia (hogar_id, periodo_id, consumo_kwh, tarifa, precio_energia, precio_total)
                VALUES (%s, %s, %s, %s, %s, %s)''',
                (consumo_energia['hogar_id'], consumo_energia['periodo_id'], consumo_energia['consumo_kwh'],
                 consumo_energia['tarifa'], consumo_energia['precio_energia'], consumo_energia['precio_total'])
            )
            
        for consumo_agua in consumo_agua_hogares:
            c.execute(
                '''INSERT INTO consumo_agua (hogar_id, periodo_id, consumo_litros)
                VALUES (%s, %s, %s)''',
                (consumo_agua['hogar_id'], consumo_agua['periodo_id'], consumo_agua['consumo_litros'])
            )
            
        for dispositivo in dispositivos:
            c.execute(
                '''INSERT INTO dispositivos (hogar_id, user_id, tipo, estado)
                VALUES (%s, %s, %s, %s)''',
                (dispositivo['hogar_id'], dispositivo['user_id'], dispositivo['tipo'], dispositivo['estado'])
            )

        db.commit()
    except Exception as e:
        db.rollback()
        click.echo(f'Error al poblar la base de datos: {str(e)}')
        return

@click.command('seed-database')
@with_appcontext
def seed_database_command():
    seed_database()
    click.echo('Seeders ejecutados')
    
def seed_registros_eventos():
    db, c = get_db()

    registros_eventos = [
        {'hogar_id': 1, 'evento_id': 1, 'timestamp': '2024-06-28 12:00:00'},
        {'hogar_id': 1, 'evento_id': 3, 'timestamp': '2024-06-28 12:10:00'},
        {'hogar_id': 2, 'evento_id': 2, 'timestamp': '2024-06-28 12:20:00'},
        {'hogar_id': 3, 'evento_id': 4, 'timestamp': '2024-06-28 12:30:00'}
    ]

    try:
        for registro_evento in registros_eventos:
            c.execute(
                '''INSERT INTO registros_eventos (hogar_id, evento_id, timestamp)
                VALUES (%s, %s, %s)''',
                (registro_evento['hogar_id'], registro_evento['evento_id'], registro_evento['timestamp'])
            )
        db.commit()
    except Exception as e:
        click.echo(f'Error al poblar la base de datos: {str(e)}')
        return

@click.command('seed-registros-eventos')
@with_appcontext
def seed_registros_eventos_command():
    seed_registros_eventos()
    click.echo('Tabla registros eventos poblada')