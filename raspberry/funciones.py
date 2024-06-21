# Aquí van las librerías de gpiozero
import logging
from . import llamada_policia

# Configurar el logging para este módulo
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Encender luces domésticas del hogar
def encenderLucesDomesticas():
    print("encenderLucesDomesticas funcionando")
    logger.debug("encenderLucesDomesticas funcionando")
    
# Apagar luces domésticas del hogar
def apagarLucesDomesticas():
    print("apagarLucesDomesticas funcionando")
    logger.debug("apagarLucesDomesticas funcionando")
    
# Activar la alarma
def activarAlarma():
    print("activarAlarma funcionando")
    logger.debug("activarAlarma funcionando")
    
# Desactivar la alarma
def desactivarAlarma():
    print("desactivarAlarma funcionando")
    logger.debug("desactivarAlarma funcionando")

# Cerrar el servo (posición a 180 grados) 
def bloquearPuertas():
    print("bloquearPuertas funcionando")
    logger.debug("bloquearPuertas funcionando")
    
# Abrir el servo (posición a 0 grados) 
def desbloquearPuertas():
    print("desbloquearPuertas funcionando")
    logger.debug("desbloquearPuertas funcionando")
    
# Enlace para llamar a la policía local (911)
def llamarPolicia():
    llamada_policia.llamarPoliciaCel()
    print("llamarPolicia funcionando")
    logger.debug("llamarPolicia funcionando")
    
# Iniciar grabación del monitoreo de la cámara en vivo
def grabarContenido():
    print("grabarContenido funcionando")
    logger.debug("grabarContenido funcionando")