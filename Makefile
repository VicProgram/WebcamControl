# ── Environment ───────────────────────────────────────────────────
VENV   ?= .venv
MAIN    = webcam_control.py

ifeq ($(OS),Windows_NT)
    BOOTSTRAP = python
    PYTHON    = $(VENV)/Scripts/python.exe
    PIP       = $(VENV)/Scripts/pip.exe
    RUFF      = $(VENV)/Scripts/ruff.exe
else
    BOOTSTRAP = python3
    PYTHON    = $(VENV)/bin/python
    PIP       = $(VENV)/bin/pip
    RUFF      = $(VENV)/bin/ruff
endif

.PHONY: all install run test lint fmt coverage ci clean fclean re

all: install run

# Create the virtual environment (only once)
$(VENV):
	$(BOOTSTRAP) -m venv $(VENV)

# Install runtime + development dependencies (editable)
install: $(VENV)
	$(PIP) install --upgrade pip --quiet
	$(PIP) install -e ".[dev]" --quiet

# Launch the application
run: install
	$(PYTHON) $(MAIN)

# Run the test suite (headless: Tk and OpenCV are mocked)
test: install
	$(PYTHON) -m pytest

# Static checks
lint: install
	$(RUFF) check .
	$(RUFF) format --check .

# Auto-format and auto-fix
fmt: install
	$(RUFF) format .
	$(RUFF) check --fix .

# Tests with coverage report
coverage: install
	$(PYTHON) -m pytest --cov=webcam_control --cov-report=term-missing

# What CI runs
ci: lint test

clean:
	$(BOOTSTRAP) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in ['.pytest_cache', '.ruff_cache', '.mypy_cache', 'htmlcov', '__pycache__', 'tests/__pycache__']]; [p.unlink(missing_ok=True) for p in ['.coverage', 'coverage.xml']]"

fclean: clean
	$(BOOTSTRAP) -c "import shutil; shutil.rmtree('$(VENV)', ignore_errors=True)"

re: fclean all
