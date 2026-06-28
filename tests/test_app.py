from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock

import cv2
import numpy as np


class TestInit:
    def test_app_se_crea_sin_error(self, app) -> None:
        assert app is not None
        assert app.preview_activo is False
        assert app.grabando is False

    def test_app_asigna_titulo(self, app, mocker) -> None:
        mock_title = mocker.patch("customtkinter.CTk.title")
        from webcam_control import WebcamApp

        WebcamApp()
        mock_title.assert_any_call("WebcamControl")

    def test_app_abre_camara_con_backend_correcto(self, mocker) -> None:
        mocker.patch("customtkinter.CTk.__init__", return_value=None)
        mocker.patch("customtkinter.CTk.title")
        mocker.patch("customtkinter.CTk.geometry")
        mocker.patch("customtkinter.CTk.resizable")
        mocker.patch("customtkinter.CTk.minsize")
        mocker.patch("customtkinter.CTk.protocol")
        mocker.patch("customtkinter.CTk.grid_columnconfigure")
        mocker.patch("customtkinter.CTk.grid_rowconfigure")
        mocker.patch("customtkinter.CTk.destroy")
        mocker.patch("customtkinter.CTk.after", return_value="after_id")
        mocker.patch("customtkinter.CTkFrame", return_value=MagicMock())
        mocker.patch("customtkinter.CTkLabel", return_value=MagicMock())
        mocker.patch("customtkinter.CTkButton", return_value=MagicMock())
        mocker.patch("customtkinter.CTkEntry", return_value=MagicMock())
        mocker.patch("customtkinter.CTkScrollableFrame", return_value=MagicMock())
        mocker.patch("customtkinter.CTkFont", return_value=MagicMock())
        mocker.patch("tkinter.messagebox.showerror")
        mocker.patch("tkinter.messagebox.showinfo")
        mocker.patch("customtkinter.set_appearance_mode")
        mocker.patch("customtkinter.set_default_color_theme")

        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((10, 10, 3), dtype=np.uint8))
        mock_cap.grab.return_value = True
        mock_cap.get.return_value = 128.0
        mock_cap.set.return_value = True
        mock_vc = mocker.patch("cv2.VideoCapture", return_value=mock_cap)

        from webcam_control import IS_WINDOWS, WebcamApp

        WebcamApp()
        expected_backend = cv2.CAP_DSHOW if IS_WINDOWS else cv2.CAP_ANY
        mock_vc.assert_called_once_with(0, expected_backend)

    def test_app_camara_no_disponible_muestra_error(self, mock_camera_fail_open, mocker) -> None:
        mocker.patch("customtkinter.CTk.__init__", return_value=None)
        mocker.patch("customtkinter.CTk.title")
        mocker.patch("customtkinter.CTk.geometry")
        mocker.patch("customtkinter.CTk.resizable")
        mocker.patch("customtkinter.CTk.minsize")
        mocker.patch("customtkinter.CTk.protocol")
        mocker.patch("customtkinter.CTk.destroy")
        mocker.patch("customtkinter.set_appearance_mode")
        mocker.patch("customtkinter.set_default_color_theme")

        mock_error = mocker.patch("tkinter.messagebox.showerror")

        from webcam_control import WebcamApp

        app = WebcamApp()
        mock_error.assert_called_once()
        app.destroy.assert_called_once()

    def test_app_desactiva_auto_exposicion_y_auto_foco(self, mock_gui, mock_camera) -> None:
        from webcam_control import WebcamApp

        app = WebcamApp()
        app.cap.set.assert_any_call(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        app.cap.set.assert_any_call(cv2.CAP_PROP_AUTOFOCUS, 0)

    def test_carpeta_fotos_por_defecto(self, app) -> None:
        assert "Fotos" in app.carpeta_fotos


class TestActualizarLabels:
    def test_actualizar_labels_llama_a_cap_grab(self, app) -> None:
        app.cap.grab.reset_mock()
        app.actualizar_labels()
        app.cap.grab.assert_called_once()

    def test_actualizar_labels_con_parametros_soportados(self, app) -> None:
        app.cap.get.return_value = 64.0
        app.actualizar_labels()
        for lbl in app.labels_dict.values():
            lbl.configure.assert_called()

    def test_actualizar_labels_con_no_soportado(self, app) -> None:
        app.cap.get.return_value = -1.0
        app.actualizar_labels()
        for lbl in app.labels_dict.values():
            args, kwargs = lbl.configure.call_args
            texto = kwargs.get("text", args[0] if args else "")
            assert "No soportado" in texto

    def test_actualizar_labels_llama_para_cada_propiedad(self, app) -> None:
        from webcam_control import PROPS_UI

        app.cap.get.reset_mock()
        app.actualizar_labels()
        assert app.cap.get.call_count == len(PROPS_UI)


class TestPreview:
    def test_toggle_preview_inicia_hilo(self, app, mocker) -> None:
        mock_thread = mocker.patch("threading.Thread")
        app.toggle_preview()
        assert app.preview_activo is True
        mock_thread.assert_called_once_with(target=app._loop_preview, daemon=True)

    def test_toggle_preview_detiene(self, app) -> None:
        app.preview_activo = True
        app.toggle_preview()
        assert app.preview_activo is False

    def test_toggle_preview_cambia_texto_boton_iniciar(self, app) -> None:
        app.toggle_preview()
        app.btn_preview.configure.assert_called_with(
            text="⏹  Detener preview",
            fg_color="#7B2020",
            hover_color="#5c1818",
        )

    def test_toggle_preview_cambia_texto_boton_detener(self, app) -> None:
        app.preview_activo = True
        app.toggle_preview()
        app.btn_preview.configure.assert_called_with(
            text="▶  Iniciar preview",
            fg_color=("#3a7ebf", "#1f538d"),
            hover_color=("#325882", "#14375e"),
        )

    def test_loop_preview_captura_frames(self, app) -> None:
        app._frame_actual = None
        t = threading.Thread(target=app._loop_preview, daemon=True)
        app.preview_activo = True
        t.start()
        time.sleep(0.05)
        app.preview_activo = False
        t.join(timeout=2)
        assert app._frame_actual is not None

    def test_loop_preview_usa_lock(self, app) -> None:
        t = threading.Thread(target=app._loop_preview, daemon=True)
        app.preview_activo = True
        t.start()
        time.sleep(0.05)
        app.preview_activo = False
        t.join(timeout=2)
        assert app._lock_frame is not None

    def test_loop_preview_lee_de_cap(self, app) -> None:
        t = threading.Thread(target=app._loop_preview, daemon=True)
        app.preview_activo = True
        t.start()
        time.sleep(0.05)
        app.preview_activo = False
        t.join(timeout=2)
        app.cap.read.assert_called()

    def test_actualizar_preview_muestra_frame(self, app, mocker) -> None:
        mock_imshow = mocker.patch("cv2.imshow")
        app.preview_activo = True
        with app._lock_frame:
            app._frame_actual = np.zeros((100, 100, 3), dtype=np.uint8)
        app._actualizar_preview()
        mock_imshow.assert_called_once()

    def test_actualizar_preview_con_grabacion_pinta_circulo(self, app, mocker) -> None:
        mock_circle = mocker.patch("cv2.circle")
        app.preview_activo = True
        app.grabando = True
        with app._lock_frame:
            app._frame_actual = np.zeros((100, 100, 3), dtype=np.uint8)
        app._actualizar_preview()
        mock_circle.assert_called_once()

    def test_actualizar_preview_con_frame_none_no_crashea(self, app, mocker) -> None:
        mock_imshow = mocker.patch("cv2.imshow")
        app.preview_activo = True
        with app._lock_frame:
            app._frame_actual = None
        app._actualizar_preview()
        mock_imshow.assert_not_called()

    def test_actualizar_preview_detecta_q_cierra(self, app, mocker) -> None:
        mocker.patch("cv2.waitKey", return_value=ord("q"))
        app.preview_activo = True
        app._actualizar_preview()
        assert app.preview_activo is False

    def test_loop_preview_escribe_frame_si_grabando(self, app, mocker) -> None:
        app.grabando = True
        mock_writer = MagicMock()
        app.video_writer = mock_writer
        t = threading.Thread(target=app._loop_preview, daemon=True)
        app.preview_activo = True
        t.start()
        time.sleep(0.05)
        app.preview_activo = False
        t.join(timeout=2)
        mock_writer.write.assert_called()

    def test_actualizar_preview_sin_activo_cierra_ventanas(self, app, mocker) -> None:
        mock_destroy = mocker.patch("cv2.destroyAllWindows")
        app.preview_activo = False
        app._actualizar_preview()
        mock_destroy.assert_called_once()

    def test_actualizar_preview_sin_activo_detiene_grabacion(self, app, mocker) -> None:
        app.preview_activo = False
        app.grabando = True
        app.video_writer = MagicMock()
        app._actualizar_preview()
        assert app.grabando is False


class TestGrabacion:
    def test_toggle_grabacion_sin_preview_muestra_warning(self, app, mocker) -> None:
        mock_warn = mocker.patch("tkinter.messagebox.showwarning")
        app.toggle_grabacion()
        mock_warn.assert_called_once()

    def test_iniciar_grabacion_crea_directorio(self, app, temp_dir) -> None:
        app.preview_activo = True
        app._iniciar_grabacion()
        assert Path(app.carpeta_fotos).exists()

    def test_iniciar_grabacion_crea_video_writer(self, app) -> None:
        app.preview_activo = True
        app._iniciar_grabacion()
        assert app.grabando is True
        assert app.video_writer is not None

    def test_iniciar_grabacion_cambia_boton(self, app) -> None:
        app.preview_activo = True
        app._iniciar_grabacion()
        app.btn_rec.configure.assert_called_with(
            text="⏹  Detener grabación",
            fg_color="#cc0000",
            hover_color="#990000",
        )

    def test_detener_grabacion_libera_writer(self, app, mocker) -> None:
        mock_writer = MagicMock()
        mocker.patch("cv2.VideoWriter", return_value=mock_writer)
        app.preview_activo = True
        app._iniciar_grabacion()
        app._detener_grabacion()
        assert app.grabando is False
        assert app.video_writer is None
        mock_writer.release.assert_called_once()

    def test_detener_grabacion_cambia_boton(self, app) -> None:
        app.preview_activo = True
        app._iniciar_grabacion()
        app._detener_grabacion()
        app.btn_rec.configure.assert_called_with(
            text="⏺  Iniciar grabación",
            fg_color="#8B0000",
            hover_color="#6B0000",
        )

    def test_iniciar_grabacion_resolucion_de_camara(self, app, mocker) -> None:
        app.preview_activo = True

        def get_side_effect(prop):
            if prop == cv2.CAP_PROP_FRAME_WIDTH:
                return 1280
            if prop == cv2.CAP_PROP_FRAME_HEIGHT:
                return 720
            return 128.0

        app.cap.get.side_effect = get_side_effect
        _mock_fourcc = mocker.patch("cv2.VideoWriter_fourcc", return_value=0)
        mock_vw = mocker.patch("cv2.VideoWriter", return_value=MagicMock())
        app._iniciar_grabacion()
        mock_vw.assert_called_once()
        args = mock_vw.call_args[0]
        assert args[2] == 20.0
        assert args[3] == (1280, 720)

    def test_iniciar_grabacion_nombre_con_timestamp(self, app, mocker) -> None:
        app.preview_activo = True
        _mock_vw = mocker.patch("cv2.VideoWriter", return_value=MagicMock())
        app._iniciar_grabacion()
        assert "video_" in app._ruta_video_actual
        assert app._ruta_video_actual.endswith(".mp4")


class TestFoto:
    def test_tomar_foto_con_preview_usa_frame_actual(self, app, mocker) -> None:
        mock_imwrite = mocker.patch("cv2.imwrite")
        app.preview_activo = True
        with app._lock_frame:
            app._frame_actual = np.zeros((100, 100, 3), dtype=np.uint8)
        app.tomar_foto()
        mock_imwrite.assert_called_once()

    def test_tomar_foto_sin_preview_captura_nuevo_frame(self, app, mocker) -> None:
        mock_imwrite = mocker.patch("cv2.imwrite")
        with app._lock_frame:
            app._frame_actual = None
        app.tomar_foto()
        app.cap.read.assert_called()
        mock_imwrite.assert_called_once()

    def test_tomar_foto_crea_directorio(self, app, temp_dir) -> None:
        app.tomar_foto()
        assert Path(app.carpeta_fotos).exists()

    def test_tomar_foto_error_captura_muestra_error(self, app, mocker) -> None:
        mock_error = mocker.patch("tkinter.messagebox.showerror")
        with app._lock_frame:
            app._frame_actual = None
        app.cap.read.side_effect = None
        app.cap.read.return_value = (False, None)
        app.tomar_foto()
        mock_error.assert_called_once()

    def test_tomar_foto_nombre_con_timestamp(self, app, mocker) -> None:
        mock_imwrite = mocker.patch("cv2.imwrite")
        app.tomar_foto()
        ruta = mock_imwrite.call_args[0][0]
        assert "foto_" in ruta
        assert ruta.endswith(".jpg")


class TestMisc:
    def test_abrir_panel_nativo(self, app) -> None:
        app.abrir_panel_nativo()
        app.cap.set.assert_called_with(cv2.CAP_PROP_SETTINGS, 1)

    def test_al_cerrar_detiene_grabacion(self, app) -> None:
        app.grabando = True
        app.video_writer = MagicMock()
        app._al_cerrar()
        assert app.grabando is False

    def test_al_cerrar_libera_camara(self, app) -> None:
        app._al_cerrar()
        app.cap.release.assert_called_once()

    def test_al_cerrar_detiene_preview(self, app) -> None:
        app.preview_activo = True
        app._al_cerrar()
        assert app.preview_activo is False

    def test_al_cerrar_cierra_ventanas_cv(self, app, mocker) -> None:
        mock_destroy = mocker.patch("cv2.destroyAllWindows")
        app._al_cerrar()
        mock_destroy.assert_called_once()

    def test_al_cerrar_destruye_ventana(self, app) -> None:
        app._al_cerrar()
        app.destroy.assert_called_once()

    def test_elegir_carpeta_actualiza_ruta(self, app, mocker) -> None:
        _mock_dialog = mocker.patch("tkinter.filedialog.askdirectory", return_value="/nueva/ruta")
        app.elegir_carpeta()
        assert app.carpeta_fotos == "/nueva/ruta"
        app.lbl_carpeta.configure.assert_called_with(text="/nueva/ruta", text_color="white")

    def test_elegir_carpeta_cancelar_no_cambia(self, app, mocker) -> None:
        mocker.patch("tkinter.filedialog.askdirectory", return_value="")
        original = app.carpeta_fotos
        app.elegir_carpeta()
        assert app.carpeta_fotos == original

    def test_guardar_y_cargar_preset_integracion(self, app, temp_dir, mocker) -> None:
        entry_mock = MagicMock()
        app.entry_nombre = entry_mock
        entry_mock.get.return_value = "Integracion_Test"
        app.guardar()
        app.cap.set.reset_mock()
        app._cargar_preset("Integracion_Test")
        assert app.cap.set.call_count > 0

    def test_props_preset_tiene_19_elementos(self) -> None:
        from webcam_control import PROPS_PRESET

        assert len(PROPS_PRESET) == 19

    def test_props_ui_es_subconjunto_de_props_preset(self) -> None:
        from webcam_control import PROPS_PRESET, PROPS_UI

        for k in PROPS_UI:
            assert k in PROPS_PRESET
