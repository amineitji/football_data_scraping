# Variables
PYTHON = python3
VENV_ACTIVATE = ./env/bin/activate
SCRIPT = ./src/main.py

# Directories to clean
VIZ_DATA_DIR = ./viz_data
PLAYER_DATA_DIR = ./player_data
HTML_DATA_DIR = ./data/html
PHOTO_DATA_DIR = ./data/photo
ADVANCED_ANALYSIS_DIR = ./advanced_analysis

# Default values for arguments
URL = ""
PLAYER_NAME = ""
POSTE = ""
NB_PASSE_D = 0

# Commands
.PHONY: all run run-advanced run-advanced-only clean install setup help

# Default command
all: help

# Run the Python script with standard arguments
run:
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "$(URL)" "$(PLAYER_NAME)" "$(POSTE)" "$(NB_PASSE_D)"'

# Run the Python script with advanced analysis
run-advanced:
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "$(URL)" "$(PLAYER_NAME)" "$(POSTE)" "$(NB_PASSE_D)" --advanced'

# Run only advanced analysis (faster)
run-advanced-only:
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "$(URL)" "$(PLAYER_NAME)" "$(POSTE)" --advanced-only'

# Quick run commands for common scenarios
quick-mil:
	@echo "🚀 Analyse rapide pour milieu de terrain..."
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "$(URL)" "$(PLAYER_NAME)" "MIL" 0'

quick-att:
	@echo "🚀 Analyse rapide pour attaquant..."
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "$(URL)" "$(PLAYER_NAME)" "ATT" 0'

quick-def:
	@echo "🚀 Analyse rapide pour défenseur..."
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "$(URL)" "$(PLAYER_NAME)" "DEF" 0'

quick-gk:
	@echo "🚀 Analyse rapide pour gardien..."
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "$(URL)" "$(PLAYER_NAME)" "GK" 0'

# Advanced analysis shortcuts
advanced-mil:
	@echo "🧠 Analyse avancée pour milieu de terrain..."
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "$(URL)" "$(PLAYER_NAME)" "MIL" 0 --advanced'

advanced-att:
	@echo "🧠 Analyse avancée pour attaquant..."
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "$(URL)" "$(PLAYER_NAME)" "ATT" 0 --advanced'

advanced-def:
	@echo "🧠 Analyse avancée pour défenseur..."
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "$(URL)" "$(PLAYER_NAME)" "DEF" 0 --advanced'

# Only advanced analysis (super fast)
only-advanced:
	@echo "⚡ Analyses avancées uniquement (rapide)..."
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "$(URL)" "$(PLAYER_NAME)" "$(POSTE)" --advanced-only'

# Clean the viz_data and player_data directories
clean:
	rm -rf $(VIZ_DATA_DIR)/*
	rm -rf $(PLAYER_DATA_DIR)/*
	rm -rf $(HTML_DATA_DIR)/*
	rm -rf $(PHOTO_DATA_DIR)/*
	rm -rf $(ADVANCED_ANALYSIS_DIR)/*
	@echo "🧹 Cleaned $(VIZ_DATA_DIR), $(PLAYER_DATA_DIR), $(HTML_DATA_DIR), $(PHOTO_DATA_DIR), and $(ADVANCED_ANALYSIS_DIR) directories."

# Clean only visualization outputs (keep raw data)
clean-viz:
	rm -rf $(VIZ_DATA_DIR)/*
	rm -rf $(ADVANCED_ANALYSIS_DIR)/*
	@echo "🧹 Cleaned visualization directories only."

# Clean only player data
clean-data:
	rm -rf $(PLAYER_DATA_DIR)/*
	rm -rf $(HTML_DATA_DIR)/*
	@echo "🧹 Cleaned data directories only."

# Install the required Python dependencies
install:
	sudo apt install chromium-chromedriver
	bash -c 'source $(VENV_ACTIVATE) && pip install -r requirements.txt'
	@echo "📦 Installed required dependencies from requirements.txt."

# Set up the virtual environment
setup:
	python3 -m venv env
	@echo "🔧 Virtual environment created in /env. Activate it using 'source env/bin/activate'."

# Test the installation
test:
	@echo "🧪 Testing installation..."
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) --version'
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) -c "import selenium, matplotlib, numpy; print(\"✅ All modules imported successfully\")"'
	@echo "✅ Installation test completed."

# Show project status
status:
	@echo "📊 PROJECT STATUS"
	@echo "=================="
	@echo "🐍 Python version: $$(python3 --version)"
	@echo "📁 Viz data files: $$(find $(VIZ_DATA_DIR) -name "*.png" 2>/dev/null | wc -l) PNG files"
	@echo "📄 Player data files: $$(find $(PLAYER_DATA_DIR) -name "*.json" 2>/dev/null | wc -l) JSON files"
	@echo "🧠 Advanced analyses: $$(find $(ADVANCED_ANALYSIS_DIR) -name "*.png" 2>/dev/null | wc -l) PNG files"
	@echo "📸 Player photos: $$(find $(PHOTO_DATA_DIR) -name "*.jpg" 2>/dev/null | wc -l) JPG files"

# Help command with examples
help:
	@echo "⚽ FOOTBALL DATA ANALYSIS TOOLKIT"
	@echo "=================================="
	@echo ""
	@echo "🎯 QUICK COMMANDS:"
	@echo "  make quick-mil URL=\"...\" PLAYER_NAME=\"Vitinha\"     # Analyse rapide milieu"
	@echo "  make quick-att URL=\"...\" PLAYER_NAME=\"Mbappé\"     # Analyse rapide attaquant"
	@echo "  make advanced-mil URL=\"...\" PLAYER_NAME=\"Vitinha\" # Analyse avancée milieu"
	@echo "  make only-advanced URL=\"...\" PLAYER_NAME=\"Vitinha\" # Analyses avancées uniquement"
	@echo ""
	@echo "📊 STANDARD COMMANDS:"
	@echo "  make run URL=\"...\" PLAYER_NAME=\"...\" POSTE=\"MIL\" # Analyse standard"
	@echo "  make run-advanced URL=\"...\" PLAYER_NAME=\"...\" POSTE=\"MIL\" # Standard + avancée"
	@echo "  make run-advanced-only URL=\"...\" PLAYER_NAME=\"...\" # Avancée uniquement"
	@echo ""
	@echo "🧹 MAINTENANCE:"
	@echo "  make clean          # Nettoyer tous les fichiers générés"
	@echo "  make clean-viz      # Nettoyer uniquement les visualisations"
	@echo "  make clean-data     # Nettoyer uniquement les données"
	@echo "  make status         # Afficher le statut du projet"
	@echo ""
	@echo "🔧 SETUP:"
	@echo "  make setup          # Créer l'environnement virtuel"
	@echo "  make install        # Installer les dépendances"
	@echo "  make test           # Tester l'installation"
	@echo ""
	@echo "💡 EXEMPLES COMPLETS:"
	@echo "  make quick-mil URL=\"https://fr.whoscored.com/matches/1899310/live/...\" PLAYER_NAME=\"Vitinha\""
	@echo "  make advanced-att URL=\"https://fr.whoscored.com/matches/1899310/live/...\" PLAYER_NAME=\"Mbappé\""
	@echo "  make only-advanced URL=\"https://fr.whoscored.com/matches/1899310/live/...\" PLAYER_NAME=\"Hakimi\""
	@echo ""
	@echo "🚀 NOUVEAU: Analyses Avancées Disponibles!"
	@echo "   🧠 Intelligence Spatiale    ⚡ Analyse de Pression    🔮 Analyse Prédictive"

# Development shortcuts
dev-vitinha:
	@echo "🔬 DEV: Analyse Vitinha avec toutes les options..."
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "https://fr.whoscored.com/matches/1899310/live/europe-champions-league-2024-2025-paris-saint-germain-inter" "Vitinha" "MIL" 0 --advanced'

dev-mbappe:
	@echo "🔬 DEV: Analyse Mbappé avec toutes les options..."
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT) "https://fr.whoscored.com/matches/1899310/live/europe-champions-league-2024-2025-paris-saint-germain-inter" "Kylian Mbappé" "ATT" 0 --advanced'

# Performance monitoring
benchmark:
	@echo "⏱️ BENCHMARK: Mesure des performances..."
	@time make only-advanced URL="$(URL)" PLAYER_NAME="$(PLAYER_NAME)"
	@echo "✅ Benchmark terminé."