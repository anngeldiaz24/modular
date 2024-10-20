import os, time, locale
import threading # para crear hilos
import re # para usar expresiones regulares
from dotenv import load_dotenv # para cargar las variables del .env
from datetime import datetime # para acceder a la fecha y hora del sistema
import hashlib # para hashear la contraseña del usuario
from concurrent.futures import ThreadPoolExecutor
import telebot # para manejar la API de Telegram
from telebot import types
from telebot.types import BotCommand # para crear los comandos del menú de telegram
from telebot.types import ReplyKeyboardMarkup # para crear botones
from telebot.types import ForceReply # para citar un mensaje
from telebot.types import ReplyKeyboardRemove # para eliminar botones
from .raspberry import llamada_policia # para llamar a la policia
from .raspberry import funciones # para usar las funciones de la raspberry

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Accedemos a las variables de entorno
TOKEN = os.getenv('TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME') # Nombre de usuario de nuestro bot
AXL_CHAT_ID = os.getenv('AXL_CHAT_ID') # Id único de nuestro chat (axl)
ANGEL_CHAT_ID = os.getenv('ANGEL_CHAT_ID') # Id único de nuestro chat (angel)
DANIEL_CHAT_ID = os.getenv('DANIEL_CHAT_ID') # Id único de nuestro chat (daniel)

# Configurar el locale para obtener la fecha y hora en español
#locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

# Tupla con los chat id de los administradores del bot
ADMINISTRADORES = (1477140980,1136745071,1742695268,)

# Conexión con nuestro BOT
bot = telebot.TeleBot(TOKEN)

# Carpeta donde se guardan los registros de los tiempos de los mensajes de los usuarios
CARPETA = "modo_lento"
# Si no existe la carpeta
if not os.path.isdir(CARPETA):
    # Creamos la carpeta
    os.mkdir(CARPETA)

# Segundos de espera entre cada mensaje de un usuario
MODO_LENTO = 10
# Variable global en la que guardaremos los datos del usuario registrado
usuarios = {}
# Variable global en la que guardaremos los mensajes del modo lento del chat
chat_mensajes_modo_lento = {}
# Variable global en la que guardaremos los mensajes del registro del usuario
chat_mensajes_registro = {}

# Responde al comando /start y envia el menu de opciones al usuario
@bot.message_handler(commands=['start'])
def send_start_command(message):
    #print(message.chat.id)
    # Si el usuario aún no puede enviar mensajes al bot
    if usuario_tiene_que_esperar(message.chat.id):
        # Eliminamos el mensaje enviado por el usuario
        bot.delete_message(message.chat.id, message.message_id)
        # Finalizamos la función
        return
    
    user = message.from_user # Nombre de usuario en Telegram del cliente
    bot.send_chat_action(message.chat.id, "typing")
    bot.reply_to(message, f'¡Hola, {user.first_name} {user.last_name}! 👋 Bienvenido a tu bot de seguridad {BOT_USERNAME}.')

    # Modo desarrollador
    print(f"El usuario {message.from_user.id} con nombre de usuario {message.from_user.username} COMENZO a usar el BOT")

    # Inicializa el contenido (cuerpo) del menú
    markup = types.InlineKeyboardMarkup(row_width=2)

    # Creamos los botones y las opciones disponibles del menú
    btn_activar_alarma = types.InlineKeyboardButton('🚨 Activar alarma 🟢', callback_data='activar_alarma')
    btn_desactivar_alarma = types.InlineKeyboardButton('🚨 Desactivar alarma 🔴', callback_data='desactivar_alarma')
    btn_llamar_policia = types.InlineKeyboardButton('🚓 Llamar a la policía 🚓', callback_data='llamar_policia')
    btn_monitorear_camara = types.InlineKeyboardButton('📹 Monitorear cámara 📹', callback_data='monitorear_camara')
    btn_bloquear_accesos = types.InlineKeyboardButton('🔒 Bloquear accesos 🔒', callback_data='bloquear_accesos')
    btn_desbloquear_accesos = types.InlineKeyboardButton('🔓 Desbloquear accesos 🔓', callback_data='desbloquear_accesos')
    btn_encender_luces = types.InlineKeyboardButton('💡 Encender luces 🟢', callback_data='encender_luces')
    btn_apagar_luces = types.InlineKeyboardButton('💡 Apagar luces 🔴', callback_data='apagar_luces')
    btn_activar_modo_seguro = types.InlineKeyboardButton('🔒 Activar modo seguro 🟢', callback_data='activar_modo_seguro')
    btn_desactivar_modo_seguro = types.InlineKeyboardButton('🔓 Desactivar modo seguro 🔴', callback_data='desactivar_modo_seguro')
    btn_cerrar = types.InlineKeyboardButton('❌', callback_data='cerrar')

    # Agregamos los botones del menú al markup
    #markup.add(btn_activar_alarma, btn_desactivar_alarma, btn_llamar_policia, btn_monitorear_camara, btn_bloquear_accesos, btn_desbloquear_accesos, btn_cerrar)
    markup.row(btn_encender_luces, btn_apagar_luces)
    markup.row(btn_activar_alarma, btn_desactivar_alarma)
    markup.row(btn_llamar_policia, btn_monitorear_camara)
    markup.row(btn_bloquear_accesos, btn_desbloquear_accesos)
    markup.row(btn_activar_modo_seguro, btn_desactivar_modo_seguro)
    markup.row(btn_cerrar)

    # Enviar mensaje con los botones
    bot.send_message(message.chat.id, "¿Qué deseas realizar? 🤔\n👇 <b>Selecciona una opción:</b> 👇", parse_mode="html", reply_markup=markup)

# Responde al comando /foto
@bot.message_handler(commands=['photo'])
def send_image_command(message):
    # Si el usuario aún no puede enviar mensajes al bot
    if usuario_tiene_que_esperar(message.chat.id):
        # Eliminamos el mensaje enviado por el usuario
        bot.delete_message(message.chat.id, message.message_id)
        # Finalizamos la función
        return
    
    bot.send_chat_action(message.chat.id, "upload_photo")
    img_url = 'https://static.vecteezy.com/system/resources/previews/020/927/449/original/samsung-brand-logo-phone-symbol-name-white-design-south-korean-mobile-illustration-with-black-background-free-vector.jpg'
    img_path = open("./static/bot/samsung.jpg", "rb")
    bot.send_photo(chat_id=message.chat.id, photo=img_path, caption=get_datetime())

# Responde al comando /document
@bot.message_handler(commands=['document'])
def send_document_command(message):
    # Si el usuario aún no puede enviar mensajes al bot
    if usuario_tiene_que_esperar(message.chat.id):
        # Eliminamos el mensaje enviado por el usuario
        bot.delete_message(message.chat.id, message.message_id)
        # Finalizamos la función
        return
    
    bot.send_chat_action(message.chat.id, "upload_document")
    file = open("./static/bot/Sistema de Seguridad con Raspberry - SAMSUNG.pdf", "rb")
    bot.send_document(chat_id=message.chat.id, document=file, caption="Guía de casos de uso del sistema de seguridad de SSafeZoneBot. 📋")

# Responde al comando /help
@bot.message_handler(commands=['help'])
def send_help_command(message):
    # Si el usuario aún no puede enviar mensajes al bot
    if usuario_tiene_que_esperar(message.chat.id):
        # Eliminamos el mensaje enviado por el usuario
        bot.delete_message(message.chat.id, message.message_id)
        # Finalizamos la función
        return
    
    bot.send_chat_action(message.chat.id, "typing")
    bot.reply_to(message, 'Para mas informacion ingrese a https://www.samsung.com/mx/support/ o marque al 800 7267 864 En un horario de Lunes a Domingo de las 8:00 hrs. a las 23:00 hrs.')

# Responde a los mensajes de texto que no son comandos
@bot.message_handler(content_types=["text"])
def send_mensajes_texto(message):
    """ Gestiona los mensajes de texto recibidos """
    # Si el usuario aún no puede enviar mensajes al bot
    if usuario_tiene_que_esperar(message.chat.id):
        # Eliminamos el mensaje enviado por el usuario
        bot.delete_message(message.chat.id, message.message_id)
        # Finalizamos la función
        return

    if message.text.startswith("/"):
        bot.send_chat_action(message.chat.id, "typing")
        mensaje_comando_disponible = bot.send_message(message.chat.id, "🔴 ERROR: Escribe un comando disponible.")
        bot.send_chat_action(message.chat.id, "typing")
        mensaje_elimina = bot.send_message(message.chat.id, "🟡 Eliminando mensajes invalidos: 3⏳⏳⏳", parse_mode="html")
        time.sleep(1)
        bot.edit_message_text("🟡 Eliminando mensajes invalidos: 2⏳⏳⏳", message.chat.id, mensaje_elimina.message_id)
        time.sleep(1)
        bot.edit_message_text("🟡 Eliminando mensajes invalidos: 1⏳⏳⏳", message.chat.id, mensaje_elimina.message_id)
        time.sleep(1)
        bot.delete_message(message.chat.id, message.message_id)
        bot.delete_message(message.chat.id, mensaje_comando_disponible.message_id)
        bot.delete_message(message.chat.id, mensaje_elimina.message_id)
    else:
        bot.send_chat_action(message.chat.id, "typing")
        mensaje_comando_invalido = bot.send_message(message.chat.id, "🔴 ERROR: Este no es un comando valido. Por favor, escribe un comando valido que inicie con '<b>/</b>'.", parse_mode="html")
        bot.send_chat_action(message.chat.id, "typing")
        mensaje_elimina = bot.send_message(message.chat.id, "🟡 Eliminando mensajes invalidos: 3⏳⏳⏳", parse_mode="html")
        time.sleep(1)
        bot.edit_message_text("🟡 Eliminando mensajes invalidos: 2⏳⏳⏳", message.chat.id, mensaje_elimina.message_id)
        time.sleep(1)
        bot.edit_message_text("🟡 Eliminando mensajes invalidos: 1⏳⏳⏳", message.chat.id, mensaje_elimina.message_id)
        time.sleep(1)
        bot.delete_message(message.chat.id, message.message_id)
        bot.delete_message(message.chat.id, mensaje_comando_invalido.message_id)
        bot.delete_message(message.chat.id, mensaje_elimina.message_id)

# Maneja todos los demás tipos de contenido (mensajes).
@bot.message_handler(func=lambda message: True, content_types=['audio', 'photo', 'voice', 'video', 'document', 
                                                               'location', 'contact', 'sticker'])
def send_default_command(message):
    # Si el usuario aún no puede enviar mensajes al bot
    if usuario_tiene_que_esperar(message.chat.id):
        # Eliminamos el mensaje enviado por el usuario
        bot.delete_message(message.chat.id, message.message_id)
        # Finalizamos la función
        return
    
    bot.send_chat_action(message.chat.id, "typing")
    mensaje_default = bot.send_message(message.chat.id, "🔴 ERROR: Por ahora, solo recibo mensajes de texto.\nPor favor, usa los comandos que están disponibles en el menú interactivo.")
    bot.send_chat_action(message.chat.id, "typing")
    mensaje_elimina = bot.send_message(message.chat.id, "🟡 Eliminando mensajes invalidos: 3⏳⏳⏳", parse_mode="html")
    time.sleep(1)
    bot.edit_message_text("🟡 Eliminando mensajes invalidos: 2⏳⏳⏳", message.chat.id, mensaje_elimina.message_id)
    time.sleep(1)
    bot.edit_message_text("🟡 Eliminando mensajes invalidos: 1⏳⏳⏳", message.chat.id, mensaje_elimina.message_id)
    time.sleep(1)
    bot.delete_message(message.chat.id, message.message_id)
    bot.delete_message(message.chat.id, mensaje_default.message_id)
    bot.delete_message(message.chat.id, mensaje_elimina.message_id)

# Responde a cada una de las opciones del menú que son enviadas con /start
@bot.callback_query_handler(func=lambda call:True)
def callback_query(call):
    if call.data == 'activar_alarma':
        bot.answer_callback_query(call.id, "Se ha enviado la petición para que suene la alarma", show_alert=True)
        bot.send_chat_action(call.message.chat.id, "typing")
        respuesta_alarma = bot.send_message(call.message.chat.id, "Intentando establecer conexión con el sistema...")
        time.sleep(3)
        funciones.activarAlarma()
        bot.edit_message_text("Alarma en curso...", call.message.chat.id, respuesta_alarma.message_id)
    elif call.data == 'desactivar_alarma':
        bot.answer_callback_query(call.id, "Se ha enviado la petición para que se desactive la alarma", show_alert=True)
        bot.send_chat_action(call.message.chat.id, "typing")
        respuesta_alarma = bot.send_message(call.message.chat.id, "Intentando establecer conexión con el sistema...")
        time.sleep(3)
        funciones.desactivarAlarma()
        bot.edit_message_text("Alarma desactivada...", call.message.chat.id, respuesta_alarma.message_id)
    elif call.data == 'llamar_policia':
        bot.send_chat_action(call.message.chat.id, "typing")
        bot.answer_callback_query(call.id, "Se ha enviado la petición para que se establezca la llamada con la policia", show_alert=True)
        respuesta_policia = bot.send_message(call.message.chat.id, "Intentando establecer conexión con el sistema...")
        llamada_policia.llamarPoliciaCel()
        time.sleep(3)
        bot.edit_message_text("Llamada en curso...", call.message.chat.id, respuesta_policia.message_id)
    elif call.data == 'monitorear_camara':
        bot.send_chat_action(call.message.chat.id, "typing")
        bot.answer_callback_query(call.id, "Se enviará un link para que se pueda monitorear la cámara", show_alert=True)
        respuesta_camara = bot.send_message(call.message.chat.id, "Intentando establecer conexión con el sistema...")
        funciones.monitorearCamara()
        time.sleep(3)
        bot.edit_message_text('<a href="http://192.168.1.18:81/stream">Haga click aquí para monitorear la cámara</a>', call.message.chat.id, respuesta_camara.message_id, parse_mode="html")
    elif call.data == 'bloquear_accesos':
        bot.send_chat_action(call.message.chat.id, "typing")
        funciones.bloquearPuertas()
        bot.answer_callback_query(call.id, "Puertas y ventanas bloqueadas", show_alert=True)
    elif call.data == 'desbloquear_accesos':
        bot.send_chat_action(call.message.chat.id, "typing")
        funciones.desbloquearPuertas()
        bot.answer_callback_query(call.id, "Puertas y ventanas desbloqueadas", show_alert=True)
    elif call.data == 'encender_luces':
        bot.send_chat_action(call.message.chat.id, "typing")
        bot.answer_callback_query(call.id, "Se ha enviado la petición para que se enciendan las luces", show_alert=True)
        modo_seguro = bot.send_message(call.message.chat.id, "Intentando establecer conexión con el sistema...")
        funciones.encenderLucesDomesticas()
        time.sleep(3)
        bot.edit_message_text("Luces encendidas...", call.message.chat.id, modo_seguro.message_id)
    elif call.data == 'apagar_luces':
        bot.send_chat_action(call.message.chat.id, "typing")
        bot.answer_callback_query(call.id, "Se ha enviado la petición para que se apaguen las luces", show_alert=True)
        modo_seguro = bot.send_message(call.message.chat.id, "Intentando establecer conexión con el sistema...")
        funciones.apagarLucesDomesticas()
        time.sleep(3)
        bot.edit_message_text("Luces apagadas...", call.message.chat.id, modo_seguro.message_id)
    elif call.data == 'activar_modo_seguro':
        bot.send_chat_action(call.message.chat.id, "typing")
        bot.answer_callback_query(call.id, "Se ha enviado la petición para que se establezca el modo seguro", show_alert=True)
        modo_seguro = bot.send_message(call.message.chat.id, "Intentando establecer conexión con el sistema...")
        funciones.activarSensorMovimiento()
        time.sleep(3)
        bot.edit_message_text("Modo seguro activado...", call.message.chat.id, modo_seguro.message_id)
    elif call.data == 'desactivar_modo_seguro':
        bot.send_chat_action(call.message.chat.id, "typing")
        bot.answer_callback_query(call.id, "Se ha enviado la petición para que se desactive el modo seguro", show_alert=True)
        modo_seguro = bot.send_message(call.message.chat.id, "Intentando establecer conexión con el sistema...")
        funciones.desactivarSensorMovimiento()
        time.sleep(3)
        bot.edit_message_text("Modo seguro desactivado...", call.message.chat.id, modo_seguro.message_id)
    elif call.data == 'cerrar':
        bot.delete_message(call.from_user.id, call.message.id)
        return

""" FUNCIONES ADICIONALES """
# Valida si un usuario es administrador
def es_administrador(cid, informacion=True):
    """ Devuelve True si el chat id figura en la tupla 'ADMINISTRADORES'
    y False en caso contrario.
    Si informacion es True y el usuario no es administrador, se informa en el chat. """
    if cid in ADMINISTRADORES:
        return True
    else:
        if informacion:
            print(f'{cid} no esta autorizado')
            bot.send_message(cid, "🔴 ERROR: No estás autorizado", parse_mode="html")
        return False

# Obtiene la fecha y hora actual del sistema
def get_datetime():
    fecha_hora_actual = datetime.now()

    # Formatear la fecha y hora en un formato legible
    formato_fecha_hora = fecha_hora_actual.strftime('%A, %d de %B de %Y a las %H:%M horas')

    return formato_fecha_hora

# Elimina los mensajes que son generados en el registro de un usuario
def eliminar_mensajes_registro(chat_id, message_ids):
    # Asegura que los mensajes a eliminar sean siempre una lista
    if not isinstance(message_ids, list):
        message_ids = [message_ids]

    # Se recorren cada uno de los 'message_id' que hasta ese momento estan almacenados en el diccionario 'chat_mensajes_registro'
    for message_id in message_ids:
        try:
            # Se eliminan los mensajes contenidos en dicha lista
            bot.delete_message(chat_id, message_id)
        except Exception as e:
            print(f"No se pudo eliminar el mensaje {message_id}: {e}")

    del chat_mensajes_registro[chat_id] # Eliminar el mensaje_id de la estructura de datos

# Verifica y elimina mensajes después de cierto tiempo (MODO_LENTO)
def verificar_eliminar_mensajes():
    while True:
        """ Itera sobre cada chat en el diccionario 'chat_mensajes_modo_lento'
        'cid' es el identificador del chat
        'mensajes_pendientes' es la lista de mensajes pendientes para ese chat """
        for cid, mensajes_pendientes in chat_mensajes_modo_lento.items():
            nuevos_mensajes = []
            """ Itera sobre cada mensaje pendiente en el chat actual
            'mensaje_id' es el identificador del mensaje
            'timestamp' es el momento en que se recibió el mensaje """
            for mensaje_id, timestamp in mensajes_pendientes:
                # Calcula la cantidad de segundos transcurridos desde que se recibió el mensaje hasta el momento actual
                segundos_transcurridos = time.time() - timestamp
                """ Eliminación o conservación de mensajes """
                # Se conserva el mensaje y se agrega a la lista 'nuevos_mensajes'
                if segundos_transcurridos < MODO_LENTO:
                    nuevos_mensajes.append((mensaje_id, timestamp))
                # Intenta eliminar los mensajes que se encuentran en 'chat_mensajes_modo_lento'
                else:
                    try:
                        bot.delete_message(cid, mensaje_id)
                    except Exception as e:
                        print(f"No se pudo eliminar el mensaje {mensaje_id}: {e}")
            # Después de procesar todos los mensajes pendientes para un chat, 
            # actualiza la lista de mensajes pendientes para ese chat con la nueva lista 'nuevos_mensajes'
            chat_mensajes_modo_lento[cid] = nuevos_mensajes
        time.sleep(1) # Pausa la iteración del bucle un segundo antes de comenzar una nueva iteración

# Comprueba si ha pasado suficiente tiempo desde el último mensaje del usuario
def usuario_tiene_que_esperar(cid): # Recibe el chat_id
    """ Si aún no ha pasado suficiente tiempo, muestra en el chat el tiempo que resta y devuelve True.
    En caso contrario, guarda el timestamp del usuario y devuelve False. """

    def guardar_timestamp(cid):
        """ Guarda el timestamp actual en el archivo del usuario """
        with open(f'{CARPETA}/{cid}', "w", encoding="utf-8") as file:
            file.write(f'{int(time.time())}')

    # Si no existe el archivo del usuario
    if not os.path.isfile(f'{CARPETA}/{cid}'):
        # Guardamos el timestamp actual
        guardar_timestamp(cid)
        # SI se le permite al usuario mandar mensaje
        return False
    # Leemos el timestamp del último mensaje enviado por el usuario al bot
    with open(f'{CARPETA}/{cid}', "r", encoding="utf-8") as file:
        # Asignamos a 'timestamp' el valor del tiempo
        timestamp = int(file.read())
    # Segundos que han pasado desde el último mensaje
    segundos = int(time.time()) - timestamp
    # Si ya ha pasado el tiempo requerido
    if segundos >= MODO_LENTO:
        # Guardamos el timestamp actual
        guardar_timestamp(cid)
        # SI se le permite al usuario mandar mensaje
        return False
    # Si aún no ha pasado el tiempo requerido
    else:
        bot.send_chat_action(cid, "typing")
        # Enviamos un mensaje al usuario indicando el tiempo que resta
        mensaje_modo_lento = '⚠️ MODO LENTO ACTIVADO\n'
        mensaje_modo_lento+= f'✋ Debes esperar <code>{MODO_LENTO - segundos}</code> segundos para el siguiente mensaje\n'
        mensaje_modo_lento+= f'🟡 Este mensaje será eliminado⌛️⌛️⌛️'
        mensaje_espera = bot.send_message(cid, mensaje_modo_lento, parse_mode="html")

        # Diccionario 'chat_mensajes_modo_lento' donde cada clave 'cid' tiene una lista de tuplas
        # Cada tupla representa un mensaje pendiente en el modo lento con su 'message_id' y su 'tiempo'
        chat_mensajes_modo_lento.setdefault(cid, []).append((mensaje_espera.message_id, time.time()))
        # NO se le permite al usuario mandar mensaje
        return True

# Verifica si los sensores de la raspberry activan sus funciones 
def activar_modo_seguro():
    while True:
        mensaje_modo_seguro = None
        # Si se detecta movimiento en la raspberry
        if funciones.detectar_movimiento():
            for _ in range(2):  # Itera 5 veces, cada iteración representa 10 segundos
                # Se envía una notificación al usuario
                for idx, admin_chat_id in enumerate(ADMINISTRADORES, start=1):
                    print(f'[{idx}] Enviando mensaje a {admin_chat_id}')
                    bot.send_message(admin_chat_id, "🚨🔊 <b>ALERTA</b> 🔊🚨\n<code>¡Se ha detectado movimiento en el hogar!</code>", parse_mode="html") # Axl
                print('\n')

                time.sleep(3)  # Espera 10 segundos entre cada mensaje
            # Inicializa un diccionario para almacenar los message_id
            message_ids = {}

            # Enviamos los mensajes a cada administrador y almacenamos los message_id
            for admin_chat_id in ADMINISTRADORES:
                mensaje_modo_seguro = bot.send_message(admin_chat_id, "⚠️ <b>ACTIVANDO MODO SEGURO</b> ⚠️\n<code>Encendiendo alarmas</code>🚨🚨🚨", parse_mode="html")
                message_ids[admin_chat_id] = mensaje_modo_seguro.message_id
            funciones.activarAlarma()
            #time.sleep(5)
            # Editamos los mensajes utilizando los message_id almacenados
            for admin_chat_id in ADMINISTRADORES:
                bot.edit_message_text("⚠️ <b>ACTIVANDO MODO SEGURO</b> ⚠️\n<code>Bloqueando accesos</code>🔒🔒🔒", admin_chat_id, message_ids[admin_chat_id], parse_mode="html")
            funciones.bloquearPuertas()
            #time.sleep(5)
            for admin_chat_id in ADMINISTRADORES:
                bot.edit_message_text("⚠️ <b>ACTIVANDO MODO SEGURO</b> ⚠️\n<code>Llamando a la policía</code>🚔🚔🚔", admin_chat_id, message_ids[admin_chat_id], parse_mode="html")
            llamada_policia.llamarPoliciaCel()
            #time.sleep(5)
            for admin_chat_id in ADMINISTRADORES:
                bot.edit_message_text("🟢 <b>Modo seguro activado exitosamente</b> 🟢", admin_chat_id, message_ids[admin_chat_id], parse_mode="html")
        else:
            time.sleep(10)  # Espera 10 segundos si no hay movimiento antes de volver a verificar


def recibir_mensajes():
    # Bucle infinito que comprueba si hay nuevos mensajes en el bot
    bot.infinity_polling()

""" MODULO MAIN (PRINCIPAL) DEL PROGRAMA """
def iniciar_bot():
    # Configuramos los comandos disponibles del bot
    bot.set_my_commands([
        BotCommand("/start", "ve las opciones disponibles que tengo para ti"),
        BotCommand("/photo", "toma una foto actual de la cámara instalada"),
        BotCommand("/document", "envia la guía de casos de uso del funcionamiento del sistema"),
        BotCommand("/help", "obten más información de los comandos disponibles")
    ])
    print('Iniciando el bot')
    # bot.polling(none_stop=True)
    # Hilo [1]: Iniciar el hilo del bot y pueda recibir mensajes
    bot_thread = threading.Thread(name="bot_thread", target=recibir_mensajes)
    bot_thread.start()
    # Hilo [2]: Iniciar el hilo de verificación y eliminación de mensajes (MODO_LENTO)
    verify_messages_thread = threading.Thread(name="verify_messages_thread", target=verificar_eliminar_mensajes)
    verify_messages_thread.start()
    # Hilo [3]: Iniciar el hilo de verificación de movimiento de la RASPBERRY
    verify_movimiento_raspberry_thread = threading.Thread(name="movimiento_thread", target=activar_modo_seguro)
    verify_movimiento_raspberry_thread.start()
    print('Bot iniciado')

    # Se notifica al usuario que el bot se encuentra en funcionamiento
    bot.send_message(AXL_CHAT_ID, f'🟢 ¡En estos momentos me encuentro disponible para ti!\nAtentamente: <b>{BOT_USERNAME}</b>', parse_mode="html")
    bot.send_message(ANGEL_CHAT_ID, f'🟢 ¡En estos momentos me encuentro disponible para ti!\nAtentamente: <b>{BOT_USERNAME}</b>', parse_mode="html")
    bot.send_message(DANIEL_CHAT_ID, f'🟢 ¡En estos momentos me encuentro disponible para ti!\nAtentamente: <b>{BOT_USERNAME}</b>', parse_mode="html")