# ── Configuración del entorno virtual ────────────────────────────
VENV        = venv
MAIN        = webcam_control.py
REQS        = requirements.txt

# Detectar OS: en Windows usar Scripts/, en Unix usar bin/
ifeq ($(OS),Windows_NT)
    PYTHON  = $(VENV)/Scripts/python
    PIP     = $(VENV)/Scripts/pip
    RUFF    = $(VENV)/Scripts/ruff
else
    PYTHON  = $(VENV)/bin/python3
    PIP     = $(VENV)/bin/pip
    RUFF    = $(VENV)/bin/ruff
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

# Ejecuta el linter
lint: venv
	$(PIP) install -q ruff
	$(RUFF) check $(MAIN)
	$(RUFF) format --check $(MAIN)

# Aplica formato automático
fmt: venv
	$(PIP) install -q ruff
	$(RUFF) format $(MAIN)
	$(RUFF) check --fix $(MAIN)

# Reinicia desde cero
re: clean all

.PHONY: all venv install run clean re lint fmt
