
# **\. Visión general del proyecto**

WebcamControl es una aplicación de escritorio escrita en Python que te permite controlar los parámetros de imagen de tu webcam, guardar configuraciones como presets, ver la imagen en tiempo real y tomar fotos directamente desde la interfaz.

**Archivos del proyecto:**

* webcam\_control.py — Código principal (interfaz + lógica, todo en uno)

* presets.json — Base de datos de presets guardados (se crea automáticamente la primera vez que guardas uno)

* Fotos/ — Carpeta donde se guardan las fotos y videos (se crea automáticamente)

* pyproject.toml — Configuración del proyecto y del linter (ruff)

* Makefile — Automatización: crear el entorno virtual, instalar dependencias, ejecutar, lint

| El único archivo que necesitas ejecutar es webcam\_control.py. El resto se gestiona solo. |
| :---- |

# **\. Dependencias y tecnologías usadas**

El programa usa Python 3.10+ con las siguientes librerías:

| Librería | Módulo | Para qué sirve |
| :---- | :---- | :---- |
| opencv-python | cv2 | Acceder a la cámara, leer frames, guardar imágenes y video |
| customtkinter | ctk | Interfaz gráfica moderna con tema oscuro |
| threading | (estándar Python) | Ejecutar la captura de video en un hilo paralelo |
| json | (estándar Python) | Leer y escribir el archivo de presets |
| os | (estándar Python) | Gestionar rutas de archivos y carpetas |
| datetime | (estándar Python) | Generar nombres únicos con marca de tiempo para fotos y videos |
| ruff | (dev) | Linter y formateador de código |

# **\. Estructura del código**

El código está organizado en una clase principal y dos diccionarios de constantes globales, todo en un único archivo `webcam_control.py`.

## ** Constantes globales (fuera de la clase)**

### **PROPS\_PRESET**

Diccionario con los 19 parámetros de cámara que se guardan en cada preset. La clave es el nombre legible y el valor es la constante numérica de OpenCV.

|   |
| :---- |
| PROPS\_PRESET \= { |
|     "Brillo":     cv2.CAP\_PROP\_BRIGHTNESS, |
|     "Contraste":  cv2.CAP\_PROP\_CONTRAST, |
|     "Saturacion": cv2.CAP\_PROP\_SATURATION, |
|     \# ... 16 más |
| } |
|   |

| ¿Por qué fuera de la clase? Para que sea una constante global reutilizable tanto por la UI como por el sistema de guardado, sin necesidad de pasar self por todos lados. |
| :---- |

### **PROPS\_UI**

Subconjunto de solo 5 parámetros que se muestran en pantalla (Brillo, Contraste, Saturacion, Exposicion, Ganancia). Mantener la UI limpia y no colapsar la ventana con los 19 parámetros completos.

## ** La clase WebcamApp**

Toda la lógica vive dentro de esta clase. Se instancia una sola vez al arrancar el programa.

| Método | Qué hace |
| :---- | :---- |
| \_\_init\_\_ | Inicializa la cámara, define variables de estado y construye la UI |
| \_build\_ui() | Construye toda la interfaz gráfica: labels, botones, separadores y secciones |
| actualizar\_labels() | Lee los 5 valores de PROPS\_UI de la cámara y los muestra en pantalla |
| abrir\_panel\_nativo() | Abre el cuadro de propiedades DirectShow de Windows para ajustes avanzados |
| toggle\_preview() | Activa o para el preview: lanza el hilo secundario y el loop de display |
| \_loop\_preview() | Hilo secundario: captura frames continuamente y los guarda en self.\_frame\_actual |
| \_actualizar\_preview() | Hilo principal (via self.after): muestra el frame en la ventana de OpenCV |
| elegir\_carpeta() | Abre el selector de carpetas y actualiza self.carpeta\_fotos |
| tomar\_foto() | Guarda el frame actual (o captura uno nuevo) como .jpg con timestamp |
| guardar() | Lee los 19 valores de PROPS\_PRESET y los escribe en presets.json |
| \_cargar\_preset(nombre) | Lee presets.json y aplica cada valor a la cámara, omitiendo los no soportados (-1) |
| \_borrar\_preset(nombre) | Elimina un preset del archivo después de confirmar |

# **\. Cómo funciona el preview en tiempo real**

El preview fue el reto más delicado del proyecto. En Windows, OpenCV no puede mostrar imágenes desde un hilo secundario de forma fiable (conflicto con DirectShow). La solución usa dos hilos con responsabilidades separadas:

| Regla de oro: solo el hilo principal puede actualizar la UI. El hilo secundario solo toca datos. |
| :---- |

## **Hilo secundario — \_loop\_preview()**

Su único trabajo es leer frames de la cámara lo más rápido posible y guardar el último en self.\_frame\_actual. No muestra nada, no llama a cv2.waitKey().

|   |
| :---- |
| def \_loop\_preview(self): |
|     while self.preview\_activo: |
|         ret, frame \= self.cap.read()   \# lee un frame de la cámara |
|         if ret: |
|             with self.\_lock\_frame: |
|                 self.\_frame\_actual \= frame  \# guarda el último frame bajo lock |
|   |

## **Hilo principal — \_actualizar\_preview()**

Usa self.after(30, ...) para programarse a sí mismo cada 30 ms (\~33 fps). Cada vez que se ejecuta, coge el frame guardado y lo muestra con cv2.imshow(). Como corre en el hilo principal de Tkinter, no hay conflictos con Windows. También procesa cv2.waitKey(1) aquí para detectar la tecla 'q'.

|   |
| :---- |
| def \_actualizar\_preview(self): |
|     if self.preview\_activo: |
|         with self.\_lock\_frame: |
|             frame \= self.\_frame\_actual.copy() if self.\_frame\_actual else None |
|         if frame is not None: |
|             cv2.imshow('Webcam Control Live View', frame) |
|         if cv2.waitKey(1) & 0xFF \== ord('q'): |
|             self.toggle\_preview() |
|             return |
|         self.after(30, self.\_actualizar\_preview) |
|     else: |
|         cv2.destroyAllWindows() |
|   |

| self.after(30, función) es como un setTimeout en JavaScript: ejecuta la función después de 30 ms en el hilo principal. Es la forma correcta de hacer loops en Tkinter. |
| :---- |

# **\. Sistema de presets**

## **Estructura del archivo presets.json**

Cada preset es una clave en el JSON con los 19 valores numéricos que la cámara reportó en ese momento:

|   |
| :---- |
| { |
|     "Normal": { |
|         "Brillo": 0.0, |
|         "Contraste": 15.0, |
|         "Saturacion": 10.0, |
|         "Exposicion": \-4.0, |
|         "Ganancia": 32.0, |
|         "Foco": \-1.0,          \# no soportado por esta cámara |
|         ... |
|     }, |
|     "Vibrant\_Pro": { |
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

# **\. Captura de fotos y video**

## **Fotos**

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

La carpeta por defecto es Fotos/ dentro del directorio del proyecto. El botón **Cambiar** abre el explorador para elegir cualquier otra ruta.

## **Video**

El botón ⏺ Iniciar grabación graba video en formato MP4. Requiere que el preview esté activo. Se detiene con el mismo botón y guarda el archivo en la misma carpeta de fotos.

# **\. Compatibilidad con webcams**

El programa funciona con cualquier webcam estándar en Windows y Linux. En Windows usa el backend DirectShow (cv2.CAP\_DSHOW); en Linux usa el backend por defecto (cv2.CAP\_ANY).

|   |
| :---- |
| backend \= cv2.CAP\_DSHOW if IS\_WINDOWS else cv2.CAP\_ANY |
| self.cap \= cv2.VideoCapture(0, backend) |
|   |

| Parámetro | Descripción | Cuándo usarlo |
| :---- | :---- | :---- |
| Brillo | Luminosidad general de la imagen | Entornos oscuros o demasiado brillantes |
| Contraste | Diferencia entre zonas claras y oscuras | Mejorar legibilidad en fondos planos |
| Saturacion | Intensidad de los colores | Colores más vivos o aspecto neutro/gris |
| Exposicion | Tiempo que el sensor recibe luz | Entornos con poca luz (valores negativos \= más oscuro) |
| Ganancia | Amplificación de la señal del sensor | Alternativa a la exposición, más ruido |
| Nitidez | Realce de bordes | Mejorar definición de texto o detalles |
| Gamma | Curva de luminosidad | Corregir aspecto lavado o demasiado oscuro |
| Temperatura de color | Tono cálido/frío de los blancos | Ajustar balance de blancos manualmente |
| Auto\_Exposicion | 0.25 \= manual, 0.75 \= auto | Fijar en manual para que los presets funcionen bien |
| Auto\_Foco | 0 \= manual, 1 \= automático | Desactivar para que el foco guardado se respete |

| Importante: para que los presets funcionen correctamente, Auto\_Exposicion y Auto\_Foco deben estar en modo manual (0.25 y 0 respectivamente). El programa los fija así al arrancar. |
| :---- |

# **8\. Primeros pasos**

## **Usando Make (recomendado)**

|   |
| :---- |
| make install   \# crea el entorno virtual e instala dependencias |
| make run       \# ejecuta la aplicación |
| make lint      \# ejecuta el linter (ruff) |
| make fmt       \# formatea el código automáticamente |
| make clean     \# elimina el entorno virtual y archivos temporales |
|   |

## **Usando Make (Windows)**

|   |
| :---- |
| make install |
| make run |
|   |

## **Manual (sin Make)**

|   |
| :---- |
| python3 \-m venv venv |
| source venv/bin/activate  \# Linux/macOS |
| .\\venv\\Scripts\\Activate.ps1  \# Windows |
| pip install \-r requirements.txt |
| python webcam\_control.py |
|   |

# **\. Crear un ejecutable para Windows**

Con PyInstaller puedes empaquetar todo el proyecto en un único .exe que funciona en cualquier Windows sin necesidad de tener Python instalado.

## **Pasos**

* Asegúrate de tener el entorno virtual activo (verás (venv) en el terminal)

* Instala PyInstaller:

|   |
| :---- |
| pip install pyinstaller |
|   |

* Genera el ejecutable desde la carpeta del proyecto:

|   |
| :---- |
| pyinstaller \--onefile \--noconsole webcam\_control.py |
|   |
| \# \--onefile   : todo en un solo .exe (más fácil de distribuir) |
| \# \--noconsole : no aparece la ventana negra de terminal al abrir |
|   |

* El .exe aparece en la carpeta dist/ dentro de tu proyecto

| Resultado: dist\\webcam\_control.exe — cópialo a cualquier Windows y funciona. No necesita Python, ni librerías, ni nada instalado. |
| :---- |

## **Notas sobre el ejecutable**

* La primera vez que arranque puede tardar unos segundos mientras se descomprime en memoria.

* Si cambias el código necesitas volver a ejecutar el comando de PyInstaller.

* Las carpetas build/ y dist/ que genera PyInstaller no necesitas subirlas a ningún lado, son temporales.

* El presets.json y la carpeta Fotos/ se crean junto al .exe cuando lo uses por primera vez.

# **\. Referencia rápida de uso**

| Acción | Cómo hacerlo |
| :---- | :---- |
| Ver valores actuales | Botón 'Leer valores' |
| Ver la cámara en vivo | Botón '▶ Iniciar preview' → se abre ventana OpenCV |
| Parar el preview | Botón '⏹ Detener preview' o pulsar Q en la ventana de video |
| Ajuste avanzado nativo (Windows) | Botón 'Abrir configuración avanzada' → panel de la cámara |
| Guardar preset | Escribe un nombre y pulsa '💾 Guardar preset actual' |
| Cargar preset | Haz clic en el nombre del preset en la lista |
| Borrar preset | Haz clic en el botón × junto al preset |
| Cambiar carpeta de fotos | Botón 'Cambiar' junto a la ruta de carpeta |
| Tomar foto | Botón '📷 Tomar foto' (con o sin preview activo) |
| Grabar video | Botón '⏺ Iniciar grabación' (requiere preview activo) |
| Cambiar cámara | Cambiar el 0 por 1, 2... en cv2.VideoCapture(0, ...) dentro del código |
