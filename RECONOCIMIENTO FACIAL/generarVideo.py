import cv2
import time

# Configuración de la captura de video
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Configuración para guardar el video en formato .mp4
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
output = cv2.VideoWriter('lalo-prueba.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 20.0, (frame_width, frame_height))

start_time = time.time()  # Iniciar el tiempo

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Mostrar el video en tiempo real
    cv2.imshow('frame', frame)

    # Guardar el cuadro en el archivo de video
    output.write(frame)

    # Verificar si han pasado 25 segundos
    if time.time() - start_time > 20:
        print("Grabación completada.")
        break

    # Presionar 'Esc' para salir manualmente
    if cv2.waitKey(1) == 27:
        break

# Liberar la captura y cerrar ventanas
cap.release()
output.release()
cv2.destroyAllWindows()
