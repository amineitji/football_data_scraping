# whoscored_data_extractor.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import json
import time
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

# --- Début de la fusion de MatchDataExtractor ---

class MatchDataExtractor:
    def __init__(self, html_path, color_json_path="data/color_template.json"):
        self.html_path = html_path
        self.color_json_path = color_json_path

    def _extract_data_html(self):
        raise NotImplementedError("Cette méthode doit être implémentée dans les classes héritées.")
    
    def extract_match_teams(self):
        # Tente d'extraire les équipes du nom de fichier (format ancien)
        match = re.search(r'\d{4}-\d{4}-(.+)', self.html_path)
        if match:
            return match.group(1).replace('-', ' vs ')
        
        # Tente d'extraire les équipes de l'URL (format /Matches/ID/Live/EquipeA-EquipeB)
        # Correction pour gérer la casse (matches ou Matches)
        match_live = re.search(r'/matches/\d+/live/([\w-]+)', self.html_path, re.IGNORECASE)
        if match_live:
             return match_live.group(1).replace('-', ' vs ')

        print("Impossible d'extraire les noms d'équipes depuis l'URL/path.")
        return "Equipe A vs Equipe B"


    def get_competition_from_filename(self):
        """Extracts and formats the competition name from the HTML filename or URL."""
        path_to_search = self.html_path
        filename = os.path.basename(path_to_search)
        
        competition_keywords = [
            "France-Ligue-1", "England-Premier-League", "Italy-Serie-A", "Spain-LaLiga", "Germany-Bundesliga",
            "Europe-Champions-League", "Europe-Europa-League", "Europe-Conference-League", "Angleterre-League-Cup", "Portugal-Liga-Portugal"
        ]

        # Recherche dans le nom de fichier et l'URL
        for keyword in competition_keywords:
            if keyword.lower() in path_to_search.lower():
                parts = keyword.split('-')[1:]
                competition_name = ' '.join(parts)
                return competition_name

        return "Compétition Inconnue"  # Retourne une valeur par défaut

    def load_colors_for_competition(self, competition_name):
        """Loads the colors for the given competition from the JSON file."""
        # Définit les couleurs par défaut directement ici pour simplifier
        default_colors = ("#000000", "#5a5403")
        
        return default_colors

    def get_competition_and_colors(self):
        """Combines competition extraction and color loading."""
        competition = self.get_competition_from_filename()
        color1, color2 = self.load_colors_for_competition(competition)
        return competition, color1, color2

    def extract_player_stats_and_events(self, player_name, output_dir="player_data"):
        raise NotImplementedError("Cette méthode doit être implémentée dans les classes héritées.")

# --- Fin de la fusion de MatchDataExtractor ---


class WhoScoredDataExtractor(MatchDataExtractor):
    
    def __init__(self, html_path=None):
        super().__init__(html_path)
        self.driver = None # Pour stocker l'instance du driver
        self.data = None   # Pour stocker les données scrapées
        self.match_data = None  # Pour stocker les données du match complet
        
    def _get_driver(self):
        """Initialise et retourne une instance de Selenium driver."""
        print("Configuration de Selenium avec le mode headless...")
        options = Options()
        options.headless = True
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36')
        
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

    def _extract_data_from_url(self, driver, url):
        """Extrait les données JSON d'une URL de match donnée."""
        print(f"Chargement de la page WhoScored {url}...")
        driver.get(url)

        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "layout-wrapper")))
        except Exception as e:
            print(f"Erreur d'attente pour {url}: {e}")
            return None

        print("Récupération du contenu HTML...")
        html = driver.page_source

        print("Extraction des données avec le modèle regex...")
        regex_pattern = r'(?<=require\.config\.params\["args"\].=.)[\s\S]*?;'
        
        data_txt_match = re.search(regex_pattern, html)
        
        if not data_txt_match:
            print(f"Regex n'a rien trouvé pour {url}")
            return None

        data_txt = data_txt_match.group(0)
        data_txt = data_txt.replace('matchId', '"matchId"')
        data_txt = data_txt.replace('matchCentreData', '"matchCentreData"')
        data_txt = data_txt.replace('matchCentreEventTypeJson', '"matchCentreEventTypeJson"')
        data_txt = data_txt.replace('formationIdNameMappings', '"formationIdNameMappings"')
        data_txt = data_txt.replace('};', '}')

        try:
            data_json = json.loads(data_txt)
            print("Données JSON extraites avec succès.")
            return data_json
        except json.JSONDecodeError as e:
            print(f"Erreur de décodage JSON pour {url}: {e}")
            return None

    def _extract_data_html(self):
        """Méthode pour extraire les données d'un seul match (self.html_path)."""
        # Si les données sont déjà chargées, ne rien faire
        if self.data:
            print("Données déjà chargées, utilisation du cache.")
            return self.data
            
        driver = self._get_driver()
        try:
            data_json = self._extract_data_from_url(driver, self.html_path)
            self.data = data_json # Stocker les données
            self.match_data = data_json  # Stocker aussi dans match_data pour le réseau d'équipe
        finally:
            print("Fermeture du navigateur Selenium.")
            driver.quit()
        return self.data

    def _extract_list_matchs_html(self):
        """
        Extrait les données de tous les matchs listés sur une page de joueur (agrégé).
        Utilise UNE SEULE instance Selenium pour plus de rapidité.
        """
        driver = self._get_driver()
        all_data = []
        
        try:
            print(f"Chargement de la page joueur : {self.html_path}...")
            driver.get(self.html_path)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "player-fixture")))

            print("Parsing HTML avec BeautifulSoup pour trouver les liens de matchs...")
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            BASE_URL = 'https://www.whoscored.com'
            links = soup.select('a.result-1.rc') # Sélecteur pour les matchs joués
            
            match_urls = []
            for link in links:
                href = link.get('href')
                if href and 'Matches' in href:
                    match_urls.append(BASE_URL + href.replace("/Show/", "/Live/"))

            if not match_urls:
                print("Aucun lien de match trouvé sur la page joueur.")
                return []

            print(f"Trouvé {len(match_urls)} matchs à scraper. Début de la boucle...")

            # Boucle sur les URLs de match en utilisant LE MÊME driver
            for i, match_url in enumerate(match_urls):
                print(f"\n--- Scraping Match {i+1}/{len(match_urls)} ---")
                data_json = self._extract_data_from_url(driver, match_url)
                if data_json:
                    all_data.append(data_json)
                time.sleep(1) # Petite pause pour ne pas surcharger

        except Exception as e:
            print(f"Erreur durant l'extraction de la liste des matchs : {e}")
            traceback.print_exc()
        finally:
            print("Fermeture du navigateur Selenium après la boucle.")
            driver.quit()

        print(f"Fusion complète des données. {len(all_data)} matchs scrapés.")
        return all_data

    def get_player_list(self):
        """
        Scrape les données du match (si pas déjà fait) et retourne 
        une liste formatée des joueurs.
        """
        if not self.data:
            print("Aucune donnée chargée. Lancement de l'extraction...")
            if not self.html_path:
                print("Erreur: Aucune URL n'a été définie.")
                return None
            self._extract_data_html() # Charge les données dans self.data

        if not self.data:
            print("Erreur: Impossible d'extraire les données.")
            return None
        
        try:
            name_dict = self.data['matchCentreData']['playerIdNameDictionary']
            home_players_raw = self.data['matchCentreData']['home']['players']
            away_players_raw = self.data['matchCentreData']['away']['players']

            player_list = []
            
            # Formatter la liste
            player_list.append((f"--- {self.data['matchCentreData']['home']['name'].upper()} (DOMICILE) ---", None, False))
            # Trier les titulaires d'abord
            home_players_raw.sort(key=lambda x: not x.get('isFirstEleven', False))
            for p in home_players_raw:
                player_list.append((name_dict[str(p['playerId'])], "home", p.get('isFirstEleven', False)))

            player_list.append((f"--- {self.data['matchCentreData']['away']['name'].upper()} (EXTÉRIEUR) ---", None, False))
            # Trier les titulaires d'abord
            away_players_raw.sort(key=lambda x: not x.get('isFirstEleven', False))
            for p in away_players_raw:
                    player_list.append((name_dict[str(p['playerId'])], "away", p.get('isFirstEleven', False)))

            return player_list
        
        except KeyError as e:
            print(f"Erreur de clé lors de la recherche des joueurs: {e}")
            return None

    def extract_player_stats_and_events(self, player_name, output_dir="player_data"):
        """Extrait les stats et événements du joueur sur WhoScored pour UN match."""
        
        # Vérifie si les données sont déjà chargées par get_player_list
        if not self.data:
            print("Données non trouvées, lancement de l'extraction (stats)...")
            if not self.html_path:
                print("Erreur: URL non définie.")
                return None
            self._extract_data_html() # Charge les données dans self.data
        
        if not self.data:
            print("Erreur: Aucune donnée n'a pu être extraite.")
            return None
            
        print(f"Extraction des stats de match pour {player_name}...")
        os.makedirs(output_dir, exist_ok=True)

        player_id = None
        try:
            for pid, name in self.data['matchCentreData']['playerIdNameDictionary'].items():
                if name.lower() == player_name.lower():
                    player_id = pid
                    break
        except KeyError:
             print("Erreur: 'matchCentreData' ou 'playerIdNameDictionary' non trouvé dans les données.")
             return None

        if not player_id:
            print(f"Joueur '{player_name}' non trouvé.")
            return None

        events = self.data["matchCentreData"].get("events", [])
        player_events = [event for event in events if event.get('playerId') == int(player_id)]

        player_stats = None
        team = None

        for team_type in ["home", "away"]:
            for player in self.data["matchCentreData"][team_type]["players"]:
                if player["playerId"] == int(player_id):
                    player_stats = player
                    team = team_type
                    break
            if player_stats:
                break

        if not player_stats:
            print(f"Stats du joueur '{player_name}' non trouvées.")
            return None

        player_combined_data = {
            "player_name": player_name,
            # CORRECTION: Utiliser 'playerId' et le convertir en int pour DuoVisualizer
            "playerId": int(player_id), 
            "team": team,
            "position": player_stats.get("position"),
            "shirtNo": player_stats.get("shirtNo"),
            "height": player_stats.get("height"),
            "weight": player_stats.get("weight"),
            "age": player_stats.get("age"),
            "isFirstEleven": player_stats.get("isFirstEleven"),
            "isManOfTheMatch": player_stats.get("isManOfTheMatch"),
            "stats": player_stats.get("stats"),
            "events": player_events
        }

        # Utilise l'ID du match pour un nom de fichier unique (version corrigée et robuste)
        try:
            match = re.search(r"/matches/(\d+)/", self.html_path, re.IGNORECASE)
            if not match:
                raise ValueError("Impossible d'extraire l'ID du match de l'URL")
            match_id = match.group(1)
        except Exception as e:
            print(f"Avertissement: Impossible d'extraire l'ID du match de l'URL ({e}). Utilisation d'un ID par défaut 'match'.")
            match_id = "match" # Fallback
            
        output_file = os.path.join(output_dir, f"{player_name.replace(' ', '_')}_{match_id}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(player_combined_data, f, ensure_ascii=False, indent=4)

        print(f"Les données du match pour '{player_name}' ont été enregistrées dans {output_file}")
        return output_file
    
    def extract_player_aggregate_stats(self, player_name, output_dir="player_data"):
        """Extrait et agrège les stats et événements du joueur sur plusieurs matchs WhoScored."""
        print(f"Extraction des données agrégées pour {player_name}...")

        # Utilise la nouvelle méthode optimisée
        self.data_list = self._extract_list_matchs_html()
        os.makedirs(output_dir, exist_ok=True)

        all_events = []
        positions_count = {}
        first_eleven_count = 0
        motm_count = 0
        aggregated_stats = {}
        player_id = None
        height = weight = age = None
        total_matches_processed = 0

        if not self.data_list:
            print("Aucune donnée de match n'a été extraite.")
            return None

        for match_data in self.data_list:
            match_centre = match_data.get("matchCentreData")
            if not match_centre:
                print("Données de match invalides, passage au suivant.")
                continue

            current_player_id = None
            for pid, name in match_centre.get("playerIdNameDictionary", {}).items():
                if name.lower() == player_name.lower():
                    current_player_id = pid
                    if not player_id: # Sauvegarde du premier ID trouvé
                        player_id = pid
                    break
            
            if not current_player_id:
                # print(f"Joueur '{player_name}' non trouvé dans un des matchs.")
                continue # Passe au match suivant

            events = match_centre.get("events", [])
            player_events = [event for event in events if event.get('playerId') == int(current_player_id)]
            all_events.extend(player_events)

            player_stats = None
            for team_type in ["home", "away"]:
                for player in match_centre.get(team_type, {}).get("players", []):
                    if player.get("playerId") == int(current_player_id):
                        player_stats = player
                        break
                if player_stats:
                    break

            if not player_stats:
                print(f"Stats de '{player_name}' non trouvées pour un match.")
                continue
            
            total_matches_processed += 1
            pos = player_stats.get("position")
            if pos:
                positions_count[pos] = positions_count.get(pos, 0) + 1

            if player_stats.get("isFirstEleven"):
                first_eleven_count += 1
            if player_stats.get("isManOfTheMatch"):
                motm_count += 1
            if not height: height = player_stats.get("height")
            if not weight: weight = player_stats.get("weight")
            if not age: age = player_stats.get("age")

            # Agrégation des stats
            for stat_key, stat_value in player_stats.get("stats", {}).items():
                if stat_key not in aggregated_stats:
                    aggregated_stats[stat_key] = {} # Initialise un dict pour chaque stat
                
                if isinstance(stat_value, dict):
                    for sub_key, sub_val in stat_value.items():
                        if isinstance(sub_val, (int, float)):
                            aggregated_stats[stat_key][sub_key] = aggregated_stats[stat_key].get(sub_key, 0) + sub_val
                elif isinstance(stat_value, (int, float)):
                     # Pour les stats qui ne sont pas des dicts (ex: 'rating')
                     aggregated_stats[stat_key] = aggregated_stats.get(stat_key, 0) + stat_value


        if not player_id:
            print(f"Joueur '{player_name}' non trouvé dans aucun match.")
            return None

        player_combined_data = {
            "player_name": player_name,
            "player_id": player_id,
            "position": positions_count, # Dict des positions jouées
            "height": height,
            "weight": weight,
            "age": age,
            "total_matches": total_matches_processed,
            "isFirstEleven_count": first_eleven_count,
            "isManOfTheMatch_count": motm_count,
            "stats": aggregated_stats,
            "events": all_events
        }

        output_file = os.path.join(output_dir, f"{player_name.replace(' ', '_')}_aggregated.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(player_combined_data, f, ensure_ascii=False, indent=4)

        print(f"Données agrégées pour '{player_name}' (basées sur {total_matches_processed} matchs) enregistrées dans {output_file}")
        return output_file
    
    def get_full_match_data(self):
        """Récupère toutes les données du match (pour le réseau d'équipe)."""
        # Si self.data est chargé, self.match_data l'est aussi
        if not self.match_data:
            print("⏳ Chargement des données du match...")
            self._extract_data_html()
        
        # Retourne les données brutes complètes (JSON)
        return self.match_data