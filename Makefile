# Makefile - Football Analytics Tool

# Variables
PYTHON = python3
VENV_ACTIVATE = ./env/bin/activate
SCRIPT = ./src/main.py

# Directories
VIZ_DATA_DIR = ./viz_data
PLAYER_DATA_DIR = ./player_data
PHOTO_DATA_DIR = ./data/photo
DUELS_DIR = $(VIZ_DATA_DIR)/duels
DUOS_DIR = $(VIZ_DATA_DIR)/duos
NETWORKS_DIR = $(VIZ_DATA_DIR)/networks

# Commands
.PHONY: all run clean clean-viz clean-data clean-comparisons install setup test status help modes

# Default command
all: help

# Exécuter le script Python en mode interactif
run:
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) $(SCRIPT)'

# Nettoyer tous les répertoires de données générées
clean:
	rm -rf $(VIZ_DATA_DIR)/*
	rm -rf $(PLAYER_DATA_DIR)/*
	rm -rf $(PHOTO_DATA_DIR)/*
	@echo "🧹 Nettoyage complet terminé."

# Nettoyer uniquement les visualisations individuelles
clean-viz:
	@find $(VIZ_DATA_DIR) -type f -name "*.png" ! -path "*/duels/*" ! -path "*/duos/*" ! -path "*/networks/*" -delete 2>/dev/null || true
	@echo "🧹 Nettoyage des visualisations individuelles terminé."

# Nettoyer uniquement les comparaisons (duels, duos, networks)
clean-comparisons:
	rm -rf $(DUELS_DIR)/* 2>/dev/null || true
	rm -rf $(DUOS_DIR)/* 2>/dev/null || true
	rm -rf $(NETWORKS_DIR)/* 2>/dev/null || true
	@echo "🧹 Nettoyage des comparaisons (duels/duos/networks) terminé."

# Nettoyer uniquement les données JSON
clean-data:
	rm -rf $(PLAYER_DATA_DIR)/*
	@echo "🧹 Nettoyage des données JSON terminé."

# Nettoyer uniquement les photos
clean-photos:
	rm -rf $(PHOTO_DATA_DIR)/*
	@echo "🧹 Nettoyage des photos terminé."

# Installer les dépendances système et Python
install:
	sudo apt install chromium-chromedriver
	bash -c 'source $(VENV_ACTIVATE) && pip install -r requirements.txt'
	@echo "📦 Dépendances installées depuis requirements.txt."

# Mettre en place l'environnement virtuel
setup:
	python3 -m venv env
	@echo "🔧 Environnement virtuel 'env' créé. Activez-le avec 'source env/bin/activate'."

# Tester l'installation
test:
	@echo "🧪 Test de l'installation..."
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) --version'
	bash -c 'source $(VENV_ACTIVATE) && $(PYTHON) -c "import selenium, matplotlib, numpy, mplsoccer, bs4, requests; print(\"✅ Modules principaux importés avec succès\")"'
	@echo "✅ Test d'installation terminé."

# Afficher le statut du projet
status:
	@echo "📊 STATUT DU PROJET - FOOTBALL ANALYTICS"
	@echo "========================================"
	@echo "🐍 Version Python: $$(python3 --version)"
	@echo ""
	@echo "📁 VISUALISATIONS:"
	@echo "   Individuelles: $$(find $(VIZ_DATA_DIR) -type f -name "*.png" ! -path "*/duels/*" ! -path "*/duos/*" ! -path "*/networks/*" 2>/dev/null | wc -l) PNG"
	@echo "   Duels (1v1):   $$(find $(DUELS_DIR) -name "*.png" 2>/dev/null | wc -l) PNG"
	@echo "   Duos:          $$(find $(DUOS_DIR) -name "*.png" 2>/dev/null | wc -l) PNG"
	@echo "   Networks:      $$(find $(NETWORKS_DIR) -name "*.png" 2>/dev/null | wc -l) PNG"
	@echo ""
	@echo "📄 DONNÉES:"
	@echo "   JSON:          $$(find $(PLAYER_DATA_DIR) -name "*.json" 2>/dev/null | wc -l)"
	@echo "   Photos:        $$(find $(PHOTO_DATA_DIR) -name "*.jpg" 2>/dev/null | wc -l)"

# Afficher les modes disponibles
modes:
	@echo "🎮 MODES D'ANALYSE DISPONIBLES"
	@echo "=============================="
	@echo ""
	@echo "Mode 1: Analyse Individuelle"
	@echo "  └─ Analyse détaillée d'un ou plusieurs joueurs"
	@echo "  └─ 4 visualisations par joueur (all, offensive, defensive, passes)"
	@echo ""
	@echo "Mode 2: Duel 1v1 🥊"
	@echo "  └─ Compare 2 joueurs d'équipes adverses"
	@echo "  └─ Output: viz_data/duels/"
	@echo ""
	@echo "Mode 3: Duo 🤝"
	@echo "  └─ Analyse les échanges entre 2 coéquipiers"
	@echo "  └─ Output: viz_data/duos/"
	@echo ""
	@echo "Mode 4: Réseau d'Équipe 🕸️"
	@echo "  └─ Visualise le réseau de passes des 11 titulaires"
	@echo "  └─ Output: viz_data/networks/"
	@echo ""
	@echo "Pour lancer: make run"

# Commande d'aide complète
help:
	@echo "⚽ OUTIL D'ANALYSE DE MATCH WHOSCORED"
	@echo "===================================="
	@echo ""
	@echo "🎯 COMMANDE PRINCIPALE:"
	@echo "  make run            # Lance le script en mode interactif"
	@echo "  make modes          # Affiche les 4 modes disponibles"
	@echo ""
	@echo "🧹 NETTOYAGE:"
	@echo "  make clean              # Nettoyer TOUT"
	@echo "  make clean-viz          # Nettoyer visualisations individuelles uniquement"
	@echo "  make clean-comparisons  # Nettoyer duels/duos/networks uniquement"
	@echo "  make clean-data         # Nettoyer données JSON uniquement"
	@echo "  make clean-photos       # Nettoyer photos uniquement"
	@echo ""
	@echo "📊 INFORMATIONS:"
	@echo "  make status         # Afficher le statut détaillé du projet"
	@echo "  make modes          # Afficher les modes d'analyse"
	@echo ""
	@echo "🔧 SETUP:"
	@echo "  make setup          # Créer l'environnement virtuel"
	@echo "  make install        # Installer les dépendances"
	@echo "  make test           # Tester l'installation"
	@echo ""
	@echo "💡 EXEMPLES D'USAGE:"
	@echo "  make run            # Lance l'interface interactive"
	@echo "  make status         # Vérifie combien de visualisations générées"
	@echo "  make clean-comparisons && make run  # Réinitialise les comparaisons"
	@echo ""