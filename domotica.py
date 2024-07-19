from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, request, session
)
from .auth import login_required, user_role_required

from .db import get_db

bp = Blueprint('domotica', __name__)

def get_consumo_energia():
    # Establece conexión a la base de datos
    db, c = get_db()
    
    # Obtiene el hogar del usuario que ha iniciado sesión
    hogar_id = g.user['hogar_id']
    
    # Consulta para obtener el consumo_kwh del hogar por periodo
    query = """
    SELECT periodo_id, consumo_kwh
    FROM consumo_energia
    WHERE hogar_id = %s
    ORDER BY periodo_id
    """
    
    c.execute(query, (hogar_id,))
    # Obtiene los resultados de la consulta
    datos = c.fetchall()
    
    # Convierte los resultados a un formato de lista de diccionarios
    datos_grafica = [{'periodo_id': dato['periodo_id'], 'consumo_kwh': float(dato['consumo_kwh'])} for dato in datos]
    
    return datos_grafica

@bp.route('/user-domotica')
@login_required
@user_role_required
def user_domotica():
    datos_grafica = get_consumo_energia()
    
    consumo_energia_2023 = [0] * 12
    consumo_energia_2024 = [0] * 12
    
    for dato in datos_grafica:
        periodo_id = int(dato['periodo_id'])
        consumo_kwh = float(dato['consumo_kwh'])
        
        if 1 <= periodo_id <= 12:
            consumo_energia_2023[periodo_id - 1] = consumo_kwh
        elif 13 <= periodo_id <= 24:
            consumo_energia_2024[periodo_id - 13] = consumo_kwh
            
    print(consumo_energia_2023)
    print(consumo_energia_2024)
            
    return render_template(
        'user-domotica.html', 
        user=g.user, 
        consumo_energia_2023=consumo_energia_2023, 
        consumo_energia_2024=consumo_energia_2024
        )
