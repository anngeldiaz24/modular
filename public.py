from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, request, session,
)
import requests
import os
import random
from datetime import datetime
from dotenv import load_dotenv
from babel.dates import format_date
from werkzeug.exceptions import abort
from .auth import login_required, admin_role_required
from .db import get_db, close_db

bp = Blueprint('public', __name__)

def get_paquetes():
    db, c = get_db()
    
    try:
        c.execute('''
            SELECT
                id, nombre, descripcion
            FROM
                paquetes    
        ''')
        data = c.fetchall()
        
        paquetes = {}
        for row in data:
            paquetes[row['id']] = {
                'nombre': row['nombre'],
                'descripcion': row['descripcion']
            }
    except Exception as e:
        flash(f"Ocurrió un error: {e}", 'error')
        paquetes = {}
        
    return paquetes
    

@bp.route('/paquetes-disponibles')
def paquetes_disponibles():
    paquetes = get_paquetes()
    
    # Define una lista de colores
    colores = [
        'bg-slate-900 dark:bg-slate-800', 'bg-primary-500', 'bg-success-500', 
        'bg-info-500', 'bg-danger-500', 'bg-warning-500'
    ]
    
    # Asigna un color basado en el ID del paquete
    color_count = len(colores)
    for i, (paquete_id, paquete) in enumerate(paquetes.items()):
        paquete['color'] = colores[i % color_count]
        
    ultimo_paquete = None
    if len(paquetes) % 2 != 0:
        # Extraer el último paquete y eliminarlo de la lista original
        ultimo_paquete_id = list(paquetes.keys())[-1]
        ultimo_paquete = paquetes.pop(ultimo_paquete_id)
        
    user_role = None
    if 'user_id' in session:
        user_role = g.user['rol']
        
    return render_template('public/paquetes-disponibles.html', paquetes=paquetes, ultimo_paquete=ultimo_paquete, user_role=user_role)