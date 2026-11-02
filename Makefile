PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
PY := $(BIN)/python
PIP := $(BIN)/pip

.PHONY: help install all standard narrow catalogs check clean

help:
	@echo "RIVE ROSSE STENCILS"
	@echo ""
	@echo "  make install   Create .venv and install requirements.txt"
	@echo "  make all       Regenerate every STL and PNG"
	@echo "  make standard  Only the 190 x 190 catalog"
	@echo "  make narrow    Only the 190 x 80 narrow catalog"
	@echo "  make catalogs  Only the PNG catalogs"
	@echo "  make check     Validate the 120 STL files"
	@echo "  make clean     Remove Python caches and .venv"
	@echo ""
	@echo "Generated STL and PNG files are written to stl/ and png/."

install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

all:
	$(PY) script/generare_cartelli.py
	$(PY) script/generare_segnali.py
	$(PY) script/generare_segnali_aiuto.py
	$(PY) script/generare_cartelli_stretti.py
	$(PY) script/generare_segnali_stretti.py
	$(PY) script/generare_trails_2.py
	$(PY) script/generare_catalogo.py

standard:
	$(PY) script/generare_cartelli.py
	$(PY) script/generare_segnali.py
	$(PY) script/generare_segnali_aiuto.py

narrow:
	$(PY) script/generare_cartelli_stretti.py
	$(PY) script/generare_segnali_stretti.py
	$(PY) script/generare_trails_2.py

catalogs:
	$(PY) script/generare_catalogo.py

check:
	$(PY) script/validar_stl.py

clean:
	rm -rf $(VENV)
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
