import mysql.connector
import os
import string
from faker import Faker

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
from unidecode import unidecode

fake = Faker('es_MX')

# Definir tipos de dispositivo y posibles estados
tipos_dispositivo = ['celular', 'computadora', 'tablet']
estados_dispositivo = ['conectado', 'desconectado']
    
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

# Calcula el precio total del consumo de agua basado en las tarifas y el consumo
def calcular_precio_agua(consumo_litros):
    if consumo_litros <= 10000:
        tarifa = 'básico'
        precio_agua = 15.25
    elif 10001 <= consumo_litros <= 20000:
        tarifa = 'intermedio'
        precio_agua = 23.22
    else:
        tarifa = 'excedente'
        precio_agua = 26.67
    
    precio_total = (consumo_litros / 1000) * precio_agua
    return tarifa, precio_agua, precio_total

def generate_codigos_acceso(num_codigos, periodos):
    codigos_acceso = []
    
    def generar_codigo():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) + '-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    
    def generar_paquete():
        return random.choice(['Básico', 'Premium', 'Deluxe'])
    
    def generar_disponible(index):
        return index >= num_codigos // 2
    
    def obtener_periodo_aleatorio():
        return random.choice(periodos)
    
    def generar_tipo_suscripcion():
        return random.choice(['semestral', 'anual'])
    
    def calcular_fechas(inicio_periodo, tipo_suscripcion):
        inicio_str = inicio_periodo.strftime('%Y-%m-%d')
        inicio = datetime.strptime(inicio_str, '%Y-%m-%d')
        if tipo_suscripcion == 'semestral':
            fin = inicio + timedelta(days=182)  # Aproximadamente 6 meses
        else:
            fin = inicio + timedelta(days=365)  # Aproximadamente 1 año
        return inicio.strftime('%Y-%m-%d'), fin.strftime('%Y-%m-%d')
    
    def calcular_precio(paquete, tipo_suscripcion):
        precios = {
            'Básico': {'semestral': 50, 'anual': 90},
            'Premium': {'semestral': 80, 'anual': 150},
            'Deluxe': {'semestral': 100, 'anual': 190},
        }
        return precios[paquete][tipo_suscripcion]
    
    for i in range(num_codigos):  # Generar 100 códigos de acceso
        codigo = generar_codigo()
        paquete = generar_paquete()
        disponible = generar_disponible(i)
        periodo = obtener_periodo_aleatorio()
        periodo_id = periodo['id']
        inicio_periodo = periodo['inicio']
        tipo_suscripcion = generar_tipo_suscripcion()
        inicio, fin = calcular_fechas(inicio_periodo, tipo_suscripcion)
        precio = calcular_precio(paquete, tipo_suscripcion)
        
        codigos_acceso.append({
            'codigo': codigo,
            'paquete': paquete,
            'disponible': 0,
            'periodo_id': periodo_id,
            'tipo_suscripcion': tipo_suscripcion,
            'inicio': inicio,
            'fin': fin,
            'precio': precio
        })
    
    return codigos_acceso

# Generar hogares en función de los códigos de acceso
def generate_hogares(codigos_acceso):
    hogares = []
    for codigo in codigos_acceso:
        hogar = {
            'codigo_postal': fake.postcode(),
            'calle': fake.street_name(),
            'numero_exterior': fake.building_number(),
            'numero_interior': fake.building_number(),
            'colonia': fake.city(),
            'municipio': fake.city(),
            'estado': fake.state(),
            'informacion_adicional': fake.catch_phrase(),
            'estatus': random.choice(['activo', 'inactivo', 'cancelado']),
            'tamanio': random.choice(['pequeño', 'mediano', 'grande'])
        }
        hogares.append(hogar)
    return hogares

def generate_usuarios(hogares, codigos_acceso):
    usuarios = []
    emails = set() # Para asegurarnos de que los correos electrónicos sean únicos
    
    def generar_nombre():
        return fake.first_name()
    
    def generar_apellidos():
        return fake.last_name()
    
    def generar_email(nombre):
        # Eliminar acentos del nombre y convertirlo a minúsculas
        nombre_sin_acentos = unidecode(nombre).lower().replace(' ', '.')
        base_email = f"{nombre_sin_acentos}@example.com"
        email = base_email
        i = 1
        while email in emails:
            email = f"{nombre_sin_acentos}_{i}@example.com"
            i += 1
        emails.add(email)
        return email
    
    def generar_password():
        return generate_password_hash('password')
    
    def generar_telefono():
        return ''.join(random.choices(string.digits, k=10))
    
    def generar_rol(admin):
        return 'Owner' if admin else 'User'
    
    codigo_index = 0
    
    for hogar in hogares:
        # Generar un usuario administrador
        nombre = generar_nombre()
        apellidos = generar_apellidos()
        email = generar_email(nombre)
        password = generar_password()
        telefono = generar_telefono()
        rol = generar_rol(admin=True)
        codigo_acceso_id = codigos_acceso[codigo_index]['id'] if codigo_index < len(codigos_acceso) else None
        periodo_id = codigos_acceso[codigo_index]['periodo_id'] if codigo_index < len(codigos_acceso) else None
        usuario_admin = {
            'nombre': nombre,
            'apellidos': apellidos,
            'email': email,
            'password': password,
            'telefono': telefono,
            'rol': rol,
            'codigo_acceso': codigo_acceso_id,
            'acepto_terminos': True,
            'hogar_id': hogar['id'],
            'periodo_id': periodo_id
        }
        
        usuarios.append(usuario_admin)
        codigo_index += 1
        
        # Generar otros usuarios para el hogar
        num_usuarios = random.randint(1, 4)  # Número aleatorio de usuarios por hogar
        for _ in range(num_usuarios):
            nombre = generar_nombre()
            apellidos = generar_apellidos()
            email = generar_email(nombre)
            password = generar_password()
            telefono = generar_telefono()
            rol = generar_rol(admin=False)
            
            usuario = {
                'nombre': nombre,
                'apellidos': apellidos,
                'email': email,
                'password': password,
                'telefono': telefono,
                'rol': rol,
                'codigo_acceso': None,  # Otros usuarios no necesitan código de acceso
                'acepto_terminos': True,
                'hogar_id': hogar['id'],
                'periodo_id': periodo_id
            }
            
            usuarios.append(usuario)
    
    return usuarios

def generate_registros_eventos(hogares, usuarios, eventos, periodos):
    registros_eventos = []

    for hogar in hogares:
        for usuario in usuarios:
            if usuario['hogar_id'] == hogar['id']:
                num_eventos = random.randint(0, 5)  # Número aleatorio de eventos por usuario
                for _ in range(num_eventos):
                    evento_id = 9
                    periodo_id = random.choice(periodos)['id']
                    
                    registro_evento = {
                        'hogar_id': hogar['id'],
                        'usuario_id': usuario['id'],
                        'evento_id': evento_id,
                        'periodo_id': periodo_id
                    }
                    
                    registros_eventos.append(registro_evento)
    
    return registros_eventos

# Generate consumption data
def generate_consumo_energia_hogares(hogares, periodos):
    consumo_energia_hogares = []
    for hogar in hogares:
        hogar_id = hogar['id']
        for periodo in periodos:
            periodo_id = periodo['id']
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
    return consumo_energia_hogares

def generate_consumo_agua_hogares(hogares, periodos):
    consumo_agua_hogares = []
    for hogar in hogares:
        hogar_id = hogar['id']
        num_miembros = random.randint(1, 5)  # Número aleatorio de miembros por hogar
        for periodo in periodos:
            periodo_id = periodo['id']
            consumo_litros = round(random.uniform(50, 150) * num_miembros * 30, 2)
            tarifa, precio_agua, precio_total = calcular_precio_agua(consumo_litros)
            consumo_agua_hogares.append({
                'hogar_id': hogar_id, 
                'periodo_id': periodo_id, 
                'consumo_litros': consumo_litros,
                'tarifa': tarifa,
                'precio_agua': precio_agua,
                'precio_total': precio_total
            })
    return consumo_agua_hogares

def generate_dispositivos(usuarios):
    usuarios_por_hogar = {}
    for usuario in usuarios:
        hogar_id = usuario['hogar_id']
        if hogar_id not in usuarios_por_hogar:
            usuarios_por_hogar[hogar_id] = []
        usuarios_por_hogar[hogar_id].append(usuario['id'])
    
    dispositivos = []
    for hogar_id, user_ids in usuarios_por_hogar.items():
        for user_id in user_ids:
            tipo = random.choice(tipos_dispositivo)
            estado = random.choice(estados_dispositivo)
            dispositivos.append({
                'hogar_id': hogar_id, 
                'user_id': user_id, 
                'tipo': tipo, 
                'estado': estado
            })
    return dispositivos

def init_app(app):
    # Carga las variables de entorno desde el archivo .env
    load_dotenv()
    
    #ejecuta funciones que nosotros le pasamos como argumento
    #Cerramos la conexión a la BD
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(drop_tables_command)
    app.cli.add_command(seed_database_command)
    
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
        db.close()
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
        db.close()
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
    
    periodos = generate_periodos()
    
    estados = [
        'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas', 'Chihuahua', 
        'Coahuila', 'Colima', 'Durango', 'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Estado de México', 
        'Michoacán', 'Morelos', 'Nayarit', 'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 
        'San Luis Potosí', 'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 
        'Zacatecas'
    ]

    codigos = [
        {'codigo': 'CODE-1AB', 'paquete': 'Básico', 'disponible': False, 'periodo_id': 19, 'tipo_suscripcion': 'anual', 'inicio': '2024-07-01', 'fin': '2025-07-01', 'precio': 90.0},
        {'codigo': 'CODE-2BC', 'paquete': 'Básico', 'disponible': False, 'periodo_id': 19, 'tipo_suscripcion': 'semestral', 'inicio': '2024-07-01', 'fin': '2024-12-30', 'precio': 50.0},
        {'codigo': 'CODE-3CD', 'paquete': 'Premium', 'disponible': False, 'periodo_id': 18, 'tipo_suscripcion': 'anual', 'inicio': '2024-06-01', 'fin': '2025-06-01','precio': 150.0},
        {'codigo': 'CODE-4DE', 'paquete': 'Premium', 'disponible': False, 'periodo_id': 18, 'tipo_suscripcion': 'semestral', 'inicio': '2024-06-01', 'fin': '2024-11-30', 'precio': 80.0},
        {'codigo': 'CODE-5EF', 'paquete': 'Deluxe', 'disponible': False, 'periodo_id': 17, 'tipo_suscripcion': 'anual', 'inicio': '2024-05-01', 'fin': '2025-05-01', 'precio': 190.0}
    ]
    
    hogares = [
        {'codigo_postal': '01000', 'calle': 'Calle Falsa', 'numero_exterior': '123', 'numero_interior': 'A', 'colonia': 'Centro', 'municipio': 'Ciudad de México', 'estado': 'Ciudad de México', 'informacion_adicional': 'Cerca del parque', 'estatus': 'activo', 'tamanio': 'pequeño'},
        {'codigo_postal': '02000', 'calle': 'Avenida Siempre Viva', 'numero_exterior': '742', 'numero_interior': '', 'colonia': 'Primavera', 'municipio': 'Monterrey', 'estado': 'Nuevo León', 'informacion_adicional': '', 'estatus': 'activo', 'tamanio': 'mediano'},
        {'codigo_postal': '03000', 'calle': 'Callejón sin Salida', 'numero_exterior': '666', 'numero_interior': 'B', 'colonia': 'Fantasma', 'municipio': 'Guadalajara', 'estado': 'Jalisco', 'informacion_adicional': 'Al lado del cementerio', 'estatus': 'activo', 'tamanio': 'grande'},
        {'codigo_postal': '04000', 'calle': 'Camino Real', 'numero_exterior': '789', 'numero_interior': '', 'colonia': 'San Juan', 'municipio': 'Puebla', 'estado': 'Puebla', 'informacion_adicional': '', 'estatus': 'activo', 'tamanio': 'pequeño'},
        {'codigo_postal': '05000', 'calle': 'Av. Revolución', 'numero_exterior': '101', 'numero_interior': 'C', 'colonia': 'Las Flores', 'municipio': 'Querétaro', 'estado': 'Querétaro', 'informacion_adicional': 'Frente a la plaza', 'estatus': 'activo', 'tamanio': 'mediano'}
    ]

    usuarios = [
        {'nombre': 'Juan', 'apellidos': 'Pérez', 'email': 'juan.perez@example.com', 'password': generate_password_hash('password'), 'telefono': '1234567890', 'rol': 'Admin', 'codigo_acceso': None, 'acepto_terminos': True, 'hogar_id': None, 'periodo_id': None},
        {'nombre': 'Ana', 'apellidos': 'García', 'email': 'ana.garcia@example.com', 'password': generate_password_hash('password'), 'telefono': '0987654321', 'rol': 'Owner', 'codigo_acceso': 1, 'acepto_terminos': True, 'hogar_id':1, 'periodo_id': 19},
        {'nombre': 'Luis', 'apellidos': 'Martínez', 'email': 'luis.martinez@example.com', 'password': generate_password_hash('password'), 'telefono': '1122334455', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True, 'hogar_id':1, 'periodo_id': 19},
        {'nombre': 'Carlos', 'apellidos': 'Hernández', 'email': 'carlos.hernandez@example.com', 'password': generate_password_hash('password'), 'telefono': '5566778899', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True, 'hogar_id':1, 'periodo_id': 19},
        {'nombre': 'María', 'apellidos': 'López', 'email': 'maria.lopez@example.com', 'password': generate_password_hash('password'), 'telefono': '6677889900', 'rol': 'Owner', 'codigo_acceso': 2, 'acepto_terminos': True,'hogar_id':2, 'periodo_id': 19},
        {'nombre': 'Miguel', 'apellidos': 'Rodríguez', 'email': 'miguel.rodriguez@example.com', 'password': generate_password_hash('password'), 'telefono': '7788990011', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True,'hogar_id':2, 'periodo_id': 19},
        {'nombre': 'Laura', 'apellidos': 'Gómez', 'email': 'laura.gomez@example.com', 'password': generate_password_hash('password'), 'telefono': '8899001122', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True,'hogar_id':2, 'periodo_id': 18},
        {'nombre': 'David', 'apellidos': 'Díaz', 'email': 'david.diaz@example.com', 'password': generate_password_hash('password'), 'telefono': '9900112233', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True,'hogar_id':2, 'periodo_id': 18},
        {'nombre': 'Sofía', 'apellidos': 'Fernández', 'email': 'sofia.fernandez@example.com', 'password': generate_password_hash('password'), 'telefono': '0011223344', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True,'hogar_id':2, 'periodo_id': 18},
        {'nombre': 'Jorge', 'apellidos': 'Morales', 'email': 'jorge.morales@example.com', 'password': generate_password_hash('password'), 'telefono': '1122334455', 'rol': 'Owner', 'codigo_acceso': 3, 'acepto_terminos': True,'hogar_id':3, 'periodo_id': 18},
        {'nombre': 'Patricia', 'apellidos': 'Ramírez', 'email': 'patricia.ramirez@example.com', 'password': generate_password_hash('password'), 'telefono': '2233445566', 'rol': 'Owner', 'codigo_acceso': 4, 'acepto_terminos': True,'hogar_id':4, 'periodo_id': 17},
        {'nombre': 'Manuel', 'apellidos': 'Cruz', 'email': 'manuel.cruz@example.com', 'password': generate_password_hash('password'), 'telefono': '3344556677', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True,'hogar_id':4,'periodo_id': 17},
        {'nombre': 'Gabriela', 'apellidos': 'Sánchez', 'email': 'gabriela.sanchez@example.com', 'password': generate_password_hash('password'), 'telefono': '4455667788', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True,'hogar_id':4, 'periodo_id': 17},
        {'nombre': 'Fernando', 'apellidos': 'Ortiz', 'email': 'fernando.ortiz@example.com', 'password': generate_password_hash('password'), 'telefono': '5566778899', 'rol': 'Owner', 'codigo_acceso': 5, 'acepto_terminos': True,'hogar_id':5, 'periodo_id': 17},
        {'nombre': 'Elena', 'apellidos': 'Vargas', 'email': 'elena.vargas@example.com', 'password': generate_password_hash('password'), 'telefono': '6677889900', 'rol': 'User', 'codigo_acceso': None, 'acepto_terminos': True, 'hogar_id':5, 'periodo_id': 17}
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
            tarifa, precio_agua, precio_total = calcular_precio_agua(consumo_litros)
            consumo_agua_hogares.append({
                'hogar_id': hogar_id, 
                'periodo_id': periodo_id, 
                'consumo_litros': consumo_litros,
                'tarifa': tarifa,
                'precio_agua': precio_agua,
                'precio_total': precio_total
            })
                
    dispositivos = []
    
    for hogar_id, user_ids in usuarios_por_hogar.items():
        for user_id in user_ids:
            tipo = random.choice(tipos_dispositivo)
            estado = random.choice(estados_dispositivo)
            dispositivos.append({'hogar_id': hogar_id, 'user_id': user_id, 'tipo': tipo, 'estado': estado})
    
    try:
        for periodo in periodos:
            c.execute(
                '''INSERT INTO periodos (nombre, inicio, fin)
                VALUES (%s, %s, %s)''',
                (periodo['nombre'], periodo['inicio'], periodo['fin'])
            )
            
        for estado in estados:
            c.execute(
                '''INSERT INTO estados (nombre)
                VALUES (%s)''',
                (estado,)
            )
            
        for codigo in codigos:
            c.execute(
                '''INSERT INTO codigos_acceso (codigo, paquete, disponible, periodo_id, tipo_suscripcion, inicio, fin, precio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                (codigo['codigo'], codigo['paquete'], codigo['disponible'], codigo['periodo_id'], codigo['tipo_suscripcion'], codigo['inicio'], codigo['fin'], codigo['precio'])
            )
        
        for hogar in hogares:
            c.execute(
                '''INSERT INTO hogares (codigo_postal, calle, numero_exterior, numero_interior, colonia, municipio, estado, informacion_adicional, estatus, tamanio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (hogar['codigo_postal'], hogar['calle'], hogar['numero_exterior'], hogar['numero_interior'], hogar['colonia'], hogar['municipio'], hogar['estado'], hogar['informacion_adicional'], hogar['estatus'], hogar['tamanio'])
            )
        
        for usuario in usuarios:
            c.execute(
                '''INSERT INTO users (nombre, apellidos, email, password, telefono, rol, codigo_acceso, acepto_terminos, hogar_id, periodo_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (usuario['nombre'], usuario['apellidos'], usuario['email'], usuario['password'], usuario['telefono'], usuario['rol'], usuario['codigo_acceso'], usuario['acepto_terminos'], usuario['hogar_id'], usuario['periodo_id'])
            )
            
        for evento in eventos:
            c.execute(
                '''INSERT INTO eventos (nombre)
                VALUES (%s)''',
                (evento['nombre'],)
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
                '''INSERT INTO consumo_agua (hogar_id, periodo_id, consumo_litros, tarifa, precio_agua, precio_total)
                VALUES (%s, %s, %s, %s, %s, %s)''',
                (consumo_agua['hogar_id'], consumo_agua['periodo_id'], consumo_agua['consumo_litros'],
                consumo_agua['tarifa'], consumo_agua['precio_agua'], consumo_agua['precio_total'])
            )
            
        for dispositivo in dispositivos:
            c.execute(
                '''INSERT INTO dispositivos (hogar_id, user_id, tipo, estado)
                VALUES (%s, %s, %s, %s)''',
                (dispositivo['hogar_id'], dispositivo['user_id'], dispositivo['tipo'], dispositivo['estado'])
            )

        # db.commit()
        
        # PARTE 2 DE LOS SEEDERS
        
        # Seleccionar periodos desde la base de datos con sus IDs
        c.execute("SELECT * FROM periodos")
        periodosCommit = c.fetchall()
        
        # Generar y insertar códigos de acceso
        num_codigos = 10  # Número de códigos de acceso a generar
        codigos_acceso = generate_codigos_acceso(num_codigos, periodosCommit)
        for codigo in codigos_acceso:
            c.execute(
                '''INSERT INTO codigos_acceso (codigo, paquete, disponible, periodo_id, tipo_suscripcion, inicio, fin, precio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                (codigo['codigo'], codigo['paquete'], codigo['disponible'], codigo['periodo_id'], codigo['tipo_suscripcion'], codigo['inicio'], codigo['fin'], codigo['precio'])
            )
            codigo['id'] = c.lastrowid
        
        # Generar y insertar hogares en función de los códigos de acceso
        hogares = generate_hogares(codigos_acceso)
        for hogar in hogares:
            c.execute(
                '''INSERT INTO hogares (codigo_postal, calle, numero_exterior, numero_interior, colonia, municipio, estado, informacion_adicional, estatus, tamanio)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (hogar['codigo_postal'], hogar['calle'], hogar['numero_exterior'], hogar['numero_interior'], hogar['colonia'], hogar['municipio'], hogar['estado'], hogar['informacion_adicional'], hogar['estatus'], hogar['tamanio'])
            )
            hogar['id'] = c.lastrowid
        
        # Generar y insertar usuarios en función de los hogares
        usuarios = generate_usuarios(hogares, codigos_acceso) 
        for usuario in usuarios:
            c.execute(
                '''INSERT INTO users (nombre, apellidos, email, password, telefono, rol, codigo_acceso, acepto_terminos, hogar_id, periodo_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (usuario['nombre'], usuario['apellidos'], usuario['email'], usuario['password'], usuario['telefono'], usuario['rol'], usuario['codigo_acceso'], usuario['acepto_terminos'], usuario['hogar_id'], usuario['periodo_id'])
            )
            usuario['id'] = c.lastrowid
            
        registros_eventos = generate_registros_eventos(hogares, usuarios, eventos, periodosCommit)     
        for registro in registros_eventos:
            c.execute(
                '''INSERT INTO registros_eventos (hogar_id, usuario_id, evento_id, periodo_id)
                VALUES (%s, %s, %s, %s)''',
                (registro['hogar_id'], registro['usuario_id'], registro['evento_id'], registro['periodo_id'])
            )
            
        registros_consumo_energia = generate_consumo_energia_hogares(hogares, periodosCommit)      
        for consumo in registros_consumo_energia:
            c.execute(
                '''INSERT INTO consumo_energia (hogar_id, periodo_id, consumo_kwh, tarifa, precio_energia, precio_total)
                VALUES (%s, %s, %s, %s, %s, %s)''',
                (consumo['hogar_id'], consumo['periodo_id'], consumo['consumo_kwh'], consumo['tarifa'], consumo['precio_energia'], consumo['precio_total'])
            )
            
        registros_consumo_agua = generate_consumo_agua_hogares(hogares, periodosCommit)
        for consumo in registros_consumo_agua:
            c.execute(
                '''INSERT INTO consumo_agua (hogar_id, periodo_id, consumo_litros, tarifa, precio_agua, precio_total)
                VALUES (%s, %s, %s, %s, %s, %s)''',
                (consumo['hogar_id'], consumo['periodo_id'], consumo['consumo_litros'], consumo['tarifa'], consumo['precio_agua'], consumo['precio_total'])
            )
            
        registros_dispositivos = generate_dispositivos(usuarios)
        
        for dispositivo in registros_dispositivos:
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
    finally:
        close_db()  # Cerrar conexión a la base de datos

@click.command('seed-database')
@with_appcontext
def seed_database_command():
    seed_database()
    click.echo('Seeders ejecutados')