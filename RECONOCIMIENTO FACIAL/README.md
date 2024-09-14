## 👩 Reconocimiento Facial 👨 | Python - OpenCV

Para una descripción más detallada sobre el proceso de construcción de los programas, por favor dirígete a:

Mi blog: https://omes-va.com/reconocimiento-facial-python-opencv/

Video: https://youtu.be/cZkpaL36fW4

En capturandoRostros.py vamos a capturar las personas que deseamos reconocer. En entrenandoRF.py entrenamos el reconocedor de rostros con:
EigenFaces, FisherFaces y LBPH. Finalmente podremos probar cada uno de los métodos (por separado) en ReconocimientoFacial.py

pip install opencv-contrib-python

Detección de rostros con Haarcascade:
es un conjunto de clasificadores utilizados para la detección de objetos en imágenes o videos, basados en el algoritmo de cascada de Haar, una técnica de aprendizaje automático, utiliza archivos XML preentrenados para la detección de varios objetos

se hace un resize y se trabaja con la escala de grises


1. Generar video
2. capturandoRostros
3. entrenandoRF
4. reconocimiento facial