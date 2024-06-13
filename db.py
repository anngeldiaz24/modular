import mysql.connector

#Ejecutar comandos en la terminal
import click

#Current mantiene la aplicacion que se ejecuta y 
#con g podemos acceder a variables e ir asignandolas a distintas cosas
from flask import current_app, g
#Nos sirve para ejecutar el script de la base de datos (host, base de datos, password)
from flask.cli import with_appcontext

from .schema import instructions

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
    print(current_app.config['DATABASE'])
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

    click.echo('Base de datos inicializada')

@click.command('init-db')
@with_appcontext

def init_db_command():
    init_db()
    click.echo('Base de datos inicializada')
    

def init_app(app):
    #ejecuta funciones que nosotros le pasamos como argumento
    #Cerramos la conexión a la BD
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    
    # Configuración de la base de datos
    app.config['DATABASE_HOST'] = 'localhost'
    app.config['DATABASE_USER'] = 'root'
    app.config['DATABASE_PASSWORD'] = ''  
    app.config['DATABASE'] = 'samsung'
    app.config['DATABASE_PORT'] = 3307  # Puerto personalizado