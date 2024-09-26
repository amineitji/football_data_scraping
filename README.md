ITJI Amine

# Projet de visualisation des données de joueurs

Ce projet fournit un outil pour extraire et visualiser les statistiques des joueurs à partir des données de match. Les visualisations générées incluent les passes, les activités défensives, les activités offensives, et bien plus, et sont sauvegardées dans des répertoires organisés.

## Structure du projet

```
/src                # Code source, y compris main.py et autres scripts
/doc                # Documentation
/data               # Données des matchs (fichiers JSON en entrée)
/viz_data           # Répertoire pour sauvegarder les visualisations générées
/player_data        # Répertoire pour stocker les données de joueurs extraites
/env                # Environnement virtuel Python (non inclus dans le contrôle de version)
/requirements.txt   # Liste des dépendances
/Makefile           # Makefile pour automatisation
/README.md          # Documentation du projet
```

## Pré-requis

- Python 3.x
- Environnement virtuel (`venv`) ou tout autre outil de gestion d'environnement

## Instructions d'installation

1. **Cloner le dépôt** :
   ```
   git clone <url_du_dépôt>
   cd <répertoire_du_projet>
   ```

2. **Configurer l'environnement virtuel** :
   ```
   make setup
   ```

3. **Activer l'environnement virtuel** :
   ```
   source env/bin/activate
   ```

4. **Installer les dépendances requises** :
   ```
   make install
   ```

## Exécution du code

Vous pouvez exécuter le script principal pour générer des visualisations pour un match et un joueur spécifiques en utilisant le Makefile :

```
make run URL=<url_des_données_de_match> PLAYER_NAME=<nom_du_joueur> POSTE=<poste>
```

Par exemple :

```
make run URL="data/html/Monaco 3-1 Le Havre - Ligue 1 2024_2025 Live.html" PLAYER_NAME="Eliesse Ben Seghir" POSTE="ATT"
```

## Nettoyage des répertoires de données

Pour nettoyer les répertoires `/viz_data` et `/player_data`, utilisez :

```
make clean
```

Cela supprimera toutes les visualisations et données de joueurs générées précédemment.

## Documentation

Consultez le répertoire `/doc` pour une documentation plus détaillée du projet.