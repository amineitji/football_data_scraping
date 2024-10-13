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
from match_data_extractor import MatchDataExtractor

class WhoScoredDataExtractor(MatchDataExtractor):
    def _extract_data_html(self):
        """Méthode spécifique pour extraire les données d'une page WhoScored."""
        print("Configuration de Selenium avec le mode headless...")
        options = Options()
        options.headless = True
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36')

        driver = webdriver.Chrome(options=options)

        # Désactiver la détection de Selenium par les sites
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"Chargement de la page WhoScored {self.html_path}...")
        driver.get(self.html_path)

        # Attente que la page se charge
        print("Attente que la page se charge complètement...")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Récupération du contenu HTML après le chargement complet
        print("Récupération du contenu HTML...")
        html = driver.page_source

        print("Fermeture du navigateur Selenium...")
        driver.quit()

        # Extraction des données avec regex spécifique à WhoScored
        print("Extraction des données avec le modèle regex pour WhoScored...")
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

    def extract_player_stats_and_events(self, player_name, output_dir="player_data"):
        """Extrait les stats et événements du joueur sur WhoScored."""
        print("Extraction des données pour le joueur - ", player_name)

        os.makedirs(output_dir, exist_ok=True)

        player_id = None
        for pid, name in self.data['matchCentreData']['playerIdNameDictionary'].items():
            if name.lower() == player_name.lower():
                player_id = pid
                break

        if not player_id:
            return f"Player '{player_name}' not found."

        events = self.data["matchCentreData"]["events"]
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
            return f"Player '{player_name}' stats not found in either team."

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

        match_name = os.path.basename(self.html_path).replace("data/", "").replace(".html", "")
        output_file = os.path.join(output_dir, f"{player_name.replace(' ', '_')}_{match_name}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(player_combined_data, f, ensure_ascii=False, indent=4)

        print(f"Les données combinées pour le joueur '{player_name}' ont été enregistrées dans {output_file}")
        return output_file
