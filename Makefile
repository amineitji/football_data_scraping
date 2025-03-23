# Variables
PYTHON = python3
VENV_ACTIVATE = ./env/bin/activate
SCRIPT = ./src/main.py

# Directories to clean
VIZ_DATA_DIR = ./viz_data
PLAYER_DATA_DIR = ./player_data
HTML_DATA_DIR = ./data/html
PHOTO_DATA_DIR = ./data/photo

# Default values for arguments
URL = ""
PLAYER_NAME = ""
POSTE = ""
NB_PASSE_D = 0

# Commands
.PHONY: all run clean install setup

# Default command
all: run

# Run the Python script with arguments (allowing spaces in the URL, PLAYER_NAME, and optional NB_PASSE_D)
run:
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "$(URL)" "$(PLAYER_NAME)" "$(POSTE)" "$(NB_PASSE_D)"'

# Clean the viz_data and player_data directories
clean:
	rm -rf $(VIZ_DATA_DIR)/*
	rm -rf $(PLAYER_DATA_DIR)/*
	rm -rf $(HTML_DATA_DIR)/*
	rm -rf $(PHOTO_DATA_DIR)/*
	@echo "Cleaned $(VIZ_DATA_DIR), $(PLAYER_DATA_DIR), $(HTML_DATA_DIR), and $(PHOTO_DATA_DIR) directories."

# Install the required Python dependencies
install:
	sudo apt install chromium-chromedriver
	bash -c 'source $(VENV_ACTIVATE) && pip install -r requirements.txt'
	@echo "Installed required dependencies from requirements.txt."

# Set up the virtual environment
setup:
	python3 -m venv env
	@echo "Virtual environment created in /env. Activate it using 'source env/bin/activate'.'
