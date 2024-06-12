import mysql.connector
from mysql.connector import Error
import click
from flask import current_app, g
from flask.cli import with_appcontext
from .schema import instructions

try:
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='ssafezone',
        port=3307,
    )

    if db.is_connected():
        print("Conexión exitosa a la base de datos MySQL")
        

except Error as e:
    print(f"Error al conectar a la base de datos MySQL: {e}")

finally:
    if db.is_connected():
        db.close()
        print("Conexión a MySQL cerrada")
