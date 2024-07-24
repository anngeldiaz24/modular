from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, request, session
)
from .auth import login_required, user_role_required

from .db import get_db

bp = Blueprint('domotica', __name__)

def get_consumo_energia(columna='consumo_kwh'):
    # Establece conexión a la base de datos
    db, c = get_db()
    
    # Obtiene el hogar del usuario que ha iniciado sesión
    hogar_id = g.user['hogar_id']
    
    # Consulta para obtener los datos del hogar por periodo
    query = f"""
    SELECT periodo_id, {columna}
    FROM consumo_energia
    WHERE hogar_id = %s
    ORDER BY periodo_id
    """
    
    c.execute(query, (hogar_id,))
    # Obtiene los resultados de la consulta
    datos = c.fetchall()
    
    # Convierte los resultados a un formato de lista de diccionarios
    datos_grafica = [{'periodo_id': dato['periodo_id'], columna: float(dato[columna])} for dato in datos]
    
    return datos_grafica

def get_consumo_agua(columna='consumo_litros'):
    # Establece conexión a la base de datos
    db, c = get_db()
    
    # Obtiene el hogar del usuario que ha iniciado sesión
    hogar_id = g.user['hogar_id']
    
    # Consulta para obtener el consumo_litros del hogar por periodo
    query = f"""
    SELECT periodo_id, {columna}
    FROM consumo_agua
    WHERE hogar_id = %s
    ORDER BY periodo_id
    """
    
    c.execute(query, (hogar_id,))
    # Obtiene los resultados de la consulta
    datos = c.fetchall()
    
    # Convierte los resultados a un formato de lista de diccionarios
    datos_grafica = [{'periodo_id': dato['periodo_id'], columna: float(dato[columna])} for dato in datos]
    
    return datos_grafica

def get_dispositivos_por_tipo():
    # Establece conexión a la base de datos
    db, c = get_db()
    
    # Obtiene el hogar del usuario que ha iniciado sesión
    hogar_id = g.user['hogar_id']
    
    # Consulta para obtener los dispositivos del hogar por hogar
    query = """
    SELECT d.tipo, COUNT(d.id) as total
    FROM dispositivos d
    WHERE d.hogar_id = %s
    GROUP BY d.tipo
    """
    
    c.execute(query, (hogar_id,))
    # Obtiene los resultados de la consulta
    dispositivos = c.fetchall()
    
    dispositivos_tipos = [dispositivo['tipo'] for dispositivo in dispositivos]
    dispositivos_cantidades = [dispositivo['total'] for dispositivo in dispositivos]
    
    return dispositivos_tipos, dispositivos_cantidades

def get_miembros_por_hogar():
    # Establece conexión a la base de datos
    db, c = get_db()
    
    # Obtiene el hogar del usuario que ha iniciado sesión
    hogar_id = g.user['hogar_id']
    
    # Consulta para obtener los dispositivos del hogar por hogar
    query = """
    SELECT COUNT(id) as total
    FROM users
    WHERE hogar_id = %s
    """
    
    c.execute(query, (hogar_id,))
    # Obtiene los resultados de la consulta
    miembros = c.fetchall()
    
    return miembros

def get_registros_modo_seguro():
    # Establece conexión a la base de datos
    db, c = get_db()
    
    # Obtiene el hogar del usuario que ha iniciado sesión
    hogar_id = g.user['hogar_id']
    
    # Consulta para obtener el número de veces que se ha usado el modo seguro por hogar
    query = """
    SELECT COUNT(r.id) as total
    FROM registros_eventos r
    WHERE r.hogar_id = %s AND r.evento_id = 9
    """
    
    c.execute(query, (hogar_id,))
    modo_seguro = c.fetchone()
    
    return modo_seguro['total']

def get_codigo_acceso_por_hogar():
    # Establece conexión a la base de datos
    db, c = get_db()
    
    # Obtiene el hogar del usuario que ha iniciado sesión
    hogar_id = g.user['hogar_id']
    
    query = """
    SELECT ca.paquete
    FROM codigos_acceso ca
    JOIN users u ON u.codigo_acceso = ca.id
    WHERE u.hogar_id = %s
    """
    
    c.execute(query, (hogar_id,))
    codigo_acceso = c.fetchone()
    
    return codigo_acceso['paquete'] if codigo_acceso else None

def get_dispositivos_por_hogar():
    # Establece conexión a la base de datos
    db, c = get_db()
    
    # Obtiene el hogar del usuario que ha iniciado sesión
    hogar_id = g.user['hogar_id']
    
    # Consulta para obtener los dispositivos del hogar por hogar
    query = """
    SELECT COUNT(id) as total
    FROM dispositivos
    WHERE hogar_id = %s
    """
    
    c.execute(query, (hogar_id,))
    # Obtiene los resultados de la consulta
    dispositivos = c.fetchall()
    
    return dispositivos

@bp.route('/user-domotica')
@login_required
@user_role_required
def user_domotica():
    # CANTIDAD DE MIEMBROS POR HOGAR
    miembros = get_miembros_por_hogar()
    
    # CANTIDAD DE DISPOSITIVOS POR HOGAR
    dispositivos = get_dispositivos_por_hogar()
    
    # USOS DE MODO SEGURO POR HOGAR
    modo_seguro = get_registros_modo_seguro()
    
    # TIPO DE PAQUETE
    paquete = get_codigo_acceso_por_hogar()
    
    # GRAFICA LINE - CONSUMO DE ENERGIA (kwh)
    datos_grafica_energia_kwh = get_consumo_energia('consumo_kwh')
    
    consumo_energia_kwh_2023 = [0] * 12
    consumo_energia_kwh_2024 = [0] * 12
    
    for dato in datos_grafica_energia_kwh:
        periodo_id = int(dato['periodo_id'])
        consumo_kwh = float(dato['consumo_kwh'])
        
        if 1 <= periodo_id <= 12:
            consumo_energia_kwh_2023[periodo_id - 1] = consumo_kwh
        elif 13 <= periodo_id <= 24:
            consumo_energia_kwh_2024[periodo_id - 13] = consumo_kwh
            
    # GRAFICA LINE - CONSUMO DE ENERGIA (MXN)
    datos_grafica_energia_mxn = get_consumo_energia('precio_total')
    
    consumo_energia_mxn_2023 = [0] * 12
    consumo_energia_mxn_2024 = [0] * 12
    
    for dato in datos_grafica_energia_mxn:
        periodo_id = int(dato['periodo_id'])
        consumo_mxn = float(dato['precio_total'])
        
        if 1 <= periodo_id <= 12:
            consumo_energia_mxn_2023[periodo_id - 1] = consumo_mxn
        elif 13 <= periodo_id <= 24:
            consumo_energia_mxn_2024[periodo_id - 13] = consumo_mxn
            
    # GRAFICA LINE - CONSUMO DE AGUA (litros)
    datos_grafica_agua_litros = get_consumo_agua('consumo_litros')
    
    consumo_agua_litros_2023 = [0] * 12
    consumo_agua_litros_2024 = [0] * 12
    
    for dato_agua in datos_grafica_agua_litros:
        periodo_id = int(dato_agua['periodo_id'])
        consumo_litros = float(dato_agua['consumo_litros'])
        
        if 1 <= periodo_id <= 12:
            consumo_agua_litros_2023[periodo_id - 1] = consumo_litros
        elif 13 <= periodo_id <= 24:
            consumo_agua_litros_2024[periodo_id - 13] = consumo_litros
            
    # GRAFICA LINE - CONSUMO DE AGUA (MXN)
    datos_grafica_agua_mxn = get_consumo_agua('precio_total')
    
    consumo_agua_mxn_2023 = [0] * 12
    consumo_agua_mxn_2024 = [0] * 12
    
    for dato_agua in datos_grafica_agua_mxn:
        periodo_id = int(dato_agua['periodo_id'])
        consumo_mxn = float(dato_agua['precio_total'])
        
        if 1 <= periodo_id <= 12:
            consumo_agua_mxn_2023[periodo_id - 1] = consumo_mxn
        elif 13 <= periodo_id <= 24:
            consumo_agua_mxn_2024[periodo_id - 13] = consumo_mxn
    
    # GRAFICA PIE - TIPOS DE DISPOSITIVOS
    dispositivos_tipos, dispositivos_cantidades = get_dispositivos_por_tipo()
            
    return render_template(
        'user/user-domotica.html', 
        user=g.user,
        miembros=miembros[0]['total'],
        dispositivos=dispositivos[0]['total'],
        modo_seguro=modo_seguro,
        paquete=paquete,
        consumo_energia_kwh_2023=consumo_energia_kwh_2023, 
        consumo_energia_kwh_2024=consumo_energia_kwh_2024,
        consumo_energia_mxn_2023=consumo_energia_mxn_2023,
        consumo_energia_mxn_2024=consumo_energia_mxn_2024,
        consumo_agua_litros_2023=consumo_agua_litros_2023,
        consumo_agua_litros_2024=consumo_agua_litros_2024,
        consumo_agua_mxn_2023=consumo_agua_mxn_2023,
        consumo_agua_mxn_2024=consumo_agua_mxn_2024,
        dispositivos_tipos=dispositivos_tipos,
        dispositivos_cantidades=dispositivos_cantidades
        )
