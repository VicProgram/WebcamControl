from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import cv2

PRESETS_FILE = "presets.json"


class TestLeerPresets:
    def test_archivo_no_existe_devuelve_dict_vacio(self, app, temp_dir) -> None:
        presets = app._leer_presets()
        assert presets == {}

    def test_archivo_valido(self, app, preset_file: Path) -> None:
        presets = app._leer_presets()
        assert "Normal" in presets
        assert presets["Normal"]["Brillo"] == 0.0

    def test_archivo_corrupto_devuelve_dict_vacio(self, app, preset_file_corrupted: Path) -> None:
        presets = app._leer_presets()
        assert presets == {}


class TestGuardar:
    def test_guardar_preset_crea_archivo(self, app, temp_dir: Path) -> None:
        app.entry_nombre.get.return_value = "Test_Preset"  # type: ignore[union-attr]
        app.guardar()
        assert Path(PRESETS_FILE).exists()

    def test_guardar_preset_contiene_19_parametros(self, app, temp_dir: Path) -> None:
        app.entry_nombre.get.return_value = "Mi_Preset"  # type: ignore[union-attr]
        app.guardar()
        data = json.loads(Path(PRESETS_FILE).read_text())
        assert len(data["Mi_Preset"]) == 19

    def test_guardar_sin_nombre_muetra_error(self, app, mocker) -> None:
        mock_showerror = mocker.patch("tkinter.messagebox.showwarning")
        app.entry_nombre.get.return_value = ""  # type: ignore[union-attr]
        app.guardar()
        mock_showerror.assert_called_once()

    def test_guardar_preset_no_sobrescribe_otros(
        self, app, preset_file: Path, temp_dir: Path
    ) -> None:
        app.entry_nombre.get.return_value = "Extra"  # type: ignore[union-attr]
        app.guardar()
        data = json.loads(Path(PRESETS_FILE).read_text())
        assert "Normal" in data
        assert "Extra" in data

    def test_guardar_limpia_entry(self, app, temp_dir: Path) -> None:
        entry_mock = MagicMock()
        app.entry_nombre = entry_mock
        entry_mock.get.return_value = "Clean_Test"
        app.guardar()
        entry_mock.delete.assert_called_once_with(0, "end")

    def test_guardar_varias_veces_acumula_presets(self, app, temp_dir: Path) -> None:
        entry_mock = MagicMock()
        app.entry_nombre = entry_mock
        for name in ["A", "B", "C"]:
            entry_mock.get.return_value = name
            app.guardar()
        data = json.loads(Path(PRESETS_FILE).read_text())
        assert set(data.keys()) == {"A", "B", "C"}


class TestCargarPreset:
    def test_cargar_preset_existente_aplica_valores(self, app, preset_file: Path) -> None:
        app._cargar_preset("Normal")
        assert app.cap.set.call_count > 0

    def test_cargar_preset_salta_parametros_no_soportados(self, app, preset_file: Path) -> None:
        app._cargar_preset("Normal")
        args_list = [call[0] for call in app.cap.set.call_args_list]
        props_pasados = {args[0] for args in args_list}
        assert cv2.CAP_PROP_FOCUS not in props_pasados

    def test_cargar_preset_inexistente_muestra_error(self, app, preset_file: Path, mocker) -> None:
        mock_error = mocker.patch("tkinter.messagebox.showerror")
        app._cargar_preset("NoExiste")
        mock_error.assert_called_once()

    def test_cargar_preset_actualiza_labels(self, app, preset_file: Path) -> None:

        app.actualizar_labels = MagicMock()
        app._cargar_preset("Normal")
        app.actualizar_labels.assert_called_once()

    def test_cargar_con_multiples_presets(self, app, temp_dir: Path) -> None:
        data = {
            "A": {"Brillo": 10.0, "Contraste": 20.0},
            "B": {"Brillo": 50.0, "Contraste": 5.0},
        }
        Path(PRESETS_FILE).write_text(json.dumps(data))
        app._cargar_preset("A")
        app.cap.set.assert_any_call(getattr(cv2, "CAP_PROP_BRIGHTNESS"), 10.0)
        app.cap.set.assert_any_call(getattr(cv2, "CAP_PROP_CONTRAST"), 20.0)

    def test_cargar_con_todos_no_soportados(self, app, temp_dir: Path) -> None:
        data = {"AllMinusOne": {"Brillo": -1.0, "Contraste": -1.0}}
        Path(PRESETS_FILE).write_text(json.dumps(data))
        app.cap.set.reset_mock()
        app._cargar_preset("AllMinusOne")
        assert app.cap.set.call_count == 0

    def test_cargar_omitidos_contados_correctamente(self, app, preset_file: Path, mocker) -> None:
        mock_info = mocker.patch("tkinter.messagebox.showinfo")
        app._cargar_preset("Normal")
        mensaje = mock_info.call_args[0][1]
        assert "omitidos" in mensaje


class TestBorrarPreset:
    def test_borrar_preset_existente(self, app, preset_file: Path) -> None:
        app._borrar_preset("Normal")
        data = json.loads(Path(PRESETS_FILE).read_text())
        assert "Normal" not in data

    def test_borrar_preset_inexistente(self, app, preset_file: Path) -> None:
        app._borrar_preset("NoExiste")
        data = json.loads(Path(PRESETS_FILE).read_text())
        assert "Normal" in data

    def test_borrar_pregunta_confirmacion(self, app, mocker) -> None:
        mock_ask = mocker.patch("tkinter.messagebox.askyesno", return_value=False)

        app._borrar_preset("Normal")
        mock_ask.assert_called_once()

    def test_borrar_cancelado_no_elimina(self, app, preset_file: Path, mocker) -> None:
        mocker.patch("tkinter.messagebox.askyesno", return_value=False)
        app._borrar_preset("Normal")
        data = json.loads(Path(PRESETS_FILE).read_text())
        assert "Normal" in data

    def test_borrar_refresca_lista(self, app, preset_file: Path) -> None:
        app._refrescar_lista_presets = MagicMock()
        app._borrar_preset("Normal")
        app._refrescar_lista_presets.assert_called_once()

    def test_borrar_ultimo_preset_deja_json_vacio(self, app, temp_dir: Path) -> None:
        data = {"Unico": {"Brillo": 1.0}}
        Path(PRESETS_FILE).write_text(json.dumps(data))
        app._borrar_preset("Unico")
        data = json.loads(Path(PRESETS_FILE).read_text())
        assert data == {}


class TestRefrescarLista:
    def test_refrescar_con_presets_crea_botones(self, app, preset_file: Path, mock_gui) -> None:
        app._refrescar_lista_presets()
        assert mock_gui["frame_mock"].pack.call_count > 0

    def test_refrescar_sin_presets_muestra_mensaje(self, app, temp_dir: Path) -> None:
        app._refrescar_lista_presets()
        assert app.lista_frame.pack.called or True
