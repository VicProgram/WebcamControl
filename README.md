
# **\. Visión general del proyecto**

WebcamControl es una aplicación de escritorio escrita en Python que te permite controlar los parámetros de imagen de tu webcam, guardar configuraciones como presets, ver la imagen en tiempo real y tomar fotos directamente desde la interfaz.

**Archivos del proyecto:**

* ui\_webcam.py — Interfaz gráfica principal (el programa que usas)

* main.py — Versión de consola para uso rápido por terminal

* presets.json — Base de datos de presets guardados (se crea automáticamente)

* Fotos/ — Carpeta donde se guardan las fotos (se crea automáticamente)

* .venv/ — Entorno virtual de Python con las dependencias instaladas

* .vscode/settings.json — Configuración de VSCode para activar el entorno solo

| El único archivo que necesitas ejecutar es ui\_webcam.py. El resto se gestiona solo. |
| :---- |

# **\. Dependencias y tecnologías usadas**

El programa usa exclusivamente librerías estándar de Python más OpenCV. No necesita nada externo una vez instalado el entorno.

| Librería | Módulo | Para qué sirve |
| :---- | :---- | :---- |
| opencv-python | cv2 | Acceder a la cámara, leer frames y guardar imágenes |
| tkinter | tk, ttk, messagebox, filedialog | Construir la interfaz gráfica de ventanas |
| threading | (estándar Python) | Ejecutar la captura de video en un hilo paralelo |
| json | (estándar Python) | Leer y escribir el archivo de presets |
| os | (estándar Python) | Gestionar rutas de archivos y carpetas |
| datetime | (estándar Python) | Generar nombres únicos con marca de tiempo para las fotos |

# **\. Estructura del código**

El código está organizado en una clase principal y dos diccionarios de constantes globales.

## ** Constantes globales (fuera de la clase)**

### **PROPS\_PRESET**

Diccionario con los 19 parámetros de cámara que se guardan en cada preset. La clave es el nombre legible y el valor es la constante numérica de OpenCV.

|   |
| :---- |
| PROPS\_PRESET \= { |
|     "Brillo":     cv2.CAP\_PROP\_BRIGHTNESS, |
|     "Contraste":  cv2.CAP\_PROP\_CONTRAST, |
|     "Exposición": cv2.CAP\_PROP\_EXPOSURE, |
|     \# ... 16 más |
| } |
|   |

| ¿Por qué fuera de la clase? Para que sea una constante global reutilizable tanto por la UI como por el sistema de guardado, sin necesidad de pasar self por todos lados. |
| :---- |

### **PROPS\_UI**

Subconjunto de solo 5 parámetros que se muestran en pantalla. Mantener la UI limpia y no colapsar la ventana con los 19 parámetros completos.

## ** La clase WebcamApp**

Toda la lógica vive dentro de esta clase. Se instancia una sola vez al arrancar el programa.

| Método | Qué hace |
| :---- | :---- |
| \_\_init\_\_ | Inicializa la cámara, define variables de estado y llama a create\_widgets() |
| create\_widgets() | Construye toda la interfaz gráfica: labels, botones, separadores y secciones |
| actualizar\_labels() | Lee los 5 valores de PROPS\_UI de la cámara y los muestra en pantalla |
| abrir\_panel\_nativo() | Abre el cuadro de propiedades DirectShow de Windows para ajustes avanzados |
| toggle\_preview() | Activa o para el preview: lanza el hilo secundario y el loop de display |
| \_loop\_preview() | Hilo secundario: captura frames continuamente y los guarda en self.\_frame\_actual |
| \_actualizar\_preview() | Hilo principal (via root.after): muestra el frame en la ventana de OpenCV |
| elegir\_carpeta() | Abre el selector de carpetas de Windows y actualiza self.carpeta\_fotos |
| tomar\_foto() | Guarda el frame actual (o captura uno nuevo) como .jpg con timestamp |
| guardar() | Lee los 19 valores de PROPS\_PRESET y los escribe en presets.json |
| cargar() | Lee presets.json y aplica cada valor a la cámara, omitiendo los no soportados (-1) |

# **\. Cómo funciona el preview en tiempo real**

El preview fue el reto más delicado del proyecto. En Windows, OpenCV no puede mostrar imágenes desde un hilo secundario de forma fiable (conflicto con DirectShow). La solución usa dos hilos con responsabilidades separadas:

| Regla de oro: solo el hilo principal puede actualizar la UI. El hilo secundario solo toca datos. |
| :---- |

## **Hilo secundario — \_loop\_preview()**

Su único trabajo es leer frames de la cámara lo más rápido posible y guardar el último en self.\_frame\_actual. No muestra nada.

|   |
| :---- |
| def \_loop\_preview(self): |
|     while self.preview\_activo: |
|         ret, frame \= self.cap.read()   \# lee un frame de la cámara |
|         if ret: |
|             self.\_frame\_actual \= frame  \# guarda el último frame |
|         if cv2.waitKey(1) & 0xFF \== ord('q'): |
|             self.preview\_activo \= False |
|             break |
|   |

## **Hilo principal — \_actualizar\_preview()**

Usa root.after(30, ...) para programarse a sí mismo cada 30 ms (\~33 fps). Cada vez que se ejecuta, coge el frame guardado y lo muestra con cv2.imshow(). Como corre en el hilo principal de Tkinter, no hay conflictos con Windows.

|   |
| :---- |
| def \_actualizar\_preview(self): |
|     if self.preview\_activo: |
|         if self.\_frame\_actual is not None: |
|             cv2.imshow('Preview Webcam', self.\_frame\_actual) |
|         self.root.after(30, self.\_actualizar\_preview)  \# se reprograma solo |
|     else: |
|         cv2.destroyAllWindows()  \# cierra la ventana al parar |
|   |

| root.after(30, función) es como un setTimeout en JavaScript: ejecuta la función después de 30 ms en el hilo principal. Es la forma correcta de hacer loops en Tkinter. |
| :---- |

# **\. Sistema de presets**

## **Estructura del archivo presets.json**

Cada preset es una clave en el JSON con los 19 valores numéricos que la cámara reportó en ese momento:

|   |
| :---- |
| { |
|     "Streaming": { |
|         "Brillo": 128.0, |
|         "Contraste": 32.0, |
|         "Saturación": 80.0, |
|         "Exposición": \-6.0, |
|         "Auto\_Exposicion": 0.25, |
|         "Auto\_Foco": 0.0, |
|         "Foco": 0.0, |
|         ... |
|     }, |
|     "Reunión": { |
|         ... |
|     } |
| } |
|   |

## **¿Por qué se guardan los \-1?**

Cuando una propiedad no está soportada por tu cámara, OpenCV devuelve \-1. Se guardan en el JSON para tener un registro completo, pero al **cargar** un preset el código los salta automáticamente:

|   |
| :---- |
| for nombre\_prop, val in presets\[nombre\].items(): |
|     if val \== \-1: |
|         omitidos \+= 1 |
|         continue          \# esta propiedad no la soporta la cámara |
|     self.cap.set(PROPS\_PRESET\[nombre\_prop\], val)   \# aplicamos el valor |
|     aplicados \+= 1 |
|   |

| Esto hace que los presets sean portables entre cámaras: si cargas un preset en otra webcam, simplemente se omiten las propiedades que esa cámara no tenga. |
| :---- |

# **\. Captura de fotos**

El botón 📷 Tomar Foto funciona en dos modos dependiendo de si el preview está activo:

* Con preview activo: usa self.\_frame\_actual.copy() — el frame que ya está en memoria. Es instantáneo y coherente con lo que ves en pantalla.

* Sin preview activo: llama a self.cap.read() para capturar un frame en ese momento.

Las fotos se guardan con timestamp para evitar colisiones de nombre:

|   |
| :---- |
| timestamp \= datetime.now().strftime('%Y%m%d\_%H%M%S') |
| nombre\_archivo \= f'foto\_{timestamp}.jpg' |
| \# Resultado: foto\_20260409\_143022.jpg |
|   |

La carpeta por defecto es Fotos/ dentro del directorio del proyecto. El botón **Cambiar** abre el explorador de Windows para elegir cualquier otra ruta.

# **\. Compatibilidad con webcams**

El programa funciona con cualquier webcam estándar en Windows. La clave está en el flag cv2.CAP\_DSHOW:

|   |
| :---- |
| self.cap \= cv2.VideoCapture(0, cv2.CAP\_DSHOW) |
| \#                          ^     ^ |
| \#                          |     DirectShow: protocolo estándar de Windows |
| \#                          índice de cámara (0 \= primera, 1 \= segunda...) |
|   |

| Parámetro | Descripción | Cuándo usarlo |
| :---- | :---- | :---- |
| Brillo | Luminosidad general de la imagen | Entornos oscuros o demasiado brillantes |
| Contraste | Diferencia entre zonas claras y oscuras | Mejorar legibilidad en fondos planos |
| Saturación | Intensidad de los colores | Colores más vivos o aspecto neutro/gris |
| Exposición | Tiempo que el sensor recibe luz | Entornos con poca luz (valores negativos \= más oscuro) |
| Ganancia | Amplificación de la señal del sensor | Alternativa a la exposición, más ruido |
| Nitidez | Realce de bordes | Mejorar definición de texto o detalles |
| Gamma | Curva de luminosidad | Corregir aspecto lavado o demasiado oscuro |
| Temperatura de color | Tono cálido/frío de los blancos | Ajustar balance de blancos manualmente |
| Auto\_Exposicion | 0.25 \= manual, 0.75 \= auto | Fijar en manual para que los presets funcionen bien |
| Auto\_Foco | 0 \= manual, 1 \= automático | Desactivar para que el foco guardado se respete |

| Importante: para que los presets funcionen correctamente, Auto\_Exposicion y Auto\_Foco deben estar en modo manual (0.25 y 0 respectivamente). El programa los fija así al arrancar. |
| :---- |

# **8\. Entorno virtual y VSCode**

El proyecto usa un entorno virtual (.venv) para aislar las dependencias de Python del sistema. Esto evita conflictos entre proyectos y asegura que siempre tengas la versión correcta de cada librería.

## **Comandos esenciales**

|   |
| :---- |
| \# Activar el entorno manualmente (PowerShell) |
| .venv\\Scripts\\Activate.ps1 |
|   |
| \# Instalar dependencias |
| pip install opencv-python |
|   |
| \# Ejecutar el programa |
| python ui\_webcam.py |
|   |
| \# Ver qué hay instalado |
| pip list |
|   |

## **Activación automática en VSCode**

El archivo .vscode/settings.json configura VSCode para activar el entorno cada vez que abres un terminal integrado. Sin esto, podrías instalar librerías en el Python del sistema sin darte cuenta.

|   |
| :---- |
| { |
|     "python.defaultInterpreterPath": "${workspaceFolder}\\\\.venv\\\\Scripts\\\\python.exe", |
|     "terminal.integrated.profiles.windows": { |
|         "PowerShell": { |
|             "source": "PowerShell", |
|             "args": \["-NoExit", "-Command", |
|                      "& '${workspaceFolder}\\\\.venv\\\\Scripts\\\\Activate.ps1'"\] |
|         } |
|     } |
| } |
|   |

# **\. Crear un ejecutable .exe para Windows**

Con PyInstaller puedes empaquetar todo el proyecto en un único .exe que funciona en cualquier Windows sin necesidad de tener Python instalado.

## **Pasos**

* Asegúrate de tener el entorno virtual activo (verás (.venv) en el terminal)

* Instala PyInstaller:

|   |
| :---- |
| pip install pyinstaller |
|   |

* Genera el ejecutable desde la carpeta del proyecto:

|   |
| :---- |
| pyinstaller \--onefile \--noconsole ui\_webcam.py |
|   |
| \# \--onefile   : todo en un solo .exe (más fácil de distribuir) |
| \# \--noconsole : no aparece la ventana negra de terminal al abrir |
|   |

* El .exe aparece en la carpeta dist/ dentro de tu proyecto

| Resultado: F:\\WebcamControl\\dist\\ui\_webcam.exe — cópialo a cualquier Windows y funciona. No necesita Python, ni librerías, ni nada instalado. |
| :---- |

## **Notas sobre el ejecutable**

* La primera vez que arranque puede tardar unos segundos mientras se descomprime en memoria.

* Si cambias el código necesitas volver a ejecutar el comando de PyInstaller.

* Las carpetas build/ y dist/ que genera PyInstaller no necesitas subirlas a ningún lado, son temporales.

* El presets.json y la carpeta Fotos/ se crean junto al .exe cuando lo uses por primera vez.

# **\. Referencia rápida de uso**

| Acción | Cómo hacerlo |
| :---- | :---- |
| Ver valores actuales | Botón 'Leer Valores Actuales' |
| Ver la cámara en vivo | Botón '▶ Iniciar Preview' → se abre ventana OpenCV |
| Parar el preview | Botón '⏹ Detener Preview' o pulsar Q en la ventana de video |
| Ajuste avanzado nativo | Botón 'Abrir Configuración Avanzada' → panel de Windows |
| Guardar configuración | Escribe un nombre en el campo y pulsa 'Guardar Preset' |
| Cargar configuración | Escribe el nombre exacto del preset y pulsa 'Cargar Preset' |
| Cambiar carpeta de fotos | Botón 'Cambiar' junto a la ruta de carpeta |
| Tomar foto | Botón '📷 Tomar Foto' (con o sin preview activo) |
| Cambiar cámara | Cambiar el 0 por 1, 2... en cv2.VideoCapture(0, ...) |

