from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os


class MatchDataExtractor:
    def __init__(self, html_path, color_json_path="data/color_template.json"):
        self.html_path = html_path
        self.color_json_path = color_json_path
        self.data = self._extract_data_html()

    def _extract_data_html(self):
        print("Configuration de Selenium avec le mode headless...")
        options = Options()
        options.headless = True
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36')

        driver = webdriver.Chrome(options=options)

        # Désactiver la détection de Selenium par les sites
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"Chargement de la page {self.html_path}...")
        driver.get(self.html_path)

        # Attente explicite que la page soit complètement chargée (exemple : attendre l'élément body)
        print("Attente que la page se charge complètement...")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Récupération du contenu HTML après le chargement complet
        print("Récupération du contenu HTML...")
        html = driver.page_source

        print("Fermeture du navigateur Selenium...")
        driver.quit()

        # Suppression de l'analyse avec BeautifulSoup car non utilisée
        print("Extraction des données avec le modèle regex...")
        regex_pattern = r'(?<=require\.config\.params\["args"\].=.)[\s\S]*?;'
        data_txt = re.findall(regex_pattern, html)[0]

        print("Nettoyage des données pour le format JSON...")
        data_txt = data_txt.replace('matchId', '"matchId"')
        data_txt = data_txt.replace('matchCentreData', '"matchCentreData"')
        data_txt = data_txt.replace('matchCentreEventTypeJson', '"matchCentreEventTypeJson"')
        data_txt = data_txt.replace('formationIdNameMappings', '"formationIdNameMappings"')
        data_txt = data_txt.replace('};', '}')

        print("Conversion des données extraites en JSON...")
        data_json = json.loads(data_txt)

        print("Extraction et conversion terminées.")
        return data_json

    def get_competition_from_filename(self):
        """Extracts and formats the competition name from the HTML filename."""
        filename = os.path.basename(self.html_path)
        competition_keywords = [
            "France-Ligue-1", "England-Premier-League", "Italy-Serie-A", "Spain-LaLiga", "Germany-Bundesliga",
            "Europe-Champions-League", "Europe-Europa-League", "Europe-Conference-League", "Angleterre-League-Cup"
        ]

        for keyword in competition_keywords:
            if keyword.lower() in filename.lower():
                # Split the keyword by hyphen and remove the first word
                parts = keyword.split('-')[1:]
                # Join the remaining parts with spaces
                competition_name = ' '.join(parts)
                return competition_name

        return None  # Return None if no competition is found

    def load_colors_for_competition(self, competition_name):
        """Loads the colors for the given competition from the JSON file."""
        try:
            with open(self.color_json_path, 'r') as f:
                colors_data = json.load(f)
        except FileNotFoundError:
            print(f"JSON file '{self.color_json_path}' not found.")
            return "#FFFFFF", "#000000"  # Default colors in case of an error

        # Get the colors for the competition
        competition_colors = colors_data.get("competitions", {}).get(competition_name)
        if competition_colors:
            return competition_colors["color1"], competition_colors["color2"]
        else:
            return "#FFFFFF", "#000000"  # Default colors if not found

    def get_competition_and_colors(self):
        """Combines competition extraction and color loading."""
        competition = self.get_competition_from_filename()
        if competition:
            color1, color2 = self.load_colors_for_competition(competition)
            return competition, color1, color2
        else:
            return "Unknown Competition", "#FFFFFF", "#000000"

    def extract_player_stats_and_events(self, player_name, output_dir="player_data"):
        print("Extraction des données pour le joueur - ", player_name)

        # Créer un répertoire pour stocker les fichiers JSON
        os.makedirs(output_dir, exist_ok=True)

        # Trouver l'ID du joueur à partir du nom
        player_id = None
        for pid, name in self.data['matchCentreData']['playerIdNameDictionary'].items():
            if name.lower() == player_name.lower():
                player_id = pid
                break

        if not player_id:
            return f"Player '{player_name}' not found."

        # Extraction des événements
        events = self.data["matchCentreData"]["events"]
        player_events = [event for event in events if event.get('playerId') == int(player_id)]

        # Recherche du joueur dans home["players"] et away["players"]
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
            return f"Player '{player_name}' stats not found in either team."

        # Combinaison des données
        player_combined_data = {
            "player_name": player_name,
            "player_id": player_id,
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

        # Extraire le nom du fichier à partir du chemin HTML
        match_name = os.path.basename(self.html_path).replace("data/", "").replace(".html", "")

        # Créer le nom du fichier de sortie en combinant player_name et match_name
        output_file = os.path.join(output_dir, f"{player_name.replace(' ', '_')}_{match_name}.json")
        
        # Enregistrer les données combinées dans un fichier JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(player_combined_data, f, ensure_ascii=False, indent=4)

        print(f"Les données combinées pour le joueur '{player_name}' ont été enregistrées dans {output_file}")
        return output_file
