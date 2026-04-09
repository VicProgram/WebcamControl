WebcamControl
Documentación técnica completa
Control, presets y captura de webcam en Windows

1. Visión general del proyecto

WebcamControl es una aplicación de escritorio escrita en Python que te permite controlar los parámetros de imagen de tu webcam, guardar configuraciones como presets, ver la imagen en tiempo real y tomar fotos directamente desde la interfaz.

Archivos del proyecto:

ui_webcam.py: Interfaz gráfica principal (el programa que usas).


main.py: Versión de consola para uso rápido por terminal.


presets.json: Base de datos de presets guardados (se crea automáticamente).


Fotos/: Carpeta donde se guardan las fotos (se crea automáticamente).


.venv/: Entorno virtual de Python con las dependencias instaladas.


.vscode/settings.json: Configuración de VSCode para activar el entorno solo.

💡 El único archivo que necesitas ejecutar es ui_webcam.py. El resto se gestiona solo.

2. Dependencias y tecnologías usadas
El programa usa exclusivamente librerías estándar de Python más OpenCV. No necesita nada externo una vez instalado el entorno.

Librería,Módulo,Para qué sirve
opencv-python,cv2,"Acceder a la cámara, leer frames y guardar imágenes."
tkinter,"tk, ttk, messagebox, filedialog",Construir la interfaz gráfica de ventanas.
threading,(estándar Python),Ejecutar la captura de video en un hilo paralelo.
json,(estándar Python),Leer y escribir el archivo de presets.
os,(estándar Python),Gestionar rutas de archivos y carpetas.
datetime,(estándar Python),Generar nombres únicos con marca de tiempo para las fotos.
