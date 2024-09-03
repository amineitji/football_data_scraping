import re
import json
import os

class MatchDataExtractor:
    def __init__(self, html_path):
        self.html_path = html_path
        self.data = self._extract_data_html()

    def _extract_data_html(self):
        with open(self.html_path, 'r') as html_file:
            html = html_file.read()

        regex_pattern = r'(?<=require\.config\.params\["args"\].=.)[\s\S]*?;'
        data_txt = re.findall(regex_pattern, html)[0]

        # Add quotations for JSON parser
        data_txt = data_txt.replace('matchId', '"matchId"')
        data_txt = data_txt.replace('matchCentreData', '"matchCentreData"')
        data_txt = data_txt.replace('matchCentreEventTypeJson', '"matchCentreEventTypeJson"')
        data_txt = data_txt.replace('formationIdNameMappings', '"formationIdNameMappings"')
        data_txt = data_txt.replace('};', '}')

        # Convert extracted data to JSON
        data_json = json.loads(data_txt)

        return data_json

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

        # Créer le fichier JSON avec les données combinées
        output_file = os.path.join(output_dir, f"{player_name.replace(' ', '_')}_combined_data.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(player_combined_data, f, ensure_ascii=False, indent=4)

        print(f"Les données combinées pour le joueur '{player_name}' ont été enregistrées dans {output_file}")
        return output_file
