# ── Configuración del entorno virtual ────────────────────────────
VENV        = venv
MAIN        = webcam_control.py
REQS        = requirements.txt

# Detectar OS: en Windows usar Scripts/, en Unix usar bin/
ifeq ($(OS),Windows_NT)
    PYTHON  = $(VENV)/Scripts/python
    PIP     = $(VENV)/Scripts/pip
else
    PYTHON  = $(VENV)/bin/python3
    PIP     = $(VENV)/bin/pip
endif

# ══════════════════════════════════════════════════════════════════
all: install run

# Crea el entorno virtual si no existe
venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creando entorno virtual..."; \
		python3 -m venv $(VENV); \
	fi

# Instala dependencias
install: venv
	@echo "Instalando dependencias..."
	$(PIP) install --upgrade pip --quiet
	$(PIP) install -r $(REQS) --quiet

# Ejecuta la aplicación
run: venv
	$(PYTHON) $(MAIN)

# Limpia archivos temporales y el entorno virtual
clean:
	@echo "Limpiando archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf $(VENV)

# Reinicia desde cero
re: clean all

.PHONY: all venv install run clean re
