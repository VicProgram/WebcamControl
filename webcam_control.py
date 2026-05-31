import sys
import cv2
import json
import os
import threading
import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import datetime

# ── Tema ──────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

IS_WINDOWS = sys.platform == "win32"

# Parámetros que se guardan en cada preset (19 propiedades)
PROPS_PRESET = {
    "Brillo":         cv2.CAP_PROP_BRIGHTNESS,
    "Contraste":      cv2.CAP_PROP_CONTRAST,
    "Saturacion":     cv2.CAP_PROP_SATURATION,
    "Exposicion":     cv2.CAP_PROP_EXPOSURE,
    "Ganancia":       cv2.CAP_PROP_GAIN,
    "Foco":           cv2.CAP_PROP_FOCUS,
    "Zoom":           cv2.CAP_PROP_ZOOM,
    "Nitidez":        cv2.CAP_PROP_SHARPNESS,
    "Gamma":          cv2.CAP_PROP_GAMMA,
    "Tono":           cv2.CAP_PROP_HUE,
    "Contraluz":      cv2.CAP_PROP_BACKLIGHT,
    "Temp_Color":     cv2.CAP_PROP_WHITE_BALANCE_BLUE_U,
    "Auto_Exposicion":cv2.CAP_PROP_AUTO_EXPOSURE,
    "Auto_Foco":      cv2.CAP_PROP_AUTOFOCUS,
    "Auto_WB":        cv2.CAP_PROP_AUTO_WB,
    "Pan":            cv2.CAP_PROP_PAN,
    "Tilt":           cv2.CAP_PROP_TILT,
    "Roll":           cv2.CAP_PROP_ROLL,
    "Iris":           cv2.CAP_PROP_IRIS,
}

# Parámetros visibles en la UI (los 5 más usados)
PROPS_UI = {
    "Brillo":     cv2.CAP_PROP_BRIGHTNESS,
    "Contraste":  cv2.CAP_PROP_CONTRAST,
    "Saturacion": cv2.CAP_PROP_SATURATION,
    "Exposicion": cv2.CAP_PROP_EXPOSURE,
    "Ganancia":   cv2.CAP_PROP_GAIN,
}

PRESETS_FILE = "presets.json"


class WebcamApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WebcamControl")
        self.geometry("720x620")
        self.resizable(False, False)

        # Abrir cámara: CAP_DSHOW solo en Windows
        backend = cv2.CAP_DSHOW if IS_WINDOWS else cv2.CAP_ANY
        self.cap = cv2.VideoCapture(0, backend)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "No se pudo abrir la cámara.")
            self.destroy()
            return

        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)

        # Estado
        self.preview_activo = False
        self.hilo_preview = None
        self._frame_actual = None
        self._lock_frame = threading.Lock()   # protege _frame_actual entre hilos
        self.grabando = False
        self.video_writer = None
        self._ruta_video_actual = ""
        self.carpeta_fotos = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "Fotos"
        )

        self._build_ui()
        self._refrescar_lista_presets()
        self.actualizar_labels()
        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    # ── UI ────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Columna izquierda
        left = ctk.CTkFrame(self, corner_radius=12)
        left.grid(row=0, column=0, padx=(16, 8), pady=16, sticky="nsew")
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left, text="WebcamControl", font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, pady=(16, 2))
        ctk.CTkLabel(
            left, text="Panel de control", font=ctk.CTkFont(size=12), text_color="gray"
        ).grid(row=1, column=0, pady=(0, 10))

        # Cuadro de valores actuales
        vf = ctk.CTkFrame(left, corner_radius=8)
        vf.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="ew")
        vf.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            vf, text="Estado actual", font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, pady=(8, 4), padx=12, sticky="w")

        self.labels_dict = {}
        for i, nombre in enumerate(PROPS_UI.keys()):
            lbl = ctk.CTkLabel(vf, text=f"{nombre}: ---", font=ctk.CTkFont(size=12), anchor="w")
            lbl.grid(row=i + 1, column=0, padx=16, pady=1, sticky="w")
            self.labels_dict[nombre] = lbl

        ctk.CTkButton(
            vf, text="Leer valores", command=self.actualizar_labels, height=30
        ).grid(row=len(PROPS_UI) + 1, column=0, padx=12, pady=(6, 10), sticky="ew")

        # Botón configuración avanzada (solo Windows)
        if IS_WINDOWS:
            ctk.CTkButton(
                left,
                text="Abrir configuración avanzada",
                command=self.abrir_panel_nativo,
                fg_color="transparent",
                border_width=1,
                height=32,
            ).grid(row=3, column=0, padx=12, pady=(0, 6), sticky="ew")

        self.btn_preview = ctk.CTkButton(
            left,
            text="▶  Iniciar preview",
            command=self.toggle_preview,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.btn_preview.grid(row=4, column=0, padx=12, pady=(0, 6), sticky="ew")

        self.btn_rec = ctk.CTkButton(
            left,
            text="⏺  Iniciar grabación",
            command=self.toggle_grabacion,
            height=36,
            fg_color="#8B0000",
            hover_color="#6B0000",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.btn_rec.grid(row=5, column=0, padx=12, pady=(0, 12), sticky="ew")

        ctk.CTkLabel(
            left, text="Captura de foto", font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=6, column=0, padx=12, pady=(4, 4), sticky="w")

        cr = ctk.CTkFrame(left, fg_color="transparent")
        cr.grid(row=7, column=0, padx=12, pady=(0, 6), sticky="ew")
        cr.grid_columnconfigure(0, weight=1)

        self.lbl_carpeta = ctk.CTkLabel(
            cr, text="Fotos/", font=ctk.CTkFont(size=11), text_color="gray", anchor="w"
        )
        self.lbl_carpeta.grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            cr, text="Cambiar", width=70, height=26, command=self.elegir_carpeta
        ).grid(row=0, column=1, padx=(6, 0))

        ctk.CTkButton(
            left,
            text="📷  Tomar foto",
            command=self.tomar_foto,
            height=36,
            fg_color="#1a5c38",
            hover_color="#144a2d",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=8, column=0, padx=12, pady=(0, 16), sticky="ew")

        # Columna derecha: presets
        right = ctk.CTkFrame(self, corner_radius=12)
        right.grid(row=0, column=1, padx=(8, 16), pady=16, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            right, text="Presets", font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, pady=(16, 2))
        ctk.CTkLabel(
            right,
            text="Clic para cargar  ·  × para borrar",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).grid(row=1, column=0, pady=(0, 8))

        self.lista_frame = ctk.CTkScrollableFrame(right, corner_radius=8)
        self.lista_frame.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self.lista_frame.grid_columnconfigure(0, weight=1)

        bot = ctk.CTkFrame(right, fg_color="transparent")
        bot.grid(row=3, column=0, padx=12, pady=(0, 16), sticky="ew")
        bot.grid_columnconfigure(0, weight=1)

        self.entry_nombre = ctk.CTkEntry(bot, placeholder_text="Nombre del preset...", height=36)
        self.entry_nombre.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        ctk.CTkButton(
            bot,
            text="💾  Guardar preset actual",
            command=self.guardar,
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=1, column=0, sticky="ew")

    # ── Presets ───────────────────────────────────────────────────

    def _refrescar_lista_presets(self):
        for w in self.lista_frame.winfo_children():
            w.destroy()
        presets = self._leer_presets()
        if not presets:
            ctk.CTkLabel(
                self.lista_frame,
                text="No hay presets guardados",
                text_color="gray",
                font=ctk.CTkFont(size=12),
            ).pack(pady=20)
            return
        for nombre in presets:
            fila = ctk.CTkFrame(self.lista_frame, corner_radius=8, height=40)
            fila.pack(fill="x", pady=3, padx=2)
            fila.pack_propagate(False)
            fila.grid_columnconfigure(0, weight=1)
            ctk.CTkButton(
                fila,
                text=nombre,
                anchor="w",
                fg_color="transparent",
                hover_color=("#3a3a3a", "#3a3a3a"),
                font=ctk.CTkFont(size=13),
                command=lambda n=nombre: self._cargar_preset(n),
            ).grid(row=0, column=0, sticky="ew", padx=(6, 0), pady=2)
            ctk.CTkButton(
                fila,
                text="×",
                width=30,
                height=28,
                fg_color="transparent",
                hover_color="#5c1a1a",
                text_color="#cc4444",
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda n=nombre: self._borrar_preset(n),
            ).grid(row=0, column=1, padx=(0, 4), pady=2)

    def _leer_presets(self):
        if not os.path.exists(PRESETS_FILE):
            return {}
        with open(PRESETS_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def _cargar_preset(self, nombre):
        presets = self._leer_presets()
        if nombre not in presets:
            messagebox.showerror("Error", f"El preset '{nombre}' no existe")
            return
        aplicados = omitidos = 0
        for prop, val in presets[nombre].items():
            if val == -1:
                omitidos += 1
                continue
            if prop in PROPS_PRESET:
                self.cap.set(PROPS_PRESET[prop], val)
                aplicados += 1
        self.actualizar_labels()
        messagebox.showinfo(
            "Preset cargado",
            f"'{nombre}' aplicado\n{aplicados} parámetros · {omitidos} omitidos",
        )

    def _borrar_preset(self, nombre):
        if not messagebox.askyesno("Borrar preset", f"¿Borrar '{nombre}'?"):
            return
        presets = self._leer_presets()
        presets.pop(nombre, None)
        with open(PRESETS_FILE, "w") as f:
            json.dump(presets, f, indent=4)
        self._refrescar_lista_presets()

    # ── Preview ───────────────────────────────────────────────────

    def toggle_preview(self):
        if not self.preview_activo:
            self.preview_activo = True
            self._frame_actual = None
            self.btn_preview.configure(
                text="⏹  Detener preview", fg_color="#7B2020", hover_color="#5c1818"
            )
            self.hilo_preview = threading.Thread(target=self._loop_preview, daemon=True)
            self.hilo_preview.start()
            self.after(30, self._actualizar_preview)
        else:
            self.preview_activo = False
            self.btn_preview.configure(
                text="▶  Iniciar preview",
                fg_color=("#3a7ebf", "#1f538d"),
                hover_color=("#325882", "#14375e"),
            )

    def _loop_preview(self):
        """Hilo secundario: solo captura frames, nunca llama a cv2.waitKey."""
        while self.preview_activo:
            ret, frame = self.cap.read()
            if ret:
                with self._lock_frame:
                    self._frame_actual = frame
                if self.grabando and self.video_writer:
                    self.video_writer.write(frame)

    def _actualizar_preview(self):
        """Hilo principal (via after): muestra el frame y gestiona waitKey."""
        if self.preview_activo:
            with self._lock_frame:
                frame = self._frame_actual.copy() if self._frame_actual is not None else None
            if frame is not None:
                if self.grabando:
                    cv2.circle(frame, (20, 20), 8, (0, 0, 220), -1)
                cv2.imshow("Webcam Control Live View", frame)
            # waitKey en el hilo principal: detecta 'q' para cerrar preview
            if cv2.waitKey(1) & 0xFF == ord("q"):
                self.toggle_preview()
                return
            self.after(30, self._actualizar_preview)
        else:
            if self.grabando:
                self._detener_grabacion()
            cv2.destroyAllWindows()

    # ── Grabación ─────────────────────────────────────────────────

    def toggle_grabacion(self):
        if not self.grabando:
            if not self.preview_activo:
                messagebox.showwarning("Atención", "Activa el preview primero para poder grabar.")
                return
            self._iniciar_grabacion()
        else:
            self._detener_grabacion()

    def _iniciar_grabacion(self):
        os.makedirs(self.carpeta_fotos, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta = os.path.join(self.carpeta_fotos, f"video_{ts}.mp4")
        w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.video_writer = cv2.VideoWriter(ruta, fourcc, 20.0, (w, h))
        self.grabando = True
        self._ruta_video_actual = ruta
        self.btn_rec.configure(text="⏹  Detener grabación", fg_color="#cc0000", hover_color="#990000")

    def _detener_grabacion(self):
        self.grabando = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        self.btn_rec.configure(text="⏺  Iniciar grabación", fg_color="#8B0000", hover_color="#6B0000")
        messagebox.showinfo("Grabación guardada", f"Video guardado en:\n{self._ruta_video_actual}")

    # ── Foto ──────────────────────────────────────────────────────

    def elegir_carpeta(self):
        nueva = filedialog.askdirectory(title="Carpeta para fotos y videos")
        if nueva:
            self.carpeta_fotos = nueva
            self.lbl_carpeta.configure(text=nueva, text_color="white")

    def tomar_foto(self):
        with self._lock_frame:
            frame = self._frame_actual.copy() if self._frame_actual is not None else None
        if frame is None:
            ret, frame = self.cap.read()
            if not ret:
                messagebox.showerror("Error", "No se pudo capturar imagen")
                return
        os.makedirs(self.carpeta_fotos, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta = os.path.join(self.carpeta_fotos, f"foto_{ts}.jpg")
        cv2.imwrite(ruta, frame)
        messagebox.showinfo("Foto guardada", f"Guardada en:\n{ruta}")

    # ── Misc ──────────────────────────────────────────────────────

    def actualizar_labels(self):
        self.cap.grab()
        for nombre, prop_id in PROPS_UI.items():
            val = self.cap.get(prop_id)
            texto = f"{val:.1f}" if val != -1 else "No soportado"
            self.labels_dict[nombre].configure(text=f"{nombre}: {texto}")

    def abrir_panel_nativo(self):
        """Abre el panel DirectShow de Windows (solo disponible en Windows)."""
        self.cap.set(cv2.CAP_PROP_SETTINGS, 1)

    def guardar(self):
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Error", "Ponle un nombre al preset")
            return
        self.cap.grab()
        actuales = {n: self.cap.get(p) for n, p in PROPS_PRESET.items()}
        presets = self._leer_presets()
        presets[nombre] = actuales
        with open(PRESETS_FILE, "w") as f:
            json.dump(presets, f, indent=4)
        self.entry_nombre.delete(0, "end")
        self._refrescar_lista_presets()
        messagebox.showinfo("Guardado", f"Preset '{nombre}' guardado con {len(actuales)} parámetros")

    def _al_cerrar(self):
        if self.grabando:
            self._detener_grabacion()
        self.preview_activo = False
        self.cap.release()
        cv2.destroyAllWindows()
        self.destroy()


if __name__ == "__main__":
    app = WebcamApp()
    app.mainloop()
