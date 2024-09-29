import cv2
import os
from dotenv import load_dotenv

# Cargar las variables desde el archivo .env
load_dotenv()

PATH = os.getenv('DATA_PATH')
dataPath = os.path.join(PATH, 'Data') 
model_path = os.path.join(PATH, 'Data', 'Modelo', 'modeloLBPHFace.xml')

face_recognizer = cv2.face.LBPHFaceRecognizer_create()
face_recognizer.read(model_path)

# Crear un diccionario para mapear etiquetas a nombres de usuario
user_dict = {}
label = 0

# Recorrer la estructura de directorios para llenar el diccionario
for hogar_id in os.listdir(dataPath):
    hogar_path = os.path.join(dataPath, hogar_id)
    if os.path.isdir(hogar_path):
        for usuario in os.listdir(hogar_path):
            user_dict[label] = usuario
            label += 1

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
#cap = cv2.VideoCapture('Video.mp4')
faceClassif = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

while True:
    ret, frame = cap.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    auxFrame = gray.copy()

    faces = faceClassif.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        rostro = auxFrame[y:y + h, x:x + w]
        rostro = cv2.resize(rostro, (150, 150), interpolation=cv2.INTER_CUBIC)
        result = face_recognizer.predict(rostro)

        if result[1] < 65:  # Ajusta el umbral según tu modelo
            user_name = user_dict.get(result[0], "Desconocido")
            cv2.putText(frame, user_name, (x, y - 25), 2, 1.1, (0, 255, 0), 1, cv2.LINE_AA)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        else:
            cv2.putText(frame, 'Desconocido', (x, y - 20), 2, 0.8, (0, 0, 255), 1, cv2.LINE_AA)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    cv2.imshow('frame', frame)
    k = cv2.waitKey(1)
    if k == 27:  # Presionar ESC para salir
        break

cap.release()
cv2.destroyAllWindows()
