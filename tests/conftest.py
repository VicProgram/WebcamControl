from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

PRESET_DATA: dict[str, dict[str, float]] = {
    "Normal": {
        "Brillo": 0.0,
        "Contraste": 15.0,
        "Saturacion": 10.0,
        "Exposicion": -4.0,
        "Ganancia": 32.0,
        "Foco": -1.0,
        "Zoom": -1.0,
        "Nitidez": 7.0,
        "Gamma": 192.0,
        "Tono": 0.0,
        "Contraluz": 0.0,
        "Temp_Color": -1.0,
        "Auto_Exposicion": -1.0,
        "Auto_Foco": -1.0,
        "Auto_WB": 1.0,
        "Pan": -1.0,
        "Tilt": -1.0,
        "Roll": -1.0,
        "Iris": -1.0,
    },
}


FAKE_FRAME: np.ndarray = np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as d:
        old_cwd = Path.cwd()
        os.chdir(d)
        yield Path(d)
        os.chdir(old_cwd)


@pytest.fixture
def preset_file(temp_dir: Path) -> Path:
    path = temp_dir / "presets.json"
    path.write_text(json.dumps(PRESET_DATA, indent=4))
    return path


@pytest.fixture
def preset_file_corrupted(temp_dir: Path) -> Path:
    path = temp_dir / "presets.json"
    path.write_text("not valid json{{}")
    return path


@pytest.fixture
def mock_camera(mocker) -> MagicMock:
    cap = MagicMock()
    cap.isOpened.return_value = True

    def fake_read() -> tuple[bool, np.ndarray | None]:
        return (True, FAKE_FRAME.copy())

    cap.read.side_effect = fake_read
    cap.grab.return_value = True
    cap.get.return_value = 128.0
    cap.set.return_value = True
    cap.release.return_value = None
    cap.get.return_value = 128.0
    mocker.patch("cv2.VideoCapture", return_value=cap)
    return cap


@pytest.fixture
def mock_camera_no_support(mocker) -> MagicMock:
    cap = MagicMock()
    cap.isOpened.return_value = True

    def fake_read() -> tuple[bool, np.ndarray | None]:
        return (True, FAKE_FRAME.copy())

    cap.read.side_effect = fake_read
    cap.grab.return_value = True
    cap.get.return_value = -1.0
    cap.set.return_value = True
    cap.release.return_value = None
    mocker.patch("cv2.VideoCapture", return_value=cap)
    return cap


@pytest.fixture
def mock_camera_fail_open(mocker) -> MagicMock:
    cap = MagicMock()
    cap.isOpened.return_value = False
    mocker.patch("cv2.VideoCapture", return_value=cap)
    return cap


@pytest.fixture
def mock_gui(mocker) -> dict[str, MagicMock]:
    mocker.patch("customtkinter.set_appearance_mode")
    mocker.patch("customtkinter.set_default_color_theme")
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

    btn_mock = MagicMock()
    label_mock = MagicMock()
    slider_mock = MagicMock()

    label_mock.configure.return_value = None
    btn_mock.configure.return_value = None
    slider_mock.grid.return_value = None
    slider_mock.set.return_value = None
    slider_mock.get.return_value = 0.0

    scrollable_mock = MagicMock()
    scrollable_mock.winfo_children.return_value = []
    scrollable_mock.grid_columnconfigure.return_value = None
    scrollable_mock.pack.return_value = None

    frame_mock = MagicMock()
    frame_mock.grid_columnconfigure.return_value = None
    frame_mock.grid_rowconfigure.return_value = None
    frame_mock.pack.return_value = None
    frame_mock.pack_propagate.return_value = None
    frame_mock.winfo_children.return_value = []

    mocker.patch("customtkinter.CTkFrame", return_value=frame_mock)
    mocker.patch("customtkinter.CTkLabel", return_value=label_mock)
    mocker.patch("customtkinter.CTkButton", return_value=btn_mock)
    mocker.patch("customtkinter.CTkSlider", return_value=slider_mock)
    mocker.patch("customtkinter.CTkEntry", return_value=MagicMock())
    mocker.patch("customtkinter.CTkScrollableFrame", return_value=scrollable_mock)
    mocker.patch("customtkinter.CTkFont", return_value=MagicMock())

    mocker.patch("tkinter.messagebox.showerror")
    mocker.patch("tkinter.messagebox.showwarning")
    mocker.patch("tkinter.messagebox.showinfo")
    mocker.patch("tkinter.messagebox.askyesno", return_value=True)

    mocker.patch("cv2.imshow")
    mocker.patch("cv2.waitKey", return_value=0)
    mocker.patch("cv2.destroyAllWindows")
    mocker.patch("cv2.imwrite", return_value=True)

    return {
        "btn_mock": btn_mock,
        "label_mock": label_mock,
        "slider_mock": slider_mock,
        "scrollable_mock": scrollable_mock,
        "frame_mock": frame_mock,
    }


@pytest.fixture
def app(mock_gui, mock_camera) -> Generator:
    from webcam_control import WebcamApp

    instance = WebcamApp()
    yield instance
    instance.preview_activo = False
    try:
        instance.cap.release()
    except Exception:
        pass
