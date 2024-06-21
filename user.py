from flask import (
    Blueprint, flash, g, redirect, render_template, url_for, 
)
from werkzeug.exceptions import abort
from .auth import login_required
from .db import get_db

bp = Blueprint('user', __name__)

@bp.route('/user-dashboard')
@login_required
def user_index():
    return render_template('user-dashboard.html', user=g.user)
