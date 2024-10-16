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
    
# Cerrar el servo uno
def bloquearPuertaUno():
    print("bloquearPuertaUno funcionando")
    logger.debug("bloquearPuertaUno funcionando")
    
# Cerrar el servo dos
def bloquearPuertaDos():
    print("bloquearPuertaDos funcionando")
    logger.debug("bloquearPuertaDos funcionando")
    
# Cerrar el servo tres
def bloquearPuertaTres():
    print("bloquearPuertaTres funcionando")
    logger.debug("bloquearPuertaTres funcionando")
    
# Cerrar el servo cuatro
def bloquearPuertaCuatro():
    print("bloquearPuertaCuatro funcionando")
    logger.debug("bloquearPuertaCuatro funcionando")
    
# Abrir el servo (posición a 0 grados) 
def desbloquearPuertas():
    print("desbloquearPuertas funcionando")
    logger.debug("desbloquearPuertas funcionando")
    
# Abrir el servo uno
def desbloquearPuertaUno():
    print("desbloquearPuertaUno funcionando")
    logger.debug("desbloquearPuertaUno funcionando")
    
# Abrir el servo dos
def desbloquearPuertaDos():
    print("desbloquearPuertaDos funcionando")
    logger.debug("desbloquearPuertaDos funcionando")
    
# Abrir el servo tres
def desbloquearPuertaTres():
    print("desbloquearPuertaTres funcionando")
    logger.debug("desbloquearPuertaTres funcionando")
    
# Abrir el servo cuatro
def desbloquearPuertaCuatro():
    print("desbloquearPuertaCuatro funcionando")
    logger.debug("desbloquearPuertaCuatro funcionando")
    
# Enlace para llamar a la policía local (911)
def llamarPolicia():
    llamada_policia.llamarPoliciaCel()
    print("llamarPolicia funcionando")
    logger.debug("llamarPolicia funcionando")
    
# Activar modo seguro
def activarSensorMovimiento():
    print("activarSensorMovimiento funcionando")
    logger.debug("activarSensorMovimiento funcionando")
    
# Desactivar modo seguro
def desactivarSensorMovimiento():
    print("DesactivarSensorMovimiento funcionando")
    logger.debug("DesactivarSensorMovimiento funcionando")
    
# Iniciar grabación del monitoreo de la cámara en vivo
def grabarContenido():
    print("grabarContenido funcionando")
    logger.debug("grabarContenido funcionando")