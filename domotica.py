from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, request, session
)
from .auth import login_required, user_role_required
from babel.dates import format_date
from datetime import datetime
from .db import get_db, close_db

bp = Blueprint('domotica', __name__)

# Función para formatear la fecha al mes en español
def formatear_fecha(fecha):
    if fecha:
        return format_date(fecha, format='MMMM yyyy', locale='es')
    return None

def get_consumo_energia(columna):
    # Establece conexión a la base de datos
    db, c = get_db()
    
    try:
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
        
        # Consulta para obtener los consumos de los dos últimos periodos
        query_ultimos_periodos = f"""
        SELECT periodo_id, {columna}
        FROM consumo_energia
        WHERE hogar_id = %s
        ORDER BY periodo_id DESC
        LIMIT 2
        """
    
        c.execute(query_ultimos_periodos, (hogar_id,))
        ultimos_periodos = c.fetchall()
        
        if len(ultimos_periodos) < 2:
            diferencia_porcentual = None  # No hay suficientes datos para calcular la diferencia porcentual
        else:
            consumo_actual = ultimos_periodos[0][columna]
            consumo_anterior = ultimos_periodos[1][columna]
            diferencia = consumo_actual - consumo_anterior
            porcentaje_cambio = (diferencia / consumo_anterior) * 100
            diferencia_porcentual = {
                'consumo_actual': consumo_actual,
                'consumo_anterior': consumo_anterior,
                'porcentaje_cambio': porcentaje_cambio,
                'positivo': porcentaje_cambio > 0
            }
        
        return datos_grafica, diferencia_porcentual
    finally:
        close_db()

def get_consumo_agua(columna='consumo_litros'):
    # Establece conexión a la base de datos
    db, c = get_db()
    
    try:
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
    finally:
        close_db()

def get_dispositivos_por_tipo():
    # Establece conexión a la base de datos
    db, c = get_db()
    
    try:
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
    finally:
        close_db()

def get_miembros_por_hogar():
    # Establece conexión a la base de datos
    db, c = get_db()
    
    try:
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
    finally:
        close_db()

def get_registros_modo_seguro():
    # Establece conexión a la base de datos
    db, c = get_db()
    
    try:
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
    finally:
        close_db()

def get_codigo_acceso_por_hogar():
    # Establece conexión a la base de datos
    db, c = get_db()
    
    try:
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
    finally:
        close_db()

def get_dispositivos_por_hogar():
    # Establece conexión a la base de datos
    db, c = get_db()
    
    try:
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
    finally:
        close_db()

# Función para obtener el último periodo
def get_ultimo_periodo_energia(hogar_id):
    db, c = get_db()
    
    try:
        query = """
        SELECT MAX(periodo_id) as ultimo_periodo_id
        FROM consumo_energia
        WHERE hogar_id = %s
        """
        
        c.execute(query, (hogar_id,))
        resultado = c.fetchone()
    
        return resultado['ultimo_periodo_id'] if resultado else None
    finally:
        close_db()
    
# Función para obtener el consumo de un período específico
def get_consumo_periodo_energia(hogar_id, periodo_id, columna):
    db, c = get_db()
    
    try:
        query = f"""
        SELECT ce.{columna}, p.inicio
        FROM consumo_energia ce
        JOIN periodos p ON ce.periodo_id = p.id
        WHERE ce.hogar_id = %s AND ce.periodo_id = %s
        """
        c.execute(query, (hogar_id, periodo_id))
        resultado = c.fetchone()
        
        return resultado[columna], resultado['inicio'] if resultado else (None, None)
    finally:
        close_db()

# Función para calcular el cambio porcentual
def calcular_cambio_porcentual_energia(consumo_anterior, consumo_actual):
    if consumo_anterior == 0:
        return 100 if consumo_actual > 0 else 0
    cambio_porcentual = ((consumo_actual - consumo_anterior) / consumo_anterior) * 100
    return round(cambio_porcentual, 2)

# Integración para obtener y calcular los consumos
def get_calcular_cambio_energia(hogar_id, columna):
    db, c = get_db()
    try:
        ultimo_periodo = get_ultimo_periodo_energia(hogar_id)
        if ultimo_periodo is None:
            return None, None, None, None  # No hay datos disponibles

        consumo_actual, inicio_actual = get_consumo_periodo_energia(hogar_id, ultimo_periodo, columna)
        consumo_anterior, inicio_anterior = get_consumo_periodo_energia(hogar_id, ultimo_periodo - 1, columna) if ultimo_periodo > 1 else (None, None)

        cambio_porcentual = calcular_cambio_porcentual_energia(consumo_anterior, consumo_actual) if consumo_anterior is not None else None

        return consumo_actual, cambio_porcentual, inicio_anterior
    finally:
        close_db()

@bp.route('/user-domotica')
@login_required
@user_role_required
def user_domotica():
    hogar_id = g.user['hogar_id'] # ID de hogar del usuario que ha iniciado sesión
    
    # CANTIDAD DE MIEMBROS POR HOGAR
    miembros = get_miembros_por_hogar()
    
    # CANTIDAD DE DISPOSITIVOS POR HOGAR
    dispositivos = get_dispositivos_por_hogar()
    
    # USOS DE MODO SEGURO POR HOGAR
    modo_seguro = get_registros_modo_seguro()
    
    # TIPO DE PAQUETE
    paquete = get_codigo_acceso_por_hogar()
    
    # GRAFICA LINE - CONSUMO DE ENERGIA (kwh)
    datos_grafica_energia_kwh, diferencia_porcentual_kwh = get_consumo_energia('consumo_kwh')
    
    consumo_energia_kwh_2023 = [0] * 12
    consumo_energia_kwh_2024 = [0] * 12
    
    for dato in datos_grafica_energia_kwh:
        periodo_id = int(dato['periodo_id'])
        consumo_kwh = float(dato['consumo_kwh'])
        
        if 1 <= periodo_id <= 12:
            consumo_energia_kwh_2023[periodo_id - 1] = consumo_kwh
        elif 13 <= periodo_id <= 24:
            consumo_energia_kwh_2024[periodo_id - 13] = consumo_kwh
            
    # Obtener último periodo y cambios porcentuales de energía para kWh
    consumo_actual_kwh, cambio_porcentual_kwh, inicio_anterior_kwh = get_calcular_cambio_energia(hogar_id, 'consumo_kwh')
            
    # GRAFICA LINE - CONSUMO DE ENERGIA (MXN)
    datos_grafica_energia_mxn, diferencia_porcentual_energia_mxn = get_consumo_energia('precio_total')
    
    consumo_energia_mxn_2023 = [0] * 12
    consumo_energia_mxn_2024 = [0] * 12
    
    for dato in datos_grafica_energia_mxn:
        periodo_id = int(dato['periodo_id'])
        consumo_mxn = float(dato['precio_total'])
        
        if 1 <= periodo_id <= 12:
            consumo_energia_mxn_2023[periodo_id - 1] = consumo_mxn
        elif 13 <= periodo_id <= 24:
            consumo_energia_mxn_2024[periodo_id - 13] = consumo_mxn
            
    # Obtener último periodo y cambios porcentuales de energía para precio
    consumo_actual_energia_mxn, cambio_porcentual_energia_mxn, inicio_anterior_energia_mxn = get_calcular_cambio_energia(hogar_id, 'precio_total')
    
    # Formatear fechas al mes en español
    inicio_anterior_kwh_formateado = formatear_fecha(inicio_anterior_kwh)
    inicio_anterior_energia_mxn_formateado = formatear_fecha(inicio_anterior_energia_mxn)
            
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
        # GRÁFICA LINE - CONSUMO DE ENERGIA
        consumo_energia_kwh_2023=consumo_energia_kwh_2023, 
        consumo_energia_kwh_2024=consumo_energia_kwh_2024,
        consumo_actual_kwh=consumo_actual_kwh,
        cambio_porcentual_kwh=cambio_porcentual_kwh,
        consumo_energia_mxn_2023=consumo_energia_mxn_2023,
        consumo_energia_mxn_2024=consumo_energia_mxn_2024,
        consumo_actual_energia_mxn=consumo_actual_energia_mxn,
        cambio_porcentual_energia_mxn=cambio_porcentual_energia_mxn,
        inicio_anterior_kwh_formateado=inicio_anterior_kwh_formateado,
        inicio_anterior_energia_mxn_formateado=inicio_anterior_energia_mxn_formateado,
        diferencia_porcentual_kwh=diferencia_porcentual_kwh,
        diferencia_porcentual_energia_mxn=diferencia_porcentual_energia_mxn,
        # GRAFICA LINE - CONSUMO DE AGUA
        consumo_agua_litros_2023=consumo_agua_litros_2023,
        consumo_agua_litros_2024=consumo_agua_litros_2024,
        consumo_agua_mxn_2023=consumo_agua_mxn_2023,
        consumo_agua_mxn_2024=consumo_agua_mxn_2024,
        # GRAFICA PIE - TIPOS DE DISPOSITIVOS
        dispositivos_tipos=dispositivos_tipos,
        dispositivos_cantidades=dispositivos_cantidades
        )
