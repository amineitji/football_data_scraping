from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import requests
import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from match_data_extractor import MatchDataExtractor
from datetime import datetime

class SofaScoreDataExtractor(MatchDataExtractor):

    def _extract_data_html(self):
        """Méthode spécifique pour extraire les données via des appels API SofaScore."""

        # Extraire l'ID de l'événement à partir de l'URL dans self.html_path
        match = re.search(r'#id:(\d+)', self.html_path)
        if not match:
            print("Erreur: Impossible d'extraire l'ID de l'événement depuis l'URL.")
            return {}, None  # Retourne un JSON vide et un event_id nul si l'extraction échoue

        event_id = match.group(1)
        print(f"ID de l'événement extrait: {event_id}")

        # URL de l'API lineups pour cet événement
        lineups_url = f"https://www.sofascore.com/api/v1/event/{event_id}/lineups"

        # Effectuer la requête GET à l'API lineups
        try:
            response = requests.get(lineups_url)
            if response.status_code == 200:
                # Retourner le JSON et l'event_id si la requête a réussi
                return response.json(), event_id
            else:
                print(f"Erreur lors de la récupération des données lineups, statut: {response.status_code}")
                return {}, event_id  # Retourne un JSON vide et l'event_id si la requête échoue
        except Exception as e:
            print(f"Erreur lors de l'appel API pour les lineups: {str(e)}")
            return {}, event_id  # Retourne un JSON vide et l'event_id en cas d'exception

    def extract_player_stats_and_events(self, player_name, output_dir="player_data"):
        """Extrait les stats, événements, la heatmap et les shots/goals d'un joueur sur SofaScore, renvoie une structure JSON."""
        print(f"Extraction des données pour le joueur - {player_name} (SofaScore)")
    
        # Appel à la méthode _extract_data_html pour obtenir les données lineups
        lineups_data, match_id = self._extract_data_html()
        if not lineups_data:
            print("Erreur : Aucune donnée lineups trouvée.")
            return None
    
        # Création du répertoire de sortie
        os.makedirs(output_dir, exist_ok=True)
    
        # Template pour les données combinées du joueur
        player_combined_data = {
            "player_name": player_name,
            "player_id": None,
            "team": None,
            "position": None,
            "shirtNo": None,
            "height": None,
            "weight": None,
            "age": None,  # On remplira cette valeur plus tard
            "isFirstEleven": None,
            "isManOfTheMatch": None,
            "stats": {},
            "events": []  # Cet array sera rempli par les événements basés sur la heatmap et shotmap
        }
    
        # Fonction pour calculer l'âge à partir d'un timestamp UNIX
        def calculate_age(timestamp):
            birth_date = datetime.utcfromtimestamp(timestamp)
            today = datetime.today()
            age = today.year - birth_date.year
            if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
                age -= 1
            return age
    
        # Recherche du joueur dans les données lineups (home et away teams)
        player_id = None
        for team_key in ['home', 'away']:
            for player in lineups_data.get(team_key, {}).get('players', []):
                if player['player']['name'].lower() == player_name.lower():
                    player_id = player['player']['id']
                    player_combined_data["player_id"] = player_id
                    player_combined_data["team"] = team_key
                    player_combined_data["position"] = player['player'].get("position", None)
                    player_combined_data["shirtNo"] = player['player'].get("jerseyNumber", None)
                    player_combined_data["height"] = player['player'].get("height", None)
                    player_combined_data["weight"] = player['player'].get("weight", None)
    
                    # Calcul de l'âge à partir du timestamp de date de naissance
                    birth_timestamp = player['player'].get("dateOfBirthTimestamp", None)
                    if birth_timestamp:
                        player_combined_data["age"] = calculate_age(birth_timestamp)
    
                    player_combined_data["isFirstEleven"] = not player.get("substitute", False)
                    player_combined_data["isManOfTheMatch"] = player.get("isManOfTheMatch", False)
                    player_combined_data["stats"] = player.get("statistics", {})
                    break
            if player_id:
                break
            
        if not player_id:
            print(f"Erreur: Aucun joueur correspondant au nom {player_name} n'a été trouvé.")
            return None
    
        # Requête pour obtenir la heatmap du joueur
        heatmap_url = f"https://www.sofascore.com/api/v1/event/{match_id}/player/{player_id}/heatmap"
        try:
            response = requests.get(heatmap_url)
            if response.status_code == 200:
                heatmap_data = response.json().get("heatmap", [])
                event_id_counter = 1  # Compteur pour l'ID des événements fictifs
    
                # Création d'événements à partir de la heatmap (x, y)
                for point in heatmap_data:
                    event = {
                        "id": float(event_id_counter),  # ID fictif pour chaque événement
                        "minute": 0,  # Sans minute précise, tu peux adapter si tu as cette info
                        "second": 0,  # Sans seconde précise
                        "teamId": None,  # Pas d'info fournie, à adapter si nécessaire
                        "playerId": player_id,
                        "x": point.get('x', 0),  # Coordonnée X
                        "y": point.get('y', 0),  # Coordonnée Y
                        "period": {
                            "value": 2,  # Valeur fictive (2 pour la seconde période)
                            "displayName": "SecondHalf"  # Valeur par défaut
                        },
                        "type": {
                            "value": 61,  # Type pour "BallTouch"
                            "displayName": "BallTouch"
                        },
                        "outcomeType": {
                            "value": 1,  # 1 = Successful
                            "displayName": "Successful"
                        },
                        "isTouch": True
                    }
                    player_combined_data["events"].append(event)
                    event_id_counter += 1
    
            else:
                print(f"Erreur lors de la récupération de la heatmap, statut: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Erreur lors de l'appel API pour la heatmap: {str(e)}")
    
        # Requête pour obtenir les shots et goals du joueur via shotmap
        shotmap_url = f"https://www.sofascore.com/api/v1/event/{match_id}/shotmap/player/{player_id}"
        try:
            response = requests.get(shotmap_url)
            if response.status_code == 200:
                shotmap_data = response.json().get("shotmap", [])
                for shot in shotmap_data:
                    event = {
                        "id": float(shot['id']),  # Utilisation de l'ID du shotmap
                        "minute": shot.get("time", 0),  # Minute du tir
                        "second": 0,  # Pas de seconde précise dans la réponse
                        "teamId": None,  # Pas d'info fournie dans la réponse
                        "playerId": player_id,
                        "x": shot.get('playerCoordinates', {}).get('x', 0),  # Coordonnée X du tir
                        "y": shot.get('playerCoordinates', {}).get('y', 0),  # Coordonnée Y du tir
                        "endX": shot.get('draw', {}).get('end', {}).get('x', 0),  # Coordonnée endX
                        "endY": shot.get('draw', {}).get('end', {}).get('y', 0),  # Coordonnée endY
                        "period": {
                            "value": 2,  # Valeur fictive (à ajuster si tu as plus d'infos)
                            "displayName": "SecondHalf"  # Valeur par défaut
                        },
                        "type": {
                            "value": 62,  # Type fictif pour "Shot"
                            "displayName": "Shot" if shot.get("shotType") != "goal" else "Goal"
                        },
                        "outcomeType": {
                            "value": 1,  # 1 = Successful
                            "displayName": "Successful"
                        },
                        "isTouch": True
                    }
                    player_combined_data["events"].append(event)
    
            else:
                print(f"Erreur lors de la récupération des shots, statut: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"Erreur lors de l'appel API pour le shotmap: {str(e)}")
    
        # Génération du nom de fichier et sauvegarde des données
        match_name = os.path.basename(self.html_path).replace("data/", "").replace(".html", "")
        output_file = os.path.join(output_dir, f"{player_name.replace(' ', '_')}_{match_name}.json")
    
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(player_combined_data, f, ensure_ascii=False, indent=4)
    
        print(f"Les données combinées pour le joueur '{player_name}' ont été enregistrées dans {output_file}")
        return output_file