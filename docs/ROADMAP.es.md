# Mejoras para WebcamControl

## Rendimiento

### 1. Reutilizar CTkImage en lugar de crear uno nuevo por frame
Cada frame se crea un nuevo `CTkImage` desde cero (PIL + CTk allocation). Mejor crear el `CTkImage` una vez en `_build_ui` y actualizar solo sus imágenes internas vía `configure(light_image=..., dark_image=...)`.

### 2. Reducir resolución del preview
Actualmente el frame completo de la cámara (normalmente 640×480 o 1280×720) se convierte a un `CTkImage` de 320×240. Hacer `resize()` en el frame antes de `cvtColor` para reducir la carga de conversion.

### 3. Evitar `.copy()` innecesario en el hilo principal
`_actualizar_preview` copia `_frame_actual` bajo el lock. Si el hilo de captura solo escribe y el principal solo lee (bajo lock), se puede usar `np.array(frame, copy=True)` solo cuando `grabando == True` (necesitamos la copia para el círculo rojo). Para el preview normal, podria leerse directamente bajo el lock sin copia.

### 4. Rate-limiter en el loop de preview
`self.after(30, ...)` da ~33 FPS, pero si la camara es 30 FPS reales, no hace falta crear CTkImage a 33 FPS si la UI no puede renderizarlos. Medir FPS reales y ajustar dinamicamente.

### 5. Sleep en el hilo de captura
`_loop_preview` corre un `while` sin pausa quemando CPU. Agregar `time.sleep(0.005)` (5ms) o esperar un `threading.Event` para liberar la CPU cuando no hay frames nuevos.

### 6. Cache de `cap.get()` en `actualizar_labels`
`actualizar_labels` llama `cap.get()` 5 veces (una por propiedad). Como las lecturas son lentas via USB, cachear el resultado en un dict y refrescar solo cuando el usuario presione "Leer valores".

### 7. Lectura asíncrona de presets
`_leer_presets` lee y parsea JSON cada vez que se abre la lista. Cachear en memoria y re-leer solo cuando se guarda/borra un preset.

---

## Funcionalidades

### 8. Selector de cámara (dispositivo 0, 1, 2...)
ComboBox en la UI para elegir entre múltiples cámaras. Al cambiar, reiniciar `cv2.VideoCapture` con el nuevo índice.

### 9. Preview con relación de aspecto correcta
Calcular el aspect ratio del frame y ajustar el `size` del `CTkImage` para que no se vea estirado. Escalar al ancho disponible manteniendo la proporción.

### 10. Atajos de teclado
- `Espacio`: toggle preview
- `R`: toggle grabación
- `F`: tomar foto
- `Escape`: cerrar preview
- `Ctrl+S`: guardar preset

### 11. Filtros en tiempo real
Botones/toggle para aplicar filtros OpenCV al frame antes de mostrarlo: escala de grises, sepia, negativo, espejo, bordes (Canny), etc.

### 12. Modo ráfaga de fotos
Tomar N fotos seguidas con intervalo configurable. Útil para time-lapse o captura de movimiento.

### 13. Overlay de información
Mostrar en el preview: fecha/hora, FPS, resolución, nombre del preset activo. Opcional de activar/desactivar.

### 14. Histograma en vivo
Panel pequeño con histograma RGB del frame actual, actualizado cada ~500ms para no consumir CPU.

### 15. Persistencia de configuración
Guardar en `config.json`: última carpeta de fotos, tamaño de ventana, índice de cámara, tema, preset activo al iniciar.

### 16. Selector de formato de grabación
ComboBox para elegir entre MP4, AVI, MKV y codec (H264, MPEG-4, etc.). Detectar formatos soportados por el sistema.

### 17. Reordenar presets por drag & drop
Arrastrar presets en la lista para cambiar el orden. Persistir el orden en el JSON.

### 18. Exportar/Importar presets
Botón para exportar presets a un archivo `.json` (compartible) e importar desde archivo.

### 19. Modo side-by-side (antes/después)
Al cargar un preset, mostrar el frame original sin procesar junto al frame con el preset aplicado para comparar.

### 20. Detección automática de propiedades soportadas
Al iniciar, probar cada `CAP_PROP` y marcar cuáles realmente responde la cámara (valor != -1). Ocultar sliders de propiedades no soportadas.

### 21. Tema claro/oscuro
Toggle en la UI para cambiar entre "dark" y "light" mode. Persistir la elección.

### 22. Empaquetado como PIP package
Agregar `pyproject.toml` con entry point `webcamcontrol` para poder instalar con `pip install .` y ejecutar desde cualquier terminal.

### 23. CI/CD con GitHub Actions
Workflow que corra `make lint && make test` en cada PR/push. Opcional: build de ejecutable con PyInstaller.

### 24. AppImage / Windows executable
Build automático via GitHub Actions usando PyInstaller. Publicar en Releases.

### 25. Plugins de efectos
Sistema simple de plugins: archivos Python en `plugins/` que exportan una función `apply(frame) -> frame`. Cargar dinámicamente y mostrar en un menú.

### 26. Soporte multilingüe
Archivos `.json` con traducciones (ES, EN). Detectar idioma del sistema o permitir selector en UI.

### 27. Feedback visual en sliders
Mostrar una mini-barra de progreso o color en el slider que indique si el valor está dentro del rango óptimo. Ej: verde = recomendado, rojo = extremo.

### 28. Watermark / superposición de texto
Campo de texto para agregar una marca de agua (fecha, nombre, logo) que se incruste en foto y video.

### 29. Notificaciones de escritorio
Usar `plyer` o `notify-send` para notificaciones no intrusivas en lugar de `messagebox` (que bloquea la UI).

### 30. Zoom digital (recorte)
Slider de "zoom digital" que recorta el centro del frame y lo escala al tamaño original. Emula un zoom óptico sin mover la lente.
