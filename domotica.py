from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, request, session
)
from .auth import login_required, user_role_required

from .db import get_db

bp = Blueprint('domotica', __name__)

@bp.route('/user-domotica')
@login_required
@user_role_required
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