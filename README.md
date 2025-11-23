# ⚽ Projet de visualisation des données de joueurs WhoScored

> Outil d'analyse et de visualisation avancée des performances de joueurs de football à partir des données WhoScored

**Auteur**: ITJI Amine

---

## 🆕 Nouvelles fonctionnalités (v2.0)

### ✨ Multi-sélection de joueurs
Analysez **plusieurs joueurs en une seule exécution** :
- **Un seul joueur** : `5`
- **Plusieurs joueurs** : `1,3,7,12` (séparés par des virgules)
- **Tous les joueurs** : `all` ou `tous`

### 🎯 Flèche de sens du jeu
Toutes les visualisations (y compris la carte des passes) affichent maintenant la flèche indiquant le sens du jeu.

---

## 📁 Structure du projet

```
.
├── src/                    # Code source principal
│   ├── main.py            # Script principal interactif
│   ├── visualizer.py      # Générateur de visualisations
│   ├── whoscored_data_extractor.py  # Extracteur de données
│   └── player_image_downloader.py   # Téléchargeur de photos
├── doc/                   # Documentation
├── data/                  # Données des matchs
│   ├── html/             # Pages HTML scrapées
│   └── photo/            # Photos des joueurs (Transfermarkt)
├── viz_data/             # Visualisations générées (organisées par joueur)
├── player_data/          # Données JSON extraites
├── env/                  # Environnement virtuel Python
├── requirements.txt      # Dépendances Python
├── Makefile             # Automatisation des tâches
└── README.md            # Ce fichier
```

---

## 🚀 Installation rapide

### 1. Cloner le dépôt
```bash
git clone <url_du_dépôt>
cd <répertoire_du_projet>
```

### 2. Configuration de l'environnement
```bash
# Créer l'environnement virtuel
make setup

# Activer l'environnement
source env/bin/activate

# Installer les dépendances système et Python
sudo apt install chromium-chromedriver  # Pour Selenium
make install
```

### 3. Tester l'installation
```bash
make test
```

---

## 🎮 Utilisation

### Mode interactif (recommandé)

```bash
make run
```

Le script vous guidera à travers les étapes suivantes :

1. **Entrer l'URL du match** (WhoScored)
   ```
   https://www.whoscored.com/Matches/1234567/Live/...
   ```

2. **Sélectionner le(s) joueur(s)**
   ```
   LISTE DES JOUEURS DU MATCH
   ══════════════════════════════════════════════════
   🏠 Équipe domicile
     1: Kylian Mbappé (Titulaire)
     2: Antoine Griezmann (Titulaire)
     3: N'Golo Kanté (Titulaire)
     ...
   
   🚶 Équipe visiteuse
     12: Cristiano Ronaldo (Titulaire)
     13: Bruno Fernandes (Titulaire)
     ...
   ══════════════════════════════════════════════════
   
   Vous pouvez choisir:
     - Un seul joueur: entrez son numéro (ex: 5)
     - Plusieurs joueurs: entrez les numéros séparés par des virgules (ex: 1,3,7)
     - Tous les joueurs: entrez 'all' ou 'tous'
   
   Votre choix: 1,2,3
   ```

3. **Renseigner le poste** (appliqué à tous si multi-sélection)
   ```
   Poste du joueur (DEF, MIL, ATT) : ATT
   ```

4. **Nombre de passes décisives** (optionnel, par défaut = 0)
   ```
   Nombre de passes décisives : 2
   ```

### Exemples d'usage

#### Analyser un seul joueur
```
Votre choix: 5
✅ Joueur(s) choisi(s) : Paul Pogba

Poste du joueur (DEF, MIL, ATT) : MIL
Nombre de passes décisives : 2

============================================================
📊 Analyse 1/1: Paul Pogba (MIL), 2 passe(s) D.
============================================================
✅ Analyse terminée pour Paul Pogba
```

#### Analyser plusieurs joueurs
```
Votre choix: 1,3,7,12
✅ Joueur(s) choisi(s) : Mbappé, Kanté, Benzema, Modric

Poste du joueur (DEF, MIL, ATT) : MIL
Nombre de passes décisives : 0

============================================================
📊 Analyse 1/4: Mbappé (MIL), 0 passe(s) D.
============================================================
...
✅ Analyse terminée pour Mbappé

============================================================
📊 Analyse 2/4: Kanté (MIL), 0 passe(s) D.
============================================================
...
```

#### Analyser tous les joueurs
```
Votre choix: all
✅ Joueur(s) choisi(s) : [22 joueurs]

Poste du joueur (DEF, MIL, ATT) : MIL
Nombre de passes décisives : 0
```

### Analyse de saison (agrégée)

Pour analyser les données agrégées d'un joueur sur toute une saison :

```bash
make run
# Entrer l'URL de type: https://www.whoscored.com/players/363181/...
# Le script détectera automatiquement le mode "saison"
```

---

## 📊 Visualisations générées

Pour chaque joueur, 4 visualisations PNG sont créées :

### 1. **Activité générale** (`*_match_all_[POSTE].png`)
- Heatmap de présence
- Toutes les actions (passes, dribbles, tirs, tacles, etc.)
- Statistiques complètes

### 2. **Activité offensive** (`*_match_offensive_[POSTE].png`)
- Focus sur : Dribbles, Tirs, Passes clés, Fautes subies
- Légende dynamique avec succès/échecs

### 3. **Activité défensive** (`*_match_defensive_[POSTE].png`)
- Focus sur : Tacles, Interceptions, Récupérations, Fautes commises
- Analyse de la densité défensive

### 4. **Carte des passes** (`*_match_passes.png`)
- Toutes les passes (réussies en vert, ratées en rouge)
- Statistiques de direction (avant/latérales/arrière)
- **Nouveau** : Flèche de sens du jeu

### Structure de sortie
```
viz_data/
├── Kylian_Mbappé/
│   └── match_1234567/
│       ├── Kylian_Mbappé_match_all_ATT.png
│       ├── Kylian_Mbappé_match_offensive_ATT.png
│       ├── Kylian_Mbappé_match_defensive_ATT.png
│       └── Kylian_Mbappé_match_passes.png
├── Antoine_Griezmann/
│   └── match_1234567/
│       └── ...
```

---

## 🧹 Commandes de maintenance

```bash
# Nettoyer tous les fichiers générés
make clean

# Nettoyer uniquement les visualisations
make clean-viz

# Nettoyer uniquement les données JSON
make clean-data

# Afficher le statut du projet
make status
```

### Exemple de `make status`
```
📊 STATUT DU PROJET
==================
🐍 Version Python: Python 3.10.12
📁 Fichiers de visualisation: 48 PNG
📄 Fichiers de données: 12 JSON
📸 Photos de joueurs: 12 JPG
```

---

## 🛠️ Technologies utilisées

- **Python 3.x**
- **Selenium** : Scraping dynamique des pages WhoScored
- **BeautifulSoup4** : Parsing HTML
- **mplsoccer** : Visualisations de terrain de football
- **Matplotlib** : Génération de graphiques
- **NumPy / SciPy** : Calculs et heatmaps
- **Requests** : Téléchargement de photos (Transfermarkt)

---

## ⚙️ Configuration avancée

### Variables d'environnement (optionnel)
Vous pouvez personnaliser certains paramètres dans le code :
- **Taille des markers** : `marker_size` dans `MatchVisualizer`
- **Couleurs des équipes** : Extraites automatiquement depuis WhoScored
- **Résolution des images** : `figsize=(16, 16)` dans `_create_base_layout()`

---

## 🐛 Dépannage

### Erreur "chromium-chromedriver not found"
```bash
sudo apt install chromium-chromedriver
```

### Erreur "Module not found"
```bash
source env/bin/activate
pip install -r requirements.txt
```

### Timeout Selenium
- Vérifiez votre connexion Internet
- Certaines pages WhoScored peuvent nécessiter plus de temps (timeout configurable dans `whoscored_data_extractor.py`)

### Photo Transfermarkt non trouvée
- Le script continue même si la photo échoue
- Vérifiez l'orthographe exacte du nom du joueur
- Certains joueurs peu connus peuvent ne pas avoir de profil Transfermarkt

---

## 📝 Notes importantes

### Performance
- **1 joueur** : ~30-60 secondes
- **5 joueurs** : ~2-5 minutes
- **22 joueurs** : ~8-20 minutes (cache photos Transfermarkt)

### Limites
- Le **poste** et le **nombre de passes décisives** sont appliqués uniformément à tous les joueurs en multi-sélection
- Les données dépendent de la disponibilité et de l'exactitude de WhoScored
- Nécessite une connexion Internet active

### Bonnes pratiques
- Utilisez le **cache des photos** : une fois téléchargée, la photo d'un joueur est réutilisée
- Pour analyser toute une équipe, utilisez `all` puis filtrez manuellement si besoin
- Organisez vos analyses par match dans des dossiers séparés

---

## 📚 Documentation complémentaire

Consultez le répertoire `/doc` pour :
- Architecture détaillée du code
- Guide de contribution
- Exemples avancés

---

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 👨‍💻 Auteur

**ITJI Amine**
- Portfolio : [TarbouchData](https://tarbouchdata.com)
- Twitter : [@TarbouchData](https://twitter.com/TarbouchData)

---

## 🙏 Remerciements

- WhoScored pour les données de match
- Transfermarkt pour les photos de joueurs
- La communauté mplsoccer pour l'excellente bibliothèque de visualisation

---

**Version** : 2.0 (Novembre 2024)
**Dernière mise à jour** : 2024-11-18# ⚽ Projet de visualisation des données de joueurs WhoScored

> Outil d'analyse et de visualisation avancée des performances de joueurs de football à partir des données WhoScored

**Auteur**: ITJI Amine

---

## 🆕 Nouvelles fonctionnalités (v2.0)

### ✨ Multi-sélection de joueurs
Analysez **plusieurs joueurs en une seule exécution** :
- **Un seul joueur** : `5`
- **Plusieurs joueurs** : `1,3,7,12` (séparés par des virgules)
- **Tous les joueurs** : `all` ou `tous`

### 🎯 Flèche de sens du jeu
Toutes les visualisations (y compris la carte des passes) affichent maintenant la flèche indiquant le sens du jeu.

---

## 📁 Structure du projet

```
.
├── src/                    # Code source principal
│   ├── main.py            # Script principal interactif
│   ├── visualizer.py      # Générateur de visualisations
│   ├── whoscored_data_extractor.py  # Extracteur de données
│   └── player_image_downloader.py   # Téléchargeur de photos
├── doc/                   # Documentation
├── data/                  # Données des matchs
│   ├── html/             # Pages HTML scrapées
│   └── photo/            # Photos des joueurs (Transfermarkt)
├── viz_data/             # Visualisations générées (organisées par joueur)
├── player_data/          # Données JSON extraites
├── env/                  # Environnement virtuel Python
├── requirements.txt      # Dépendances Python
├── Makefile             # Automatisation des tâches
└── README.md            # Ce fichier
```

---

## 🚀 Installation rapide

### 1. Cloner le dépôt
```bash
git clone <url_du_dépôt>
cd <répertoire_du_projet>
```

### 2. Configuration de l'environnement
```bash
# Créer l'environnement virtuel
make setup

# Activer l'environnement
source env/bin/activate

# Installer les dépendances système et Python
sudo apt install chromium-chromedriver  # Pour Selenium
make install
```

### 3. Tester l'installation
```bash
make test
```

---

## 🎮 Utilisation

### Mode interactif (recommandé)

```bash
make run
```

Le script vous guidera à travers les étapes suivantes :

1. **Entrer l'URL du match** (WhoScored)
   ```
   https://www.whoscored.com/Matches/1234567/Live/...
   ```

2. **Sélectionner le(s) joueur(s)**
   ```
   LISTE DES JOUEURS DU MATCH
   ══════════════════════════════════════════════════
   🏠 Équipe domicile
     1: Kylian Mbappé (Titulaire)
     2: Antoine Griezmann (Titulaire)
     3: N'Golo Kanté (Titulaire)
     ...
   
   🚶 Équipe visiteuse
     12: Cristiano Ronaldo (Titulaire)
     13: Bruno Fernandes (Titulaire)
     ...
   ══════════════════════════════════════════════════
   
   Vous pouvez choisir:
     - Un seul joueur: entrez son numéro (ex: 5)
     - Plusieurs joueurs: entrez les numéros séparés par des virgules (ex: 1,3,7)
     - Tous les joueurs: entrez 'all' ou 'tous'
   
   Votre choix: 1,2,3
   ```

3. **Renseigner le poste** (appliqué à tous si multi-sélection)
   ```
   Poste du joueur (DEF, MIL, ATT) : ATT
   ```

4. **Nombre de passes décisives** (optionnel, par défaut = 0)
   ```
   Nombre de passes décisives : 2
   ```

### Exemples d'usage

#### Analyser un seul joueur
```
Votre choix: 5
✅ Joueur(s) choisi(s) : Paul Pogba

Poste du joueur (DEF, MIL, ATT) : MIL
Nombre de passes décisives : 2

============================================================
📊 Analyse 1/1: Paul Pogba (MIL), 2 passe(s) D.
============================================================
✅ Analyse terminée pour Paul Pogba
```

#### Analyser plusieurs joueurs
```
Votre choix: 1,3,7,12
✅ Joueur(s) choisi(s) : Mbappé, Kanté, Benzema, Modric

Poste du joueur (DEF, MIL, ATT) : MIL
Nombre de passes décisives : 0

============================================================
📊 Analyse 1/4: Mbappé (MIL), 0 passe(s) D.
============================================================
...
✅ Analyse terminée pour Mbappé

============================================================
📊 Analyse 2/4: Kanté (MIL), 0 passe(s) D.
============================================================
...
```

#### Analyser tous les joueurs
```
Votre choix: all
✅ Joueur(s) choisi(s) : [22 joueurs]

Poste du joueur (DEF, MIL, ATT) : MIL
Nombre de passes décisives : 0
```

### Analyse de saison (agrégée)

Pour analyser les données agrégées d'un joueur sur toute une saison :

```bash
make run
# Entrer l'URL de type: https://www.whoscored.com/players/363181/...
# Le script détectera automatiquement le mode "saison"
```

---

## 📊 Visualisations générées

Pour chaque joueur, 4 visualisations PNG sont créées :

### 1. **Activité générale** (`*_match_all_[POSTE].png`)
- Heatmap de présence
- Toutes les actions (passes, dribbles, tirs, tacles, etc.)
- Statistiques complètes

### 2. **Activité offensive** (`*_match_offensive_[POSTE].png`)
- Focus sur : Dribbles, Tirs, Passes clés, Fautes subies
- Légende dynamique avec succès/échecs

### 3. **Activité défensive** (`*_match_defensive_[POSTE].png`)
- Focus sur : Tacles, Interceptions, Récupérations, Fautes commises
- Analyse de la densité défensive

### 4. **Carte des passes** (`*_match_passes.png`)
- Toutes les passes (réussies en vert, ratées en rouge)
- Statistiques de direction (avant/latérales/arrière)
- **Nouveau** : Flèche de sens du jeu

### Structure de sortie
```
viz_data/
├── Kylian_Mbappé/
│   └── match_1234567/
│       ├── Kylian_Mbappé_match_all_ATT.png
│       ├── Kylian_Mbappé_match_offensive_ATT.png
│       ├── Kylian_Mbappé_match_defensive_ATT.png
│       └── Kylian_Mbappé_match_passes.png
├── Antoine_Griezmann/
│   └── match_1234567/
│       └── ...
```

---

## 🧹 Commandes de maintenance

```bash
# Nettoyer tous les fichiers générés
make clean

# Nettoyer uniquement les visualisations
make clean-viz

# Nettoyer uniquement les données JSON
make clean-data

# Afficher le statut du projet
make status
```

### Exemple de `make status`
```
📊 STATUT DU PROJET
==================
🐍 Version Python: Python 3.10.12
📁 Fichiers de visualisation: 48 PNG
📄 Fichiers de données: 12 JSON
📸 Photos de joueurs: 12 JPG
```

---

## 🛠️ Technologies utilisées

- **Python 3.x**
- **Selenium** : Scraping dynamique des pages WhoScored
- **BeautifulSoup4** : Parsing HTML
- **mplsoccer** : Visualisations de terrain de football
- **Matplotlib** : Génération de graphiques
- **NumPy / SciPy** : Calculs et heatmaps
- **Requests** : Téléchargement de photos (Transfermarkt)

---

## ⚙️ Configuration avancée

### Variables d'environnement (optionnel)
Vous pouvez personnaliser certains paramètres dans le code :
- **Taille des markers** : `marker_size` dans `MatchVisualizer`
- **Couleurs des équipes** : Extraites automatiquement depuis WhoScored
- **Résolution des images** : `figsize=(16, 16)` dans `_create_base_layout()`

---

## 🐛 Dépannage

### Erreur "chromium-chromedriver not found"
```bash
sudo apt install chromium-chromedriver
```

### Erreur "Module not found"
```bash
source env/bin/activate
pip install -r requirements.txt
```

### Timeout Selenium
- Vérifiez votre connexion Internet
- Certaines pages WhoScored peuvent nécessiter plus de temps (timeout configurable dans `whoscored_data_extractor.py`)

### Photo Transfermarkt non trouvée
- Le script continue même si la photo échoue
- Vérifiez l'orthographe exacte du nom du joueur
- Certains joueurs peu connus peuvent ne pas avoir de profil Transfermarkt

---

## 📝 Notes importantes

### Performance
- **1 joueur** : ~30-60 secondes
- **5 joueurs** : ~2-5 minutes
- **22 joueurs** : ~8-20 minutes (cache photos Transfermarkt)

### Limites
- Le **poste** et le **nombre de passes décisives** sont appliqués uniformément à tous les joueurs en multi-sélection
- Les données dépendent de la disponibilité et de l'exactitude de WhoScored
- Nécessite une connexion Internet active

### Bonnes pratiques
- Utilisez le **cache des photos** : une fois téléchargée, la photo d'un joueur est réutilisée
- Pour analyser toute une équipe, utilisez `all` puis filtrez manuellement si besoin
- Organisez vos analyses par match dans des dossiers séparés

---

## 📚 Documentation complémentaire

Consultez le répertoire `/doc` pour :
- Architecture détaillée du code
- Guide de contribution
- Exemples avancés

---

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 👨‍💻 Auteur

**ITJI Amine**
- Portfolio : [TarbouchData](https://tarbouchdata.com)
- Twitter : [@TarbouchData](https://twitter.com/TarbouchData)

---

