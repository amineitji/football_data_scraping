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
import math
from datetime import datetime
from collections import defaultdict, Counter
import statistics
from match_data_extractor import MatchDataExtractor

class WhoScoredDataExtractor(MatchDataExtractor):
    
    def __init__(self, html_path=None):
        # Compatibilité avec l'ancienne interface ET la nouvelle
        if html_path is None:
            # Mode nouveau : on initialise sans html_path pour l'instant
            self.html_path = None
            self.preprocessed_data = {}
        else:
            # Mode ancien : on passe html_path au parent
            super().__init__(html_path)
            self.preprocessed_data = {}
        
        # Mapping des types d'événements
        self.event_types = {
            1: "Pass", 2: "OffensiveAerialDuel", 3: "TakeOn", 4: "Foul", 5: "Outplay",
            6: "Challenge", 7: "Tackle", 8: "Interception", 9: "TurnOver", 10: "Save",
            11: "Claim", 12: "Clearance", 13: "MissedShots", 14: "BlockedShot", 15: "Goal",
            16: "Attempt", 17: "Corner", 18: "FreeKick", 19: "ThrowIn", 20: "GoalKick",
            21: "Substitution", 22: "Booking", 23: "SecondYellow", 24: "RedCard",
            25: "FormationChange", 26: "FormationSet", 27: "PlayerRetirement", 
            28: "TeamSet", 29: "Error", 30: "End", 31: "CancelledEnd", 32: "Start",
            41: "DefensiveAerialDuel", 42: "KeyPass", 43: "AttemptSaved", 44: "ShotOnPost",
            45: "KeeperPickup", 46: "CrossNotClaimed", 47: "Punch", 48: "KeeperSweeper",
            49: "BallRecovery", 50: "Dispossessed", 51: "Tackle", 52: "Formation",
            53: "Tracking", 54: "Blocked", 55: "GoodSkill", 56: "DefensiveError",
            57: "OffsideGiven", 58: "OffsideNotGiven", 59: "Foul", 60: "HandBall",
            61: "BallTouch", 62: "Dribble", 63: "Skill"
        }
        
        # Mapping des qualificateurs
        self.qualifiers_map = {
            1: "Longball", 2: "Cross", 3: "HeadPass", 4: "ThroughBall", 5: "FreeKickTaken",
            6: "CornerTaken", 7: "PlayerPosition", 15: "BlockedPass", 20: "BigChance",
            107: "ThrowIn", 140: "PassEndX", 141: "PassEndY", 155: "Chipped",
            178: "StandingSave", 212: "Length", 213: "Angle", 233: "OppositeRelatedEvent",
            285: "Defensive", 286: "Offensive"
        }
        
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
    
    def _extract_list_matchs_html(self):
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

        # Analyse du HTML avec BeautifulSoup
        print("Parsing HTML avec BeautifulSoup...")
        soup = BeautifulSoup(html, 'html.parser')

        print("Extraction des liens de matchs...")
        BASE_URL = 'https://fr.whoscored.com'
        links = soup.find_all('a', class_='stacked-match-link')
        match_urls = [BASE_URL + link['href'] for link in links if 'href' in link.attrs]

        all_data = []
        for match in match_urls:
            options = Options()
            options.headless = True
            options.add_argument(
                'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36')

            driver = webdriver.Chrome(options=options)

            # Désactiver la détection de Selenium par les sites
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            print(f"Chargement de la page WhoScored {match}...")
            driver.get(match)

            # Attente que la page se charge
            print("Attente que la page se charge complètement...")
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            # Récupération du contenu HTML après le chargement complet
            print("Récupération du contenu HTML...")
            html = driver.page_source

            print("Fermeture du navigateur Selenium...")
            driver.quit()

            print("Extraction des données avec le modèle regex pour WhoScored...")
            regex_pattern = r'(?<=require\.config\.params\["args"\].=.)[\s\S]*?;'

            try:
                data_txt = re.findall(regex_pattern, html)[0]
            except IndexError:
                print("Aucune correspondance trouvée, on passe à l'itération suivante.")
                pass  
            
            try:
                print("Nettoyage des données pour le format JSON...")
                data_txt = data_txt.replace('matchId', '"matchId"')
                data_txt = data_txt.replace('matchCentreData', '"matchCentreData"')
                data_txt = data_txt.replace('matchCentreEventTypeJson', '"matchCentreEventTypeJson"')
                data_txt = data_txt.replace('formationIdNameMappings', '"formationIdNameMappings"')
                data_txt = data_txt.replace('};', '}')

                print("Conversion des données extraites en JSON...")
                data_json = json.loads(data_txt)

                all_data.append(data_json)
            except json.JSONDecodeError as e:
                continue

        print("Fusion complète des données.")
        return all_data

    def extract_player_stats_and_events(self, player_name, output_dir="player_data"):
        """Extrait les stats et événements du joueur sur WhoScored."""
        print("Extraction des données pour le joueur - ", player_name)
        
        self.data = self._extract_data_html()
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
    
    def extract_player_aggregate_stats(self, player_name, output_dir="player_data"):
        """Extrait et agrège les stats et événements du joueur sur plusieurs matchs WhoScored."""
        print("Extraction des données agrégées pour le joueur -", player_name)

        self.data = self._extract_list_matchs_html()
        os.makedirs(output_dir, exist_ok=True)

        all_events = []
        positions_count = {}
        first_eleven_count = 0
        motm_count = 0
        aggregated_stats = {}
        player_id = None
        height = weight = age = None

        for match_data in self.data:
            match_centre = match_data["matchCentreData"]

            for pid, name in match_centre["playerIdNameDictionary"].items():
                if name.lower() == player_name.lower():
                    player_id = pid
                    break

            if not player_id:
                continue

            events = match_centre["events"]
            player_events = [event for event in events if event.get('playerId') == int(player_id)]
            all_events.extend(player_events)

            player_stats = None
            for team_type in ["home", "away"]:
                for player in match_centre[team_type]["players"]:
                    if player["playerId"] == int(player_id):
                        player_stats = player
                        break
                if player_stats:
                    break

            if not player_stats:
                continue

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

            for stat_key, stat_value in player_stats.get("stats", {}).items():
                if stat_key not in aggregated_stats:
                    aggregated_stats[stat_key] = stat_value
                else:
                    for sub_key, sub_val in stat_value.items():
                        if isinstance(sub_val, (int, float)):
                            aggregated_stats[stat_key][sub_key] = aggregated_stats[stat_key].get(sub_key, 0) + sub_val

        if not player_id:
            return f"Player '{player_name}' not found in any match."

        player_combined_data = {
            "player_name": player_name,
            "player_id": player_id,
            "position": positions_count,
            "height": height,
            "weight": weight,
            "age": age,
            "isFirstEleven": first_eleven_count,
            "isManOfTheMatch": motm_count,
            "stats": aggregated_stats,
            "events": all_events
        }

        output_file = os.path.join(output_dir, f"{player_name.replace(' ', '_')}_aggregated.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(player_combined_data, f, ensure_ascii=False, indent=4)

        print(f"Données agrégées pour le joueur '{player_name}' enregistrées dans {output_file}")
        return output_file

    # ===== NOUVELLES MÉTHODES D'ANALYSE COMPLÈTE =====

    def preprocess_match_data(self, html_path_or_data=None):
        """Charge et prétraite les données de match pour l'analyse complète"""
        if html_path_or_data:
            if isinstance(html_path_or_data, str):
                self.html_path = html_path_or_data
                self.data = self._extract_data_html()
            else:
                self.data = html_path_or_data
        elif not hasattr(self, 'data') or not self.data:
            self.data = self._extract_data_html()
            
        print("Début du préprocessing des données pour l'analyse complète...")
        self._preprocess_all_data()
        print("Préprocessing terminé.")
        
    def _preprocess_all_data(self):
        """Prétraite toutes les données pour l'analyse"""
        match_centre = self.data["matchCentreData"]
        
        # ===== EXTRACTION AMÉLIORÉE DE LA COMPÉTITION =====
        
        # Utiliser la méthode héritée de MatchDataExtractor
        competition_name = "Unknown"
        try:
            # Essayer d'abord la méthode de la classe parent
            competition_name = self.get_competition_from_filename()
            if not competition_name:
                # Si ça ne marche pas, essayer l'extraction depuis l'URL
                if hasattr(self, 'html_path') and self.html_path:
                    if "champions-league" in self.html_path.lower():
                        competition_name = "Champions League"
                    elif "premier-league" in self.html_path.lower():
                        competition_name = "Premier League"
                    elif "ligue-1" in self.html_path.lower():
                        competition_name = "Ligue 1"
                    elif "serie-a" in self.html_path.lower():
                        competition_name = "Serie A"
                    elif "laliga" in self.html_path.lower():
                        competition_name = "LaLiga"
                    elif "bundesliga" in self.html_path.lower():
                        competition_name = "Bundesliga"
                    elif "europa-league" in self.html_path.lower():
                        competition_name = "Europa League"
                    elif "conference-league" in self.html_path.lower():
                        competition_name = "Conference League"
                    elif "liga-portugal" in self.html_path.lower():
                        competition_name = "Liga Portugal"
                    else:
                        # Dernier recours : essayer d'extraire depuis les données JSON
                        competition_name = match_centre.get("competition", {}).get("name", "Unknown")
        except Exception as e:
            print(f"⚠️ Erreur extraction compétition: {e}")
            competition_name = match_centre.get("competition", {}).get("name", "Unknown")
        
        # Informations générales du match - EXTRACTION CORRECTE
        home_team_name = match_centre["home"]["name"]
        away_team_name = match_centre["away"]["name"]
        home_score = match_centre["home"]["scores"]["fulltime"]
        away_score = match_centre["away"]["scores"]["fulltime"]
        
        # Garder les noms d'équipes complets
        self.preprocessed_data["match_info"] = {
            "home_team": home_team_name,
            "away_team": away_team_name,
            "score": f"{home_score}-{away_score}",
            "competition": competition_name,
            "venue": match_centre.get("venue", "Unknown"),
            "referee": match_centre.get("referee", "Unknown"),
            "home_score": home_score,
            "away_score": away_score
        }
        
        print(f"📊 Match info extraites: {competition_name} - {home_team_name} vs {away_team_name} ({home_score}-{away_score})")
        
        # Préprocessing des événements
        self._preprocess_events(match_centre["events"])
        
        # Préprocessing des joueurs
        self._preprocess_players(match_centre)
        
        # Calculs de métriques avancées
        self._calculate_advanced_metrics()

    def _preprocess_events(self, events):
        """Prétraite tous les événements du match"""
        self.preprocessed_data["events"] = {
            "all_events": events,
            "by_player": defaultdict(list),
            "by_team": defaultdict(list),
            "by_type": defaultdict(list),
            "by_period": defaultdict(list),
            "by_minute": defaultdict(list)
        }
        
        for event in events:
            # Par joueur
            if "playerId" in event:
                self.preprocessed_data["events"]["by_player"][event["playerId"]].append(event)
            
            # Par équipe
            self.preprocessed_data["events"]["by_team"][event["teamId"]].append(event)
            
            # Par type
            event_type = event["type"]["value"]
            self.preprocessed_data["events"]["by_type"][event_type].append(event)
            
            # Par période
            period = event["period"]["value"]
            self.preprocessed_data["events"]["by_period"][period].append(event)
            
            # Par minute
            minute = event["minute"]
            self.preprocessed_data["events"]["by_minute"][minute].append(event)

    def _preprocess_players(self, match_centre):
        """Prétraite les informations des joueurs"""
        self.preprocessed_data["players"] = {}
        
        # Dictionnaire nom-ID
        name_dict = match_centre["playerIdNameDictionary"]
        
        for team_type in ["home", "away"]:
            team_players = match_centre[team_type]["players"]
            team_id = match_centre[team_type]["teamId"]
            
            for player in team_players:
                player_id = player["playerId"]
                player_name = name_dict.get(str(player_id), "Unknown")
                
                self.preprocessed_data["players"][player_id] = {
                    "name": player_name,
                    "team": team_type,
                    "team_id": team_id,
                    "position": player.get("position", "Unknown"),
                    "shirt_number": player.get("shirtNo", 0),
                    "is_starter": player.get("isFirstEleven", False),
                    "is_motm": player.get("isManOfTheMatch", False),
                    "age": player.get("age", 0),
                    "height": player.get("height", 0),
                    "weight": player.get("weight", 0),
                    "stats": player.get("stats", {}),
                    "events": self.preprocessed_data["events"]["by_player"][player_id]
                }

    def _calculate_advanced_metrics(self):
        """Calcule des métriques avancées pour tous les joueurs"""
        self.preprocessed_data["advanced_metrics"] = {}
        
        for player_id, player_data in self.preprocessed_data["players"].items():
            if not player_data["events"]:
                continue
                
            metrics = self._calculate_player_advanced_metrics(player_id, player_data)
            self.preprocessed_data["advanced_metrics"][player_id] = metrics

    def _calculate_player_advanced_metrics(self, player_id, player_data):
        """Calcule les métriques avancées pour un joueur"""
        events = player_data["events"]
        
        # Métriques de base
        total_actions = len(events)
        successful_actions = len([e for e in events if e["outcomeType"]["value"] == 1])
        success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0
        
        # Analyses spécialisées
        passes_metrics = self._analyze_passing(events)
        defensive_metrics = self._analyze_defensive_actions(events)
        offensive_metrics = self._analyze_offensive_actions(events)
        spatial_metrics = self._analyze_spatial_distribution(events)
        temporal_metrics = self._analyze_temporal_distribution(events)
        pressure_metrics = self._analyze_pressure_situations(events)
        
        # MODIFIÉ - Calcul d'influence avec détails
        influence_data = self._calculate_influence_score_detailed(events, player_data)
        influence_score = influence_data["score"]
        
        return {
            "basic": {
                "total_actions": total_actions,
                "successful_actions": successful_actions,
                "success_rate": success_rate
            },
            "passing": passes_metrics,
            "defensive": defensive_metrics,
            "offensive": offensive_metrics,
            "spatial": spatial_metrics,
            "temporal": temporal_metrics,
            "pressure": pressure_metrics,
            "influence_score": influence_score,
            "influence_details": influence_data  # NOUVEAU - Ajouter les détails d'influence
        }

    def _analyze_passing(self, events):
        """Analyse détaillée des passes"""
        passes = [e for e in events if e["type"]["value"] == 1]
        if not passes:
            return {}
            
        successful_passes = [p for p in passes if p["outcomeType"]["value"] == 1]
        
        # Analyse par zone et types
        zones = {"Back": 0, "Center": 0, "Left": 0, "Right": 0, "Forward": 0}
        pass_lengths = []
        pass_angles = []
        
        # Types de passes spéciaux
        long_balls = through_balls = crosses = head_passes = chipped_passes = 0
        
        for pass_event in passes:
            for qualifier in pass_event.get("qualifiers", []):
                qualifier_type = qualifier["type"]["value"]
                
                if qualifier_type == 212:  # Length
                    pass_lengths.append(float(qualifier["value"]))
                elif qualifier_type == 213:  # Angle
                    pass_angles.append(float(qualifier["value"]))
                elif qualifier_type == 56:  # Zone
                    zone = qualifier["value"]
                    if zone in zones:
                        zones[zone] += 1
                elif qualifier_type == 1:  # Longball
                    long_balls += 1
                elif qualifier_type == 4:  # ThroughBall
                    through_balls += 1
                elif qualifier_type == 2:  # Cross
                    crosses += 1
                elif qualifier_type == 3:  # HeadPass
                    head_passes += 1
                elif qualifier_type == 155:  # Chipped
                    chipped_passes += 1
        
        avg_pass_length = statistics.mean(pass_lengths) if pass_lengths else 0
        pass_length_variation = statistics.stdev(pass_lengths) if len(pass_lengths) > 1 else 0
        
        risk_analysis = self._analyze_pass_risk(passes, successful_passes)
        
        return {
            "total_passes": len(passes),
            "successful_passes": len(successful_passes),
            "pass_accuracy": (len(successful_passes) / len(passes) * 100) if passes else 0,
            "avg_pass_length": avg_pass_length,
            "pass_length_variation": pass_length_variation,
            "zones_distribution": zones,
            "long_balls": long_balls,
            "through_balls": through_balls,
            "crosses": crosses,
            "head_passes": head_passes,
            "chipped_passes": chipped_passes,
            "risk_analysis": risk_analysis
        }

    def _assess_passing_risk_level(self, lateral, forward, backward):
        """Évalue le niveau de prise de risque basé sur les directions de passe"""
        total = lateral + forward + backward
        if total == 0:
            return "Insufficient data"
            
        forward_pct = forward / total * 100
        lateral_pct = lateral / total * 100
        backward_pct = backward / total * 100
        
        if forward_pct > 40:
            return "High risk-taker - Frequent forward passes"
        elif lateral_pct > 60:
            return "Conservative - Prefers lateral circulation"
        elif backward_pct > 30:
            return "Very conservative - Often plays backwards"
        else:
            return "Balanced approach"

    def _analyze_defensive_zones(self, defensive_events):
        """Analyse la répartition spatiale des actions défensives"""
        zones = {"own_box": 0, "own_third": 0, "middle_third": 0, "attacking_third": 0}
        
        for event in defensive_events:
            y_pos = event["y"]
            if y_pos < 16.5:
                zones["own_box"] += 1
            elif y_pos < 33:
                zones["own_third"] += 1
            elif y_pos < 66:
                zones["middle_third"] += 1
            else:
                zones["attacking_third"] += 1
                
        return zones

    def _calculate_defensive_intensity(self, tackles, interceptions, ball_recoveries):
        """Calcule l'intensité défensive"""
        total_actions = len(tackles + interceptions + ball_recoveries)
        
        if total_actions == 0:
            return "No defensive activity"
        elif total_actions < 3:
            return "Low defensive involvement"
        elif total_actions < 6:
            return "Moderate defensive activity"
        elif total_actions < 10:
            return "High defensive involvement"
        else:
            return "Very high defensive intensity"

    def _analyze_offensive_actions(self, events):
        """Analyse les actions offensives"""
        shots = [e for e in events if e["type"]["value"] in [13, 15, 16]]
        key_passes = [e for e in events if e["type"]["value"] == 42]
        dribbles = [e for e in events if e["type"]["value"] == 3]
        
        goals = [s for s in shots if s["type"]["value"] == 15]
        shots_on_target = [s for s in shots if s["type"]["value"] in [15, 43]]
        
        return {
            "shots_total": len(shots),
            "goals": len(goals),
            "shots_on_target": len(shots_on_target),
            "shooting_accuracy": (len(shots_on_target) / len(shots) * 100) if shots else 0,
            "key_passes": len(key_passes),
            "dribbles_attempted": len(dribbles),
            "dribbles_successful": len([d for d in dribbles if d["outcomeType"]["value"] == 1]),
            "dribble_success_rate": (len([d for d in dribbles if d["outcomeType"]["value"] == 1]) / len(dribbles) * 100) if dribbles else 0
        }

    def _analyze_spatial_distribution(self, events):
        """Analyse la distribution spatiale du joueur"""
        positions = [(e["x"], e["y"]) for e in events if "x" in e and "y" in e]
        
        if not positions:
            return {}
            
        # Centre de gravité
        avg_x = statistics.mean([pos[0] for pos in positions])
        avg_y = statistics.mean([pos[1] for pos in positions])
        
        # Dispersion
        x_variance = statistics.variance([pos[0] for pos in positions]) if len(positions) > 1 else 0
        y_variance = statistics.variance([pos[1] for pos in positions]) if len(positions) > 1 else 0
        
        # Zones de couverture
        zones_coverage = self._calculate_zones_coverage(positions)
        
        return {
            "center_of_gravity": {"x": avg_x, "y": avg_y},
            "x_variance": x_variance,
            "y_variance": y_variance,
            "mobility_score": math.sqrt(x_variance + y_variance),
            "zones_coverage": zones_coverage,
            "field_coverage_percentage": self._calculate_field_coverage(positions)
        }

    def _calculate_zones_coverage(self, positions):
        """Calcule la couverture par zones du terrain"""
        zones = {
            "left_wing": 0, "left_half": 0, "center": 0, "right_half": 0, "right_wing": 0,
            "own_third": 0, "middle_third": 0, "attacking_third": 0
        }
        
        for x, y in positions:
            # Zones horizontales
            if x < 20:
                zones["left_wing"] += 1
            elif x < 40:
                zones["left_half"] += 1
            elif x < 60:
                zones["center"] += 1
            elif x < 80:
                zones["right_half"] += 1
            else:
                zones["right_wing"] += 1
                
            # Zones verticales
            if y < 33:
                zones["own_third"] += 1
            elif y < 66:
                zones["middle_third"] += 1
            else:
                zones["attacking_third"] += 1
                
        return zones

    def _calculate_field_coverage(self, positions):
        """Calcule le pourcentage de terrain couvert"""
        if not positions:
            return 0
            
        # Divise le terrain en grille 10x10
        grid = set()
        for x, y in positions:
            grid_x = int(x // 10)
            grid_y = int(y // 10)
            grid.add((grid_x, grid_y))
            
        return len(grid) / 100 * 100

    def _assess_temporal_consistency(self, time_blocks):
        """Évalue la régularité de l'activité dans le temps"""
        values = list(time_blocks.values())
        if not values or all(v == 0 for v in values):
            return "No activity"
            
        avg = statistics.mean(values)
        variance = statistics.variance(values) if len(values) > 1 else 0
        
        consistency_score = 1 - (variance / (avg ** 2)) if avg > 0 else 0
        
        if consistency_score > 0.8:
            return "Very consistent throughout the match"
        elif consistency_score > 0.6:
            return "Generally consistent with some variations"
        elif consistency_score > 0.4:
            return "Moderate consistency with noticeable fluctuations"
        else:
            return "Inconsistent activity levels"








































































    def _assess_pressure_handling(self, total_pressure, successful_pressure):
        """Évalue la capacité à gérer la pression avec justifications statistiques"""
        if total_pressure == 0:
            return {
                "assessment": "No pressure situations identified",
                "justification": "Aucune action identifiée sous pression (< 3 secondes entre actions)",
                "context": "Le joueur n'a pas été mis sous pression temporelle significative",
                "statistical_evidence": f"0 action sous pression sur l'ensemble du match"
            }

        success_rate = successful_pressure / total_pressure * 100

        if success_rate > 80:
            return {
                "assessment": "Excellent under pressure - Rarely loses composure",
                "justification": f"Taux de réussite sous pression de {success_rate:.1f}% ({successful_pressure}/{total_pressure})",
                "context": "Performance technique maintenue même dans l'urgence temporelle",
                "statistical_evidence": f"{successful_pressure} actions réussies sur {total_pressure} tentatives sous pression",
                "benchmark_comparison": "Supérieur à la moyenne professionnelle (65-75%)"
            }
        elif success_rate > 65:
            return {
                "assessment": "Good under pressure - Generally maintains quality",
                "justification": f"Taux de réussite sous pression de {success_rate:.1f}% ({successful_pressure}/{total_pressure})",
                "context": "Léger déclin technique sous contrainte temporelle mais reste efficace",
                "statistical_evidence": f"{successful_pressure} actions réussies sur {total_pressure} tentatives sous pression",
                "benchmark_comparison": "Dans la moyenne professionnelle (65-75%)"
            }
        elif success_rate > 50:
            return {
                "assessment": "Average under pressure - Some quality loss",
                "justification": f"Taux de réussite sous pression de {success_rate:.1f}% ({successful_pressure}/{total_pressure})",
                "context": "Déclin technique notable sous contrainte temporelle",
                "statistical_evidence": f"{successful_pressure} actions réussies sur {total_pressure} tentatives sous pression",
                "benchmark_comparison": "En dessous de la moyenne professionnelle (65-75%)"
            }
        else:
            return {
                "assessment": "Struggles under pressure - Significant quality drop",
                "justification": f"Taux de réussite sous pression de {success_rate:.1f}% ({successful_pressure}/{total_pressure})",
                "context": "Forte dégradation technique sous contrainte temporelle",
                "statistical_evidence": f"{successful_pressure} actions réussies sur {total_pressure} tentatives sous pression",
                "benchmark_comparison": "Bien en dessous de la moyenne professionnelle (65-75%)"
            }

    def _assess_passing_risk_level_detailed(self, lateral, forward, backward, pass_accuracy):
        """Évalue le niveau de prise de risque avec justifications détaillées"""
        total = lateral + forward + backward
        if total == 0:
            return {
                "assessment": "Insufficient data",
                "justification": "Données de direction insuffisantes pour l'analyse",
                "statistical_evidence": "0 passe analysée pour la direction"
            }

        forward_pct = forward / total * 100
        lateral_pct = lateral / total * 100
        backward_pct = backward / total * 100

        if forward_pct > 40:
            return {
                "assessment": "High risk-taker - Frequent forward passes",
                "justification": f"{forward_pct:.1f}% de passes vers l'avant avec {pass_accuracy:.1f}% de précision",
                "context": "Privilégie la progression offensive malgré les risques",
                "statistical_evidence": f"{forward} passes vers l'avant sur {total} passes analysées",
                "risk_profile": "Offensif - Cherche constamment à faire progresser l'équipe",
                "precision_under_risk": f"Maintient {pass_accuracy:.1f}% de précision malgré la prise de risque"
            }
        elif lateral_pct > 60:
            return {
                "assessment": "Conservative - Prefers lateral circulation",
                "justification": f"{lateral_pct:.1f}% de passes latérales, privilégie la sécurité",
                "context": "Approche sécuritaire favorisant la possession",
                "statistical_evidence": f"{lateral} passes latérales sur {total} passes analysées",
                "risk_profile": "Conservateur - Maintient la possession avant tout",
                "efficiency_trade_off": f"Précision élevée ({pass_accuracy:.1f}%) au détriment de la progression"
            }
        elif backward_pct > 30:
            return {
                "assessment": "Very conservative - Often plays backwards",
                "justification": f"{backward_pct:.1f}% de passes arrière, approche très prudente",
                "context": "Privilégie la sécurité absolue et la relance depuis l'arrière",
                "statistical_evidence": f"{backward} passes arrière sur {total} passes analysées",
                "risk_profile": "Très conservateur - Évite tout risque de perte de balle",
                "tactical_role": "Rôle de consolidation et de sécurisation du jeu"
            }
        else:
            return {
                "assessment": "Balanced approach",
                "justification": f"Répartition équilibrée: {forward_pct:.1f}% avant, {lateral_pct:.1f}% latéral, {backward_pct:.1f}% arrière",
                "context": "Adaptation tactique selon les phases de jeu",
                "statistical_evidence": f"Distribution variée sur {total} passes analysées",
                "risk_profile": "Équilibré - S'adapte aux besoins de l'équipe",
                "tactical_intelligence": "Prise de décision contextuelle selon les situations"
            }

    def _assess_endurance_detailed(self, fatigue_indicator, temporal_metrics, total_actions):
        """Évalue l'endurance avec justifications statistiques détaillées"""
        first_half = temporal_metrics.get('first_half_intensity', 0)
        second_half = temporal_metrics.get('second_half_intensity', 0)

        if fatigue_indicator < 10:
            return {
                "assessment": "Excellente endurance, maintient l'intensité",
                "justification": f"Baisse d'activité de seulement {fatigue_indicator:.1f}% entre les mi-temps",
                "statistical_evidence": f"1ère mi-temps: {first_half} actions, 2ème mi-temps: {second_half} actions",
                "context": "Capacité exceptionnelle à maintenir le niveau sur 90 minutes",
                "benchmark_comparison": "Performance d'endurance de niveau élite (< 10% de baisse)",
                "physical_implication": "Condition physique optimale pour les exigences du football moderne"
            }
        elif fatigue_indicator < 25:
            return {
                "assessment": "Bonne endurance avec légère baisse",
                "justification": f"Baisse d'activité de {fatigue_indicator:.1f}% en seconde période",
                "statistical_evidence": f"1ère mi-temps: {first_half} actions, 2ème mi-temps: {second_half} actions",
                "context": "Déclin naturel d'intensité mais reste dans les standards professionnels",
                "benchmark_comparison": "Performance d'endurance correcte (10-25% de baisse acceptable)",
                "physical_implication": "Endurance suffisante pour la plupart des contextes de match"
            }
        elif fatigue_indicator < 40:
            return {
                "assessment": "Endurance correcte mais baisse notable",
                "justification": f"Baisse d'activité significative de {fatigue_indicator:.1f}% en seconde période",
                "statistical_evidence": f"1ère mi-temps: {first_half} actions, 2ème mi-temps: {second_half} actions",
                "context": "Déclin d'intensité préoccupant qui peut affecter l'efficacité globale",
                "benchmark_comparison": "Performance d'endurance en dessous des standards (25-40% de baisse)",
                "physical_implication": "Nécessité d'améliorer la condition physique aérobie"
            }
        else:
            return {
                "assessment": "Baisse d'intensité significative en seconde période",
                "justification": f"Chute drastique d'activité de {fatigue_indicator:.1f}% en seconde période",
                "statistical_evidence": f"1ère mi-temps: {first_half} actions, 2ème mi-temps: {second_half} actions",
                "context": "Endurance insuffisante pour maintenir l'efficacité sur la durée",
                "benchmark_comparison": "Performance d'endurance préoccupante (> 40% de baisse)",
                "physical_implication": "Condition physique à travailler en priorité"
            }

    def _assess_defensive_intensity_detailed(self, tackles, interceptions, ball_recoveries, total_actions):
        """Évalue l'intensité défensive avec justifications détaillées"""
        total_def_actions = len(tackles + interceptions + ball_recoveries)
        successful_tackles = len([t for t in tackles if t.get("outcomeType", {}).get("value") == 1])
        tackle_success_rate = (successful_tackles / len(tackles) * 100) if tackles else 0

        defensive_ratio = (total_def_actions / total_actions * 100) if total_actions > 0 else 0

        if total_def_actions == 0:
            return {
                "assessment": "No defensive activity",
                "justification": "Aucune action défensive identifiée durant le match",
                "statistical_evidence": "0 tacle, 0 interception, 0 récupération",
                "context": "Rôle exclusivement offensif ou très défensif (gardien)",
                "tactical_implication": "Positionnement ne nécessitant pas d'interventions défensives"
            }
        elif total_def_actions < 3:
            return {
                "assessment": "Low defensive involvement",
                "justification": f"Seulement {total_def_actions} action(s) défensive(s) sur {total_actions} actions totales",
                "statistical_evidence": f"{len(tackles)} tacle(s), {len(interceptions)} interception(s), {len(ball_recoveries)} récupération(s)",
                "context": f"Implication défensive limitée ({defensive_ratio:.1f}% des actions)",
                "tactical_role": "Rôle principalement offensif avec peu de responsabilités défensives",
                "benchmark_comparison": "En dessous de la moyenne pour un joueur de champ (5-8 actions/match)"
            }
        elif total_def_actions < 6:
            return {
                "assessment": "Moderate defensive activity",
                "justification": f"{total_def_actions} actions défensives avec {tackle_success_rate:.1f}% d'efficacité aux tacles",
                "statistical_evidence": f"{len(tackles)} tacle(s) [{successful_tackles} réussi(s)], {len(interceptions)} interception(s), {len(ball_recoveries)} récupération(s)",
                "context": f"Équilibre entre rôles offensif et défensif ({defensive_ratio:.1f}% des actions)",
                "tactical_role": "Joueur polyvalent contribuant aux deux phases de jeu",
                "benchmark_comparison": "Dans la moyenne pour un milieu de terrain (5-8 actions/match)"
            }
        elif total_def_actions < 10:
            return {
                "assessment": "High defensive involvement",
                "justification": f"{total_def_actions} actions défensives témoignant d'un engagement important",
                "statistical_evidence": f"{len(tackles)} tacle(s) [{successful_tackles} réussi(s)], {len(interceptions)} interception(s), {len(ball_recoveries)} récupération(s)",
                "context": f"Forte implication défensive ({defensive_ratio:.1f}% des actions)",
                "tactical_role": "Joueur à vocation défensive ou dans un système très défensif",
                "benchmark_comparison": "Au-dessus de la moyenne professionnelle (8-12 actions/match)"
            }
        else:
            return {
                "assessment": "Very high defensive intensity",
                "justification": f"{total_def_actions} actions défensives démontrant un rôle défensif prépondérant",
                "statistical_evidence": f"{len(tackles)} tacle(s) [{successful_tackles} réussi(s)], {len(interceptions)} interception(s), {len(ball_recoveries)} récupération(s)",
                "context": f"Implication défensive majeure ({defensive_ratio:.1f}% des actions)",
                "tactical_role": "Joueur clé dans la récupération et l'organisation défensive",
                "benchmark_comparison": "Performance défensive d'élite (> 12 actions/match)"
            }

    def _calculate_influence_score_detailed(self, events, player_data):
        """Calcule un score d'influence avec justifications détaillées"""
        if not events:
            return {
                "score": 0,
                "breakdown": {},
                "justification": "Aucun événement enregistré"
            }

        # Facteurs d'influence détaillés
        total_actions = len(events)
        successful_actions = len([e for e in events if e.get("outcomeType", {}).get("value") == 1])
        success_rate = successful_actions / total_actions if total_actions > 0 else 0

        key_actions = len([e for e in events if e.get("type", {}).get("value") in [15, 42, 4, 8]])

        factors = {
            "volume_actions": total_actions * 0.1,
            "efficiency": success_rate * 20,
            "key_moments": key_actions * 2,
            "starter_bonus": 5 if player_data.get("is_starter", False) else 0,
            "motm_bonus": 10 if player_data.get("is_motm", False) else 0
        }

        total_score = sum(factors.values())

        return {
            "score": total_score,
            "breakdown": factors,
            "justification": f"Score basé sur {total_actions} actions ({success_rate*100:.1f}% réussite), {key_actions} actions clés",
            "statistical_evidence": f"Volume: {factors['volume_actions']:.1f}pts | Efficacité: {factors['efficiency']:.1f}pts | Moments clés: {factors['key_moments']:.1f}pts",
            "context": "Score d'influence sur 50 points maximum",
            "performance_level": self._categorize_influence_score(total_score)
        }

    def _categorize_influence_score(self, score):
        """Catégorise le score d'influence"""
        if score > 35:
            return "Performance exceptionnelle - Impact majeur sur le match"
        elif score > 25:
            return "Très bonne performance - Contribution significative"
        elif score > 15:
            return "Performance correcte - Impact modéré"
        elif score > 8:
            return "Performance moyenne - Impact limité"
        else:
            return "Performance faible - Impact minimal"

    def _analyze_pressure_situations(self, events):
        """MODIFIÉE - Analyse les situations sous pression avec justifications détaillées"""
        pressure_events = []

        for i in range(1, len(events)):
            try:
                current_time = (events[i]["minute"] * 60 + events[i].get("second", 0))
                previous_time = (events[i-1]["minute"] * 60 + events[i-1].get("second", 0))
                time_diff = current_time - previous_time

                if time_diff < 3:
                    pressure_events.append(events[i])
            except (KeyError, TypeError):
                continue
            
        successful_under_pressure = len([e for e in pressure_events if e.get("outcomeType", {}).get("value") == 1])

        pressure_handling = self._assess_pressure_handling(len(pressure_events), successful_under_pressure)

        return {
            "actions_under_pressure": len(pressure_events),
            "successful_under_pressure": successful_under_pressure,
            "pressure_success_rate": (successful_under_pressure / len(pressure_events) * 100) if pressure_events else 0,
            "pressure_handling": pressure_handling["assessment"],
            "pressure_analysis": pressure_handling  # NOUVEAU - Analyse complète avec justifications
        }

    def _analyze_pass_risk(self, passes, successful_passes):
        """MODIFIÉE - Analyse le niveau de prise de risque avec justifications détaillées"""
        if not passes:
            return {}

        lateral_passes = forward_passes = backward_passes = 0

        for pass_event in passes:
            start_x, start_y = pass_event["x"], pass_event["y"]
            end_x = end_y = None

            for qualifier in pass_event.get("qualifiers", []):
                if qualifier["type"]["value"] == 140:
                    end_x = float(qualifier["value"])
                elif qualifier["type"]["value"] == 141:
                    end_y = float(qualifier["value"])

            if end_x is not None and end_y is not None:
                y_diff = end_y - start_y
                x_diff = abs(end_x - start_x)

                if abs(y_diff) > x_diff:
                    if y_diff > 0:
                        forward_passes += 1
                    else:
                        backward_passes += 1
                else:
                    lateral_passes += 1

        total_analyzed = lateral_passes + forward_passes + backward_passes
        pass_accuracy = (len(successful_passes) / len(passes) * 100) if passes else 0

        risk_analysis = self._assess_passing_risk_level_detailed(lateral_passes, forward_passes, backward_passes, pass_accuracy)

        return {
            "lateral_passes": lateral_passes,
            "forward_passes": forward_passes,
            "backward_passes": backward_passes,
            "lateral_percentage": (lateral_passes / total_analyzed * 100) if total_analyzed > 0 else 0,
            "forward_percentage": (forward_passes / total_analyzed * 100) if total_analyzed > 0 else 0,
            "backward_percentage": (backward_passes / total_analyzed * 100) if total_analyzed > 0 else 0,
            "risk_assessment": risk_analysis["assessment"],
            "risk_analysis": risk_analysis  # NOUVEAU - Analyse complète avec justifications
        }

    def _analyze_defensive_actions(self, events):
        """MODIFIÉE - Analyse les actions défensives avec justifications détaillées"""
        tackles = [e for e in events if e["type"]["value"] == 7]
        interceptions = [e for e in events if e["type"]["value"] == 8]
        ball_recoveries = [e for e in events if e["type"]["value"] == 49]
        clearances = [e for e in events if e["type"]["value"] == 12]

        successful_tackles = [t for t in tackles if t["outcomeType"]["value"] == 1]
        tackle_success_rate = (len(successful_tackles) / len(tackles) * 100) if tackles else 0

        defensive_zones = self._analyze_defensive_zones(tackles + interceptions + ball_recoveries)
        total_actions = len([e for e in events])

        intensity_analysis = self._assess_defensive_intensity_detailed(tackles, interceptions, ball_recoveries, total_actions)

        return {
            "tackles_attempted": len(tackles),
            "tackles_won": len(successful_tackles),
            "tackle_success_rate": tackle_success_rate,
            "interceptions": len(interceptions),
            "ball_recoveries": len(ball_recoveries),
            "clearances": len(clearances),
            "total_defensive_actions": len(tackles + interceptions + ball_recoveries + clearances),
            "defensive_zones": defensive_zones,
            "defensive_intensity": intensity_analysis["assessment"],
            "defensive_analysis": intensity_analysis  # NOUVEAU - Analyse complète avec justifications
        }

    def _analyze_temporal_distribution(self, events):
        """MODIFIÉE - Analyse la distribution temporelle avec justifications détaillées"""
        if not events:
            return {}

        time_blocks = {
            "0-15": 0, "16-30": 0, "31-45": 0, "46-60": 0, 
            "61-75": 0, "76-90": 0, "90+": 0
        }

        for event in events:
            minute = event["minute"]
            if minute <= 15:
                time_blocks["0-15"] += 1
            elif minute <= 30:
                time_blocks["16-30"] += 1
            elif minute <= 45:
                time_blocks["31-45"] += 1
            elif minute <= 60:
                time_blocks["46-60"] += 1
            elif minute <= 75:
                time_blocks["61-75"] += 1
            elif minute <= 90:
                time_blocks["76-90"] += 1
            else:
                time_blocks["90+"] += 1

        first_half_actions = time_blocks["0-15"] + time_blocks["16-30"] + time_blocks["31-45"]
        second_half_actions = time_blocks["46-60"] + time_blocks["61-75"] + time_blocks["76-90"]

        fatigue_indicator = (first_half_actions - second_half_actions) / first_half_actions * 100 if first_half_actions > 0 else 0
        consistency = self._assess_temporal_consistency(time_blocks)

        endurance_analysis = self._assess_endurance_detailed(fatigue_indicator, {
            'first_half_intensity': first_half_actions,
            'second_half_intensity': second_half_actions
        }, len(events))

        return {
            "time_distribution": time_blocks,
            "first_half_intensity": first_half_actions,
            "second_half_intensity": second_half_actions,
            "fatigue_indicator": fatigue_indicator,
            "consistency": consistency,
            "endurance_assessment": endurance_analysis["assessment"],
            "endurance_analysis": endurance_analysis  # NOUVEAU - Analyse complète avec justifications
        }














































    def _calculate_influence_score(self, events, player_data):
        """Calcule un score d'influence - Point d'entrée principal"""
        influence_data = self._calculate_influence_score_detailed(events, player_data)
        return influence_data["score"]

    def generate_complete_player_analysis(self, player_name, output_dir="player_data"):
        """Génère l'analyse complète d'un joueur (JSON + MD)"""
        if not hasattr(self, 'preprocessed_data') or not self.preprocessed_data:
            self.preprocess_match_data()
            
        os.makedirs(output_dir, exist_ok=True)
        
        # Trouver le joueur
        player_id = None
        for pid, pdata in self.preprocessed_data["players"].items():
            if pdata["name"].lower() == player_name.lower():
                player_id = pid
                break
                
        if not player_id:
            return f"Joueur '{player_name}' non trouvé"
            
        player_data = self.preprocessed_data["players"][player_id]
        advanced_metrics = self.preprocessed_data["advanced_metrics"].get(player_id, {})
        
        # Génération JSON
        json_analysis = {
            "match_info": self.preprocessed_data["match_info"],
            "player_info": player_data,
            "advanced_metrics": advanced_metrics,
            "detailed_analysis": self._generate_detailed_analysis(player_data, advanced_metrics),
            "timestamp": datetime.now().isoformat()
        }
        
        json_filename = f"{player_name.replace(' ', '_')}_complete_analysis.json"
        json_filepath = os.path.join(output_dir, json_filename)
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(json_analysis, f, ensure_ascii=False, indent=2)
        
        # Génération rapport MD
        md_report = self._generate_markdown_report(player_data, advanced_metrics, json_analysis["detailed_analysis"])
        md_filename = f"{player_name.replace(' ', '_')}_match_report.md"
        md_filepath = os.path.join(output_dir, md_filename)
        
        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(md_report)
            
        print(f"Analyse complète générée pour {player_name}:")
        print(f"- JSON: {json_filepath}")
        print(f"- Rapport: {md_filepath}")
        
        return {"json": json_filepath, "markdown": md_filepath}

    def _generate_detailed_analysis(self, player_data, metrics):
        """Génère une analyse détaillée avec interprétations"""
        analysis = {
            "performance_summary": self._generate_performance_summary(player_data, metrics),
            "tactical_analysis": self._generate_tactical_analysis(player_data, metrics),
            "technical_assessment": self._generate_technical_assessment(metrics),
            "physical_assessment": self._generate_physical_assessment(metrics),
            "mental_assessment": self._generate_mental_assessment(metrics),
            "areas_of_excellence": self._identify_strengths(metrics),
            "improvement_areas": self._identify_weaknesses(metrics),
            "contextual_factors": self._analyze_contextual_factors(player_data)
        }
        
        return analysis

    def _generate_performance_summary(self, player_data, metrics):
        """Génère un résumé de performance"""
        if not metrics:
            return "Données insuffisantes pour l'analyse"
            
        basic = metrics.get("basic", {})
        passing = metrics.get("passing", {})
        
        summary = f"Performance globale avec {basic.get('total_actions', 0)} actions et "
        summary += f"{basic.get('success_rate', 0):.1f}% de réussite. "
        
        if passing.get("total_passes", 0) > 0:
            summary += f"Précision des passes: {passing.get('pass_accuracy', 0):.1f}% "
            summary += f"({passing.get('successful_passes', 0)}/{passing.get('total_passes', 0)}). "
            
        summary += f"Score d'influence: {metrics.get('influence_score', 0):.1f}"
        
        return summary

    def _generate_tactical_analysis(self, player_data, metrics):
        """Analyse tactique du joueur"""
        spatial = metrics.get("spatial", {})
        passing = metrics.get("passing", {})
        defensive = metrics.get("defensive", {})
        
        center_gravity = spatial.get("center_of_gravity", {})
        zones_coverage = spatial.get("zones_coverage", {})
        
        analysis = {
            "positioning": f"Centre de gravité en ({center_gravity.get('x', 0):.1f}, {center_gravity.get('y', 0):.1f}). "
                         f"Mobilité: {spatial.get('mobility_score', 0):.1f}",
            "field_coverage": f"Couverture terrain: {spatial.get('field_coverage_percentage', 0):.1f}%. "
                            f"Zones privilégiées: {self._identify_preferred_zones(zones_coverage)}",
            "passing_style": self._analyze_passing_style(passing),
            "defensive_positioning": self._analyze_defensive_positioning(defensive, spatial),
            "tactical_discipline": self._assess_tactical_discipline(player_data, metrics)
        }
        
        return analysis

    def _identify_preferred_zones(self, zones_coverage):
        """Identifie les zones préférées du joueur"""
        if not zones_coverage:
            return "Données insuffisantes"
            
        max_zone = max(zones_coverage.items(), key=lambda x: x[1])
        return f"{max_zone[0]} ({max_zone[1]} actions)"

    def _analyze_passing_style(self, passing_metrics):
        """Analyse le style de passe du joueur"""
        if not passing_metrics:
            return "Pas de données de passes"
            
        risk_analysis = passing_metrics.get("risk_analysis", {})
        lateral_pct = risk_analysis.get("lateral_percentage", 0)
        forward_pct = risk_analysis.get("forward_percentage", 0)
        
        style = f"Style: {risk_analysis.get('risk_assessment', 'Indéterminé')}. "
        style += f"Répartition: {lateral_pct:.1f}% latéral, {forward_pct:.1f}% vers l'avant. "
        
        # Analyse des types de passes spéciaux
        special_passes = []
        if passing_metrics.get("long_balls", 0) > 3:
            special_passes.append("spécialiste longues balles")
        if passing_metrics.get("through_balls", 0) > 2:
            special_passes.append("passes décisives")
        if passing_metrics.get("crosses", 0) > 3:
            special_passes.append("centres")
            
        if special_passes:
            style += f"Spécialités: {', '.join(special_passes)}"
            
        return style

    def _analyze_defensive_positioning(self, defensive_metrics, spatial_metrics):
        """Analyse le positionnement défensif"""
        if not defensive_metrics:
            return "Pas d'activité défensive significative"
            
        zones = defensive_metrics.get("defensive_zones", {})
        intensity = defensive_metrics.get("defensive_intensity", "")
        
        analysis = f"Intensité défensive: {intensity}. "
        
        if zones:
            main_zone = max(zones.items(), key=lambda x: x[1])
            analysis += f"Zone défensive principale: {main_zone[0]} ({main_zone[1]} actions)"
            
        return analysis

    def _assess_tactical_discipline(self, player_data, metrics):
        """Évalue la discipline tactique"""
        temporal = metrics.get("temporal", {})
        consistency = temporal.get("consistency", "")
        
        discipline_score = 0
        factors = []
        
        if "consistent" in consistency.lower():
            discipline_score += 2
            factors.append("régularité temporelle")
        
        spatial = metrics.get("spatial", {})
        if spatial.get("mobility_score", 0) < 15:
            discipline_score += 1
            factors.append("respect du poste")
            
        basic = metrics.get("basic", {})
        if basic.get("success_rate", 0) > 75:
            discipline_score += 1
            factors.append("efficacité technique")
            
        if discipline_score >= 3:
            return f"Très discipliné tactiquement ({', '.join(factors)})"
        elif discipline_score >= 2:
            return f"Bonne discipline tactique ({', '.join(factors)})"
        else:
            return "Discipline tactique à améliorer"

    def _generate_technical_assessment(self, metrics):
        """Évaluation technique détaillée"""
        passing = metrics.get("passing", {})
        offensive = metrics.get("offensive", {})
        
        assessment = {
            "passing_quality": self._assess_passing_quality(passing),
            "first_touch": self._assess_first_touch(metrics),
            "shooting_ability": self._assess_shooting_ability(offensive),
            "dribbling_skills": self._assess_dribbling_skills(offensive),
            "technical_consistency": self._assess_technical_consistency(metrics)
        }
        
        return assessment

    def _assess_passing_quality(self, passing_metrics):
        """Évalue la qualité des passes"""
        if not passing_metrics:
            return "Données insuffisantes"
            
        accuracy = passing_metrics.get("pass_accuracy", 0)
        avg_length = passing_metrics.get("avg_pass_length", 0)
        variation = passing_metrics.get("pass_length_variation", 0)
        
        quality = f"Précision: {accuracy:.1f}%. "
        quality += f"Distance moyenne: {avg_length:.1f}m. "
        
        if accuracy > 90:
            quality += "Excellente précision technique."
        elif accuracy > 80:
            quality += "Bonne maîtrise technique."
        elif accuracy > 70:
            quality += "Précision correcte mais perfectible."
        else:
            quality += "Précision technique à améliorer."
            
        if variation > 10:
            quality += " Grande variété dans les distances."
        
        return quality

    def _assess_first_touch(self, metrics):
        """Évalue la qualité du premier contact"""
        pressure = metrics.get("pressure", {})
        pressure_rate = pressure.get("pressure_success_rate", 0)
        
        if pressure_rate > 80:
            return "Excellent premier contact même sous pression"
        elif pressure_rate > 65:
            return "Bon contrôle technique sous pression"
        elif pressure_rate > 50:
            return "Premier contact correct mais irrégulier sous pression"
        else:
            return "Premier contact à améliorer, difficultés sous pression"

    def _assess_shooting_ability(self, offensive_metrics):
        """Évalue les capacités de frappe"""
        if not offensive_metrics:
            return "Pas de tentatives de tir"
            
        shots = offensive_metrics.get("shots_total", 0)
        accuracy = offensive_metrics.get("shooting_accuracy", 0)
        goals = offensive_metrics.get("goals", 0)
        
        if shots == 0:
            return "Aucune tentative de tir dans ce match"
            
        assessment = f"{shots} tir(s), {accuracy:.1f}% de précision, {goals} but(s). "
        
        if accuracy > 60:
            assessment += "Excellente précision de frappe."
        elif accuracy > 40:
            assessment += "Précision de frappe correcte."
        else:
            assessment += "Précision de frappe à améliorer."
            
        return assessment

    def _assess_dribbling_skills(self, offensive_metrics):
        """Évalue les capacités de dribble"""
        if not offensive_metrics:
            return "Pas de données de dribble"
            
        attempts = offensive_metrics.get("dribbles_attempted", 0)
        success_rate = offensive_metrics.get("dribble_success_rate", 0)
        
        if attempts == 0:
            return "Aucune tentative de dribble"
            
        assessment = f"{attempts} tentative(s), {success_rate:.1f}% de réussite. "
        
        if success_rate > 70:
            assessment += "Excellent dribbleur."
        elif success_rate > 50:
            assessment += "Bonnes capacités de dribble."
        else:
            assessment += "Dribble à améliorer."
            
        return assessment

    def _assess_technical_consistency(self, metrics):
        """Évalue la régularité technique"""
        basic = metrics.get("basic", {})
        temporal = metrics.get("temporal", {})
        
        success_rate = basic.get("success_rate", 0)
        consistency = temporal.get("consistency", "")
        
        if success_rate > 85 and "consistent" in consistency.lower():
            return "Très régulier techniquement sur la durée"
        elif success_rate > 75:
            return "Bonne régularité technique"
        else:
            return "Régularité technique à améliorer"

    def _generate_physical_assessment(self, metrics):
        """Évaluation physique"""
        temporal = metrics.get("temporal", {})
        spatial = metrics.get("spatial", {})
        
        fatigue = temporal.get("fatigue_indicator", 0)
        mobility = spatial.get("mobility_score", 0)
        
        assessment = {
            "endurance": self._assess_endurance(fatigue, temporal),
            "mobility": self._assess_mobility(mobility, spatial),
            "intensity": self._assess_physical_intensity(metrics)
        }
        
        return assessment

    def _assess_endurance(self, fatigue_indicator, temporal_metrics):
        """Évalue l'endurance"""
        if fatigue_indicator < 10:
            return "Excellente endurance, maintient l'intensité"
        elif fatigue_indicator < 25:
            return "Bonne endurance avec légère baisse"
        elif fatigue_indicator < 40:
            return "Endurance correcte mais baisse notable"
        else:
            return "Baisse d'intensité significative en seconde période"

    def _assess_mobility(self, mobility_score, spatial_metrics):
        """Évalue la mobilité"""
        coverage = spatial_metrics.get("field_coverage_percentage", 0)
        
        mobility_assessment = f"Score de mobilité: {mobility_score:.1f}. "
        
        if mobility_score > 20:
            mobility_assessment += "Très mobile sur le terrain."
        elif mobility_score > 15:
            mobility_assessment += "Bonne mobilité."
        elif mobility_score > 10:
            mobility_assessment += "Mobilité modérée."
        else:
            mobility_assessment += "Mobilité limitée, reste dans sa zone."
            
        mobility_assessment += f" Couverture: {coverage:.1f}% du terrain."
        
        return mobility_assessment

    def _assess_physical_intensity(self, metrics):
        """Évalue l'intensité physique"""
        defensive = metrics.get("defensive", {})
        basic = metrics.get("basic", {})
        
        total_actions = basic.get("total_actions", 0)
        defensive_actions = defensive.get("total_defensive_actions", 0)
        
        intensity_score = total_actions + (defensive_actions * 2)
        
        if intensity_score > 50:
            return "Intensité physique très élevée"
        elif intensity_score > 30:
            return "Bonne intensité physique"
        elif intensity_score > 15:
            return "Intensité physique modérée"
        else:
            return "Intensité physique faible"

    def _generate_mental_assessment(self, metrics):
        """Évaluation mentale"""
        pressure = metrics.get("pressure", {})
        temporal = metrics.get("temporal", {})
        
        assessment = {
            "pressure_handling": pressure.get("pressure_handling", "Données insuffisantes"),
            "decision_making": self._assess_decision_making(metrics),
            "game_intelligence": self._assess_game_intelligence(metrics),
            "concentration": self._assess_concentration(temporal)
        }
        
        return assessment

    def _assess_decision_making(self, metrics):
        """Évalue la prise de décision"""
        passing = metrics.get("passing", {})
        
        pass_accuracy = passing.get("pass_accuracy", 0)
        risk_assessment = passing.get("risk_analysis", {}).get("risk_assessment", "")
        
        decision_quality = f"Précision des choix: {pass_accuracy:.1f}%. "
        decision_quality += f"Profil de risque: {risk_assessment}. "
        
        if pass_accuracy > 85 and "balanced" in risk_assessment.lower():
            decision_quality += "Excellente prise de décision."
        elif pass_accuracy > 75:
            decision_quality += "Bonnes décisions généralement."
        else:
            decision_quality += "Prise de décision à améliorer."
            
        return decision_quality

    def _assess_game_intelligence(self, metrics):
        """Évalue l'intelligence de jeu"""
        offensive = metrics.get("offensive", {})
        defensive = metrics.get("defensive", {})
        
        key_passes = offensive.get("key_passes", 0)
        interceptions = defensive.get("interceptions", 0)
        
        intelligence_score = key_passes * 3 + interceptions * 2
        
        intelligence_assessment = f"Score d'intelligence: {intelligence_score}. "
        
        if intelligence_score > 10:
            intelligence_assessment += "Très bonne lecture du jeu."
        elif intelligence_score > 5:
            intelligence_assessment += "Bonne compréhension tactique."
        else:
            intelligence_assessment += "Intelligence de jeu à développer."
            
        return intelligence_assessment

    def _assess_concentration(self, temporal_metrics):
        """Évalue la concentration"""
        consistency = temporal_metrics.get("consistency", "")
        
        if "very consistent" in consistency.lower():
            return "Concentration exemplaire sur toute la durée"
        elif "consistent" in consistency.lower():
            return "Bonne concentration avec quelques fluctuations"
        elif "moderate" in consistency.lower():
            return "Concentration correcte mais irrégulière"
        else:
            return "Difficultés de concentration, performance en dents de scie"

    def _identify_strengths(self, metrics):
        """Identifie les points forts"""
        strengths = []
        
        basic = metrics.get("basic", {})
        passing = metrics.get("passing", {})
        defensive = metrics.get("defensive", {})
        offensive = metrics.get("offensive", {})
        pressure = metrics.get("pressure", {})
        
        if basic.get("success_rate", 0) > 85:
            strengths.append("Très grande efficacité technique")
            
        if passing.get("pass_accuracy", 0) > 90:
            strengths.append("Précision de passe exceptionnelle")
            
        if defensive.get("tackle_success_rate", 0) > 75:
            strengths.append("Excellent dans les duels défensifs")
            
        if offensive.get("dribble_success_rate", 0) > 70:
            strengths.append("Très bon dribbleur")
            
        if pressure.get("pressure_success_rate", 0) > 80:
            strengths.append("Excellent sous pression")
            
        if metrics.get("influence_score", 0) > 30:
            strengths.append("Forte influence sur le jeu")
            
        return strengths if strengths else ["Profil équilibré sans point fort dominant"]

    def _identify_weaknesses(self, metrics):
        """Identifie les axes d'amélioration"""
        weaknesses = []
        
        basic = metrics.get("basic", {})
        passing = metrics.get("passing", {})
        defensive = metrics.get("defensive", {})
        offensive = metrics.get("offensive", {})
        temporal = metrics.get("temporal", {})
        
        if basic.get("success_rate", 0) < 70:
            weaknesses.append("Efficacité technique générale à améliorer")
            
        if passing.get("pass_accuracy", 0) < 75:
            weaknesses.append("Précision des passes à travailler")
            
        if temporal.get("fatigue_indicator", 0) > 30:
            weaknesses.append("Endurance à développer")
            
        if defensive.get("total_defensive_actions", 0) < 3:
            weaknesses.append("Implication défensive insuffisante")
            
        if offensive.get("shots_total", 0) == 0 and offensive.get("key_passes", 0) < 2:
            weaknesses.append("Contribution offensive à intensifier")
            
        lateral_pct = passing.get("risk_analysis", {}).get("lateral_percentage", 0)
        if lateral_pct > 70:
            weaknesses.append("Prise de risque offensive à développer")
            
        return weaknesses if weaknesses else ["Pas d'axe d'amélioration majeur identifié"]

    def _analyze_contextual_factors(self, player_data):
        """Analyse les facteurs contextuels"""
        factors = {
            "starting_status": "Titulaire" if player_data["is_starter"] else "Remplaçant",
            "position": player_data["position"],
            "team_context": f"Équipe {player_data['team']}",
            "physical_attributes": f"Taille: {player_data['height']}cm, Poids: {player_data['weight']}kg, Âge: {player_data['age']} ans"
        }
        
        context_analysis = ""
        
        if not player_data["is_starter"]:
            context_analysis += "Entrée en cours de jeu - analyse basée sur temps de jeu partiel. "
            
        if player_data["is_motm"]:
            context_analysis += "Élu homme du match. "
            
        factors["context_analysis"] = context_analysis
        
        return factors

    def _generate_markdown_report(self, player_data, metrics, detailed_analysis):
        """Génère le rapport Markdown complet"""
        match_info = self.preprocessed_data["match_info"]
        
        report = f"""# Rapport de Match - {player_data['name']}

## Informations du Match
- **Match**: {match_info['home_team']} vs {match_info['away_team']} ({match_info['score']})
- **Compétition**: {match_info['competition']}
- **Stade**: {match_info['venue']}
- **Arbitre**: {match_info['referee']}

## Profil Joueur
- **Nom**: {player_data['name']}
- **Position**: {player_data['position']}
- **Numéro**: {player_data['shirt_number']}
- **Équipe**: {player_data['team'].title()}
- **Statut**: {'Titulaire' if player_data['is_starter'] else 'Remplaçant'}
- **Âge**: {player_data['age']} ans
- **Taille**: {player_data['height']} cm
- **Poids**: {player_data['weight']} kg
{'- **🏆 Homme du Match**' if player_data['is_motm'] else ''}

## Résumé Exécutif

{detailed_analysis['performance_summary']}

**Score d'Influence Globale**: {metrics.get('influence_score', 0):.1f}/50

## Analyse Technique Détaillée

### Passes et Distribution
"""
        
        passing = metrics.get("passing", {})
        if passing:
            report += f"""
- **Total des passes**: {passing.get('total_passes', 0)}
- **Passes réussies**: {passing.get('successful_passes', 0)}
- **Précision**: {passing.get('pass_accuracy', 0):.1f}%
- **Distance moyenne**: {passing.get('avg_pass_length', 0):.1f} mètres
- **Passes longues**: {passing.get('long_balls', 0)}
- **Passes décisives**: {passing.get('through_balls', 0)}
- **Centres**: {passing.get('crosses', 0)}

#### Analyse du Style de Passe
{detailed_analysis['tactical_analysis']['passing_style']}

#### Répartition Directionnelle
"""
            risk_analysis = passing.get('risk_analysis', {})
            if risk_analysis:
                report += f"""
- **Passes latérales**: {risk_analysis.get('lateral_percentage', 0):.1f}%
- **Passes vers l'avant**: {risk_analysis.get('forward_percentage', 0):.1f}%
- **Passes arrière**: {risk_analysis.get('backward_percentage', 0):.1f}%

**Évaluation**: {risk_analysis.get('risk_assessment', 'Indéterminé')}

**Interprétation**: """
                
                lateral_pct = risk_analysis.get('lateral_percentage', 0)
                forward_pct = risk_analysis.get('forward_percentage', 0)
                
                if lateral_pct > 70:
                    report += f"Avec {lateral_pct:.1f}% de passes latérales, {player_data['name']} privilégie la sécurité et la circulation du ballon. "
                    report += "Cela témoigne d'un joueur fiable sous pression mais qui pourrait être plus incisif vers l'avant pour créer du danger. "
                    if forward_pct < 20:
                        report += "Le faible pourcentage de passes vers l'avant ({forward_pct:.1f}%) suggère un manque de prise de risque offensive."
                elif forward_pct > 40:
                    report += f"Avec {forward_pct:.1f}% de passes vers l'avant, {player_data['name']} montre un profil offensif et une volonté de faire progresser l'équipe. "
                    report += "Cette prise de risque constante démontre de la confiance technique et une vision du jeu tournée vers la création."
                else:
                    report += f"Répartition équilibrée entre passes latérales ({lateral_pct:.1f}%) et vers l'avant ({forward_pct:.1f}%), "
                    report += f"montrant une capacité d'adaptation selon les phases de jeu."

        report += f"""

### Actions Défensives
"""
        
        defensive = metrics.get("defensive", {})
        if defensive:
            report += f"""
- **Tacles tentés**: {defensive.get('tackles_attempted', 0)}
- **Tacles réussis**: {defensive.get('tackles_won', 0)}
- **Efficacité des tacles**: {defensive.get('tackle_success_rate', 0):.1f}%
- **Interceptions**: {defensive.get('interceptions', 0)}
- **Récupérations**: {defensive.get('ball_recoveries', 0)}
- **Dégagements**: {defensive.get('clearances', 0)}

**Intensité défensive**: {defensive.get('defensive_intensity', 'Inconnue')}

**Analyse défensive**: """
            
            total_def_actions = defensive.get('total_defensive_actions', 0)
            if total_def_actions > 8:
                report += f"Très impliqué défensivement avec {total_def_actions} actions. Montre un tempérament de guerrier et une volonté de récupérer le ballon."
            elif total_def_actions > 5:
                report += f"Bonne implication défensive ({total_def_actions} actions). Équilibre bien ses tâches offensives et défensives."
            elif total_def_actions > 2:
                report += f"Implication défensive modérée ({total_def_actions} actions). Pourrait être plus agressif dans les duels."
            else:
                report += f"Faible activité défensive ({total_def_actions} actions). Se concentre davantage sur les phases offensives."

        report += f"""

### Actions Offensives
"""
        
        offensive = metrics.get("offensive", {})
        if offensive:
            report += f"""
- **Tirs tentés**: {offensive.get('shots_total', 0)}
- **Buts marqués**: {offensive.get('goals', 0)}
- **Tirs cadrés**: {offensive.get('shots_on_target', 0)}
- **Précision de tir**: {offensive.get('shooting_accuracy', 0):.1f}%
- **Passes clés**: {offensive.get('key_passes', 0)}
- **Dribbles tentés**: {offensive.get('dribbles_attempted', 0)}
- **Dribbles réussis**: {offensive.get('dribbles_successful', 0)}
- **Efficacité dribble**: {offensive.get('dribble_success_rate', 0):.1f}%

**Analyse offensive**: """
            
            shots = offensive.get('shots_total', 0)
            key_passes = offensive.get('key_passes', 0)
            dribbles = offensive.get('dribbles_attempted', 0)
            
            if shots > 3 or key_passes > 3:
                report += f"Forte contribution offensive avec {shots} tir(s) et {key_passes} passe(s) clé(s). Joueur décisif dans les phases offensives."
            elif shots > 1 or key_passes > 1:
                report += f"Contribution offensive correcte ({shots} tir(s), {key_passes} passe(s) clé(s)). Pourrait être plus entreprenant."
            else:
                report += f"Contribution offensive limitée. Doit davantage s'impliquer dans la finition et la création."
                
            if dribbles > 5:
                report += f" Très bon dribbleur ({dribbles} tentatives), aime prendre des initiatives individuelles."

        report += f"""

## Analyse Tactique Approfondie

### Positionnement et Mobilité
{detailed_analysis['tactical_analysis']['positioning']}

### Couverture du Terrain
{detailed_analysis['tactical_analysis']['field_coverage']}

### Style de Jeu et Personnalité Footballistique
"""

        # Analyse de personnalité basée sur les métriques
        lateral_pct = passing.get("risk_analysis", {}).get("lateral_percentage", 0)
        pressure_rate = metrics.get("pressure", {}).get("pressure_success_rate", 0)
        mobility = metrics.get("spatial", {}).get("mobility_score", 0)
        
        if lateral_pct > 70 and pressure_rate > 75:
            report += f"**Profil**: Joueur sécuritaire et fiable. {player_data['name']} privilégie la possession et la sécurité technique. "
            report += "Excellent sous pression mais pourrait oser davantage pour créer le déséquilibre. "
            report += "Type de joueur sur qui on peut compter dans les moments difficiles."
        elif lateral_pct < 50 and offensive.get('dribbles_attempted', 0) > 3:
            report += f"**Profil**: Joueur créatif et entreprenant. {player_data['name']} cherche constamment à faire progresser l'équipe. "
            report += "N'hésite pas à prendre des risques pour créer du danger. Tempérament offensif marqué."
        elif defensive.get('total_defensive_actions', 0) > 6:
            report += f"**Profil**: Joueur combattif et généreux. {player_data['name']} n'hésite pas à se sacrifier pour l'équipe. "
            report += "Tempérament de guerrier qui compense parfois les lacunes techniques par l'engagement."
        else:
            report += f"**Profil**: Joueur équilibré et polyvalent. {player_data['name']} s'adapte aux besoins de l'équipe selon les phases de jeu."

        report += f"""

### Discipline Tactique
{detailed_analysis['tactical_analysis']['tactical_discipline']}

## Analyse Mentale et Physique

### Gestion de la Pression
{detailed_analysis['mental_assessment']['pressure_handling']}

**Analyse psychologique**: """
        
        if pressure_rate > 80:
            report += f"Mentalité exceptionnelle. {player_data['name']} garde son sang-froid même dans l'intensité. "
            report += "Joueur sur qui on peut compter dans les moments cruciaux."
        elif pressure_rate > 65:
            report += f"Bonne maîtrise mentale. Gère généralement bien la pression mais peut parfois perdre en précision."
        else:
            report += f"Difficultés sous pression. Doit travailler la concentration et la gestion du stress en match."

        report += f"""

### Évolution et Endurance
{detailed_analysis['physical_assessment']['endurance']}

### Mobilité et Intensité
{detailed_analysis['physical_assessment']['mobility']}

## Évolution Temporelle Détaillée
"""
        
        temporal = metrics.get("temporal", {})
        if temporal:
            time_dist = temporal.get("time_distribution", {})
            report += f"""
### Répartition de l'Activité par Période (15 min)

| Période | Actions | Analyse |
|---------|---------|---------|
| **0-15 min** | {time_dist.get('0-15', 0)} | {'Début de match actif' if time_dist.get('0-15', 0) > 5 else 'Mise en route progressive'} |
| **16-30 min** | {time_dist.get('16-30', 0)} | {'Maintien du rythme' if time_dist.get('16-30', 0) >= time_dist.get('0-15', 0) else 'Baisse d\'activité'} |
| **31-45 min** | {time_dist.get('31-45', 0)} | {'Finish fort de première période' if time_dist.get('31-45', 0) > 4 else 'Fin de première période calme'} |
| **46-60 min** | {time_dist.get('46-60', 0)} | {'Reprise énergique' if time_dist.get('46-60', 0) > time_dist.get('31-45', 0) else 'Reprise en douceur'} |
| **61-75 min** | {time_dist.get('61-75', 0)} | {'Maintien de l\'intensité' if time_dist.get('61-75', 0) >= time_dist.get('46-60', 0) else 'Première baisse'} |
| **76-90 min** | {time_dist.get('76-90', 0)} | {'Finish fort' if time_dist.get('76-90', 0) > 4 else 'Fin de match difficile'} |

**Constance**: {temporal.get('consistency', 'Inconnue')}
**Indicateur de fatigue**: {temporal.get('fatigue_indicator', 0):.1f}%

**Interprétation**: """
            
            fatigue = temporal.get('fatigue_indicator', 0)
            first_half = temporal.get('first_half_intensity', 0)
            second_half = temporal.get('second_half_intensity', 0)
            
            if fatigue < 10:
                report += f"Excellente condition physique. {player_data['name']} maintient son niveau sur toute la durée du match."
            elif fatigue < 25:
                report += f"Bonne endurance avec une légère baisse en seconde période ({fatigue:.1f}% de baisse)."
            else:
                report += f"Baisse notable d'activité en seconde période ({fatigue:.1f}% de baisse). Condition physique à travailler."

        report += f"""

## Points Forts Identifiés

"""
        for i, strength in enumerate(detailed_analysis['areas_of_excellence'], 1):
            report += f"{i}. ✅ **{strength}**\n"

        report += f"""

## Axes d'Amélioration Prioritaires

"""
        for i, weakness in enumerate(detailed_analysis['improvement_areas'], 1):
            report += f"{i}. 🔶 **{weakness}**\n"

        report += f"""

## Évaluation Globale par Domaine

| Domaine | Note | Commentaire |
|---------|------|-------------|
| **Technique** | {self._get_technical_rating(metrics)} | {detailed_analysis['technical_assessment']['passing_quality'][:80]}... |
| **Tactique** | {self._get_tactical_rating(detailed_analysis)} | Discipline et positionnement |
| **Physique** | {self._get_physical_rating(metrics)} | Endurance et intensité |
| **Mental** | {self._get_mental_rating(metrics)} | Gestion de pression et concentration |

## Recommandations Personnalisées

### Pour l'Entraîneur
"""
        
        # Recommandations spécifiques basées sur l'analyse
        recommendations = []
        
        if lateral_pct > 70:
            recommendations.append(f"Encourager {player_data['name']} à prendre plus de risques vers l'avant lors des exercices de possession")
        
        if defensive.get('total_defensive_actions', 0) < 3:
            recommendations.append(f"Travailler l'agressivité défensive et les duels avec {player_data['name']}")
        
        if metrics.get('temporal', {}).get('fatigue_indicator', 0) > 30:
            recommendations.append(f"Prévoir un plan de préparation physique spécifique pour améliorer l'endurance")
        
        if pressure_rate < 65:
            recommendations.append(f"Multiplier les exercices sous pression pour améliorer la gestion du stress")
        
        if not recommendations:
            recommendations.append(f"Maintenir le niveau actuel et continuer le développement progressif")
        
        for rec in recommendations:
            report += f"- {rec}\n"

        report += f"""

### Pour le Joueur
"""
        
        player_recommendations = []
        
        if passing.get('pass_accuracy', 0) < 80:
            player_recommendations.append("Travail technique quotidien sur la précision des passes courtes et moyennes")
        
        if lateral_pct > 70:
            player_recommendations.append("Oser davantage la passe verticale, avoir confiance en ses capacités techniques")
        
        if offensive.get('key_passes', 0) < 2:
            player_recommendations.append("Chercher davantage les espaces pour créer du danger offensif")
        
        if defensive.get('total_defensive_actions', 0) < 3:
            player_recommendations.append("Être plus agressif dans les duels et anticiper davantage les trajectoires")
        
        if not player_recommendations:
            player_recommendations.append("Continuer sur cette lancée et maintenir ce niveau d'excellence")
        
        for rec in player_recommendations:
            report += f"- {rec}\n"

        report += f"""

## Comparaison avec le Profil de Poste

### Attentes pour un {player_data['position']}
"""
        
        position = player_data['position']
        if 'CM' in position or 'CDM' in position:
            report += f"""
- **Passes**: ✅ Attendu >80% → Réalisé {passing.get('pass_accuracy', 0):.1f}%
- **Récupérations**: {'✅' if defensive.get('ball_recoveries', 0) > 3 else '⚠️'} Attendu >3 → Réalisé {defensive.get('ball_recoveries', 0)}
- **Couverture**: {'✅' if metrics.get('spatial', {}).get('field_coverage_percentage', 0) > 25 else '⚠️'} Attendu >25% → Réalisé {metrics.get('spatial', {}).get('field_coverage_percentage', 0):.1f}%
"""
        elif 'CB' in position:
            report += f"""
- **Dégagements**: {'✅' if defensive.get('clearances', 0) > 2 else '⚠️'} Attendu >2 → Réalisé {defensive.get('clearances', 0)}
- **Tacles**: {'✅' if defensive.get('tackles_won', 0) > 2 else '⚠️'} Attendu >2 → Réalisé {defensive.get('tackles_won', 0)}
- **Précision**: ✅ Attendu >85% → Réalisé {passing.get('pass_accuracy', 0):.1f}%
"""
        elif 'AM' in position or 'RW' in position or 'LW' in position:
            report += f"""
- **Créativité**: {'✅' if offensive.get('key_passes', 0) > 1 else '⚠️'} Attendu >1 → Réalisé {offensive.get('key_passes', 0)}
- **Dribbles**: {'✅' if offensive.get('dribbles_attempted', 0) > 2 else '⚠️'} Attendu >2 → Réalisé {offensive.get('dribbles_attempted', 0)}
- **Contribution**: {'✅' if (offensive.get('shots_total', 0) + offensive.get('key_passes', 0)) > 2 else '⚠️'} Offensive attendue
"""

        report += f"""

## Contextualisation de la Performance

### Influence du Statut
{detailed_analysis['contextual_factors']['context_analysis'] or 'Performance en tant que titulaire dans le système tactique.'}

### Impact sur le Résultat Final
"""
        
        influence_score = metrics.get('influence_score', 0)
        if influence_score > 30:
            report += f"**Impact majeur** - Avec un score d'influence de {influence_score:.1f}, {player_data['name']} a été déterminant dans ce match."
        elif influence_score > 20:
            report += f"**Impact notable** - Score d'influence de {influence_score:.1f}, bonne contribution à la performance collective."
        elif influence_score > 10:
            report += f"**Impact modéré** - Score d'influence de {influence_score:.1f}, contribution correcte sans être déterminante."
        else:
            report += f"**Impact limité** - Score d'influence de {influence_score:.1f}, faible influence sur le déroulement du match."

        report += f"""

---

## Conclusion

{player_data['name']} a livré une performance """
        
        avg_rating = (metrics.get('basic', {}).get('success_rate', 0) + passing.get('pass_accuracy', 0)) / 2
        if avg_rating > 80:
            report += "excellente"
        elif avg_rating > 70:
            report += "très correcte"
        elif avg_rating > 60:
            report += "correcte"
        else:
            report += "perfectible"
            
        report += f" dans ce match avec {metrics.get('basic', {}).get('total_actions', 0)} actions et {metrics.get('basic', {}).get('success_rate', 0):.1f}% de réussite. "
        
        # Point principal de progression
        main_weakness = detailed_analysis['improvement_areas'][0] if detailed_analysis['improvement_areas'] else None
        if main_weakness and "prise de risque" in main_weakness.lower():
            report += f"L'axe de progression principal concerne sa prise de risque offensive pour maximiser son impact créatif."
        elif main_weakness and "défensive" in main_weakness.lower():
            report += f"L'axe de progression principal concerne son implication défensive pour équilibrer son jeu."
        elif main_weakness and "endurance" in main_weakness.lower():
            report += f"L'axe de progression principal concerne sa condition physique pour maintenir l'intensité."
        else:
            report += f"Profil équilibré qui doit continuer sur cette lancée."

        report += f"""

---
*Rapport généré automatiquement le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*  
*Analyse basée sur {len(player_data['events'])} actions durant le match*  
*Système d'analyse WhoScored Enhanced v2.0*
"""
        
        return report

    def _get_technical_rating(self, metrics):
        """Évaluation technique globale"""
        basic = metrics.get("basic", {})
        passing = metrics.get("passing", {})
        
        success_rate = basic.get("success_rate", 0)
        pass_accuracy = passing.get("pass_accuracy", 0)
        
        avg_rating = (success_rate + pass_accuracy) / 2
        
        if avg_rating > 85:
            return "⭐⭐⭐⭐⭐ Excellent"
        elif avg_rating > 75:
            return "⭐⭐⭐⭐ Très Bien"
        elif avg_rating > 65:
            return "⭐⭐⭐ Bien"
        elif avg_rating > 55:
            return "⭐⭐ Correct"
        else:
            return "⭐ À améliorer"

    def _get_tactical_rating(self, detailed_analysis):
        """Évaluation tactique globale"""
        discipline = detailed_analysis['tactical_analysis']['tactical_discipline']
        
        if "très discipliné" in discipline.lower():
            return "⭐⭐⭐⭐⭐ Excellent"
        elif "bonne discipline" in discipline.lower():
            return "⭐⭐⭐⭐ Très Bien"
        elif "discipline" in discipline.lower():
            return "⭐⭐⭐ Bien"
        else:
            return "⭐⭐ Correct"

    def _get_physical_rating(self, metrics):
        """Évaluation physique globale"""
        temporal = metrics.get("temporal", {})
        fatigue = temporal.get("fatigue_indicator", 0)
        
        if fatigue < 10:
            return "⭐⭐⭐⭐⭐ Excellent"
        elif fatigue < 25:
            return "⭐⭐⭐⭐ Très Bien"
        elif fatigue < 40:
            return "⭐⭐⭐ Bien"
        else:
            return "⭐⭐ À améliorer"

    def _get_mental_rating(self, metrics):
        """Évaluation mentale globale"""
        pressure = metrics.get("pressure", {})
        pressure_rate = pressure.get("pressure_success_rate", 0)
        
        if pressure_rate > 80:
            return "⭐⭐⭐⭐⭐ Excellent"
        elif pressure_rate > 65:
            return "⭐⭐⭐⭐ Très Bien"
        elif pressure_rate > 50:
            return "⭐⭐⭐ Bien"
        else:
            return "⭐⭐ À améliorer"

    def generate_team_comparative_analysis(self, output_dir="player_data"):
        """Génère une analyse comparative de tous les joueurs de l'équipe"""
        if not hasattr(self, 'preprocessed_data') or not self.preprocessed_data:
            self.preprocess_match_data()
            
        os.makedirs(output_dir, exist_ok=True)
        
        team_analysis = {
            "match_info": self.preprocessed_data["match_info"],
            "players_analysis": {},
            "team_metrics": self._calculate_team_metrics(),
            "comparative_rankings": self._generate_comparative_rankings(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Analyse de chaque joueur
        for player_id, player_data in self.preprocessed_data["players"].items():
            if not player_data["events"]:
                continue
                
            advanced_metrics = self.preprocessed_data["advanced_metrics"].get(player_id, {})
            
            team_analysis["players_analysis"][player_data["name"]] = {
                "player_info": player_data,
                "metrics": advanced_metrics,
                "summary": self._generate_performance_summary(player_data, advanced_metrics)
            }
        
        # Sauvegarde JSON
        json_filename = "team_comparative_analysis.json"
        json_filepath = os.path.join(output_dir, json_filename)
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(team_analysis, f, ensure_ascii=False, indent=2)
        
        print(f"Analyse comparative d'équipe générée : {json_filepath}")
        return json_filepath

    def _calculate_team_metrics(self):
        """Calcule les métriques d'équipe"""
        home_players = []
        away_players = []
        
        for player_id, player_data in self.preprocessed_data["players"].items():
            if player_data["team"] == "home":
                home_players.append(player_id)
            else:
                away_players.append(player_id)
        
        return {
            "home_team": {
                "player_count": len(home_players),
                "avg_influence": self._calculate_average_influence(home_players),
                "total_actions": self._calculate_total_actions(home_players)
            },
            "away_team": {
                "player_count": len(away_players),
                "avg_influence": self._calculate_average_influence(away_players),
                "total_actions": self._calculate_total_actions(away_players)
            }
        }

    def _calculate_average_influence(self, player_ids):
        """Calcule l'influence moyenne d'un groupe de joueurs"""
        influences = []
        for pid in player_ids:
            metrics = self.preprocessed_data["advanced_metrics"].get(pid, {})
            influence = metrics.get("influence_score", 0)
            influences.append(influence)
        
        return statistics.mean(influences) if influences else 0

    def _calculate_total_actions(self, player_ids):
        """Calcule le total d'actions d'un groupe de joueurs"""
        total = 0
        for pid in player_ids:
            metrics = self.preprocessed_data["advanced_metrics"].get(pid, {})
            basic = metrics.get("basic", {})
            total += basic.get("total_actions", 0)
        
        return total

    def _generate_comparative_rankings(self):
        """Génère des classements comparatifs"""
        rankings = {
            "influence": [],
            "passing_accuracy": [],
            "defensive_actions": [],
            "offensive_contribution": []
        }
        
        for player_id, player_data in self.preprocessed_data["players"].items():
            metrics = self.preprocessed_data["advanced_metrics"].get(player_id, {})
            
            if not metrics:
                continue
                
            player_name = player_data["name"]
            
            # Classements
            influence = metrics.get("influence_score", 0)
            rankings["influence"].append({"name": player_name, "value": influence})
            
            passing = metrics.get("passing", {})
            pass_accuracy = passing.get("pass_accuracy", 0)
            rankings["passing_accuracy"].append({"name": player_name, "value": pass_accuracy})
            
            defensive = metrics.get("defensive", {})
            def_actions = defensive.get("total_defensive_actions", 0)
            rankings["defensive_actions"].append({"name": player_name, "value": def_actions})
            
            offensive = metrics.get("offensive", {})
            off_score = offensive.get("shots_total", 0) + offensive.get("key_passes", 0) * 2
            rankings["offensive_contribution"].append({"name": player_name, "value": off_score})
        
        # Tri des classements
        for category in rankings:
            rankings[category].sort(key=lambda x: x["value"], reverse=True)
        
        return rankings
    
    
    
    # ===== NOUVELLE MÉTHODE dans whoscored_data_extractor.py =====

    def generate_unified_player_analysis(self, player_name, output_dir="player_data"):
        """Génère UN SEUL JSON complet avec toutes les stats et analyses"""
        print(f"🔍 Génération de l'analyse unifiée pour {player_name}...")

        # 1. Extraction des données de base (comme extract_player_stats_and_events)
        self.data = self._extract_data_html()
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

        # 2. Préprocessing pour l'analyse avancée
        self.preprocess_match_data()

        # Trouver le joueur dans les données préprocessées
        advanced_metrics = {}
        player_data_advanced = {}

        for pid, pdata in self.preprocessed_data["players"].items():
            if pdata["name"].lower() == player_name.lower():
                player_data_advanced = pdata
                advanced_metrics = self.preprocessed_data["advanced_metrics"].get(pid, {})
                break


        # 3. Construction du JSON unifié avec COMPATIBILITÉ VISUALIZER
        unified_data = {
            # === COMPATIBILITÉ AVEC LES VISUALIZERS (structure originale) ===
            "player_name": player_name,  # ✅ AJOUTÉ pour compatibilité
            "player_id": player_id,      # ✅ AJOUTÉ pour compatibilité
            "team": team,                # ✅ AJOUTÉ pour compatibilité
            "position": player_stats.get("position"),    # ✅ AJOUTÉ
            "shirtNo": player_stats.get("shirtNo"),      # ✅ AJOUTÉ
            "height": player_stats.get("height"),        # ✅ AJOUTÉ
            "weight": player_stats.get("weight"),        # ✅ AJOUTÉ
            "age": player_stats.get("age"),              # ✅ AJOUTÉ
            "isFirstEleven": player_stats.get("isFirstEleven"),    # ✅ AJOUTÉ
            "isManOfTheMatch": player_stats.get("isManOfTheMatch"), # ✅ AJOUTÉ
            "stats": player_stats.get("stats", {}),     # ✅ AJOUTÉ pour compatibilité
            "events": player_events,                    # ✅ AJOUTÉ pour compatibilité

            # === INFORMATIONS DU MATCH ===
            "match_info": self.preprocessed_data.get("match_info", {}),

            # === INFORMATIONS JOUEUR DÉTAILLÉES ===
            "player_basic_info": {
                "player_name": player_name,
                "player_id": player_id,
                "team": team,
                "position": player_stats.get("position"),
                "shirtNo": player_stats.get("shirtNo"),
                "height": player_stats.get("height"),
                "weight": player_stats.get("weight"),
                "age": player_stats.get("age"),
                "isFirstEleven": player_stats.get("isFirstEleven"),
                "isManOfTheMatch": player_stats.get("isManOfTheMatch")
            },

            # === STATS BRUTES WHOSCORED ===
            "whoscored_raw_stats": player_stats.get("stats", {}),

            # === MÉTRIQUES AVANCÉES CALCULÉES ===
            "advanced_metrics": advanced_metrics,

            # === ANALYSE DÉTAILLÉE TEXTUELLE ===
            "detailed_analysis": {},

            # === MÉTADONNÉES ===
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "analysis_version": "WhoScored Enhanced v2.0",
                "total_events": len(player_events),
                "data_source": "WhoScored.com",
                "structure_note": "Compatible avec visualizers existants + données avancées"
            }
        }
        # 4. Génération de l'analyse détaillée si les métriques avancées existent
        if advanced_metrics and player_data_advanced:
            unified_data["detailed_analysis"] = self._generate_detailed_analysis(
                player_data_advanced, advanced_metrics
            )

        # 5. Sauvegarde du fichier unifié
        match_name = os.path.basename(self.html_path).replace("data/", "").replace(".html", "")
        output_file = os.path.join(output_dir, f"{player_name.replace(' ', '_')}_{match_name}_COMPLETE.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(unified_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Fichier JSON unifié généré: {output_file}")
        print(f"📊 Contenu: Stats de base + {len(player_events)} événements + Analyse avancée")

        return output_file

############ Exemple d'utilisation simple
###########def example_usage():
###########    """Exemple d'utilisation de la classe étendue"""
###########    
###########    # Utilisation exactement comme avant + nouvelles fonctionnalités
###########    extractor = WhoScoredDataExtractor()
###########    
###########    # Méthodes existantes (inchangées)
###########    # extractor.extract_player_stats_and_events("Vitinha")
###########    # extractor.extract_player_aggregate_stats("Vitinha")
###########    
###########    # Nouvelles méthodes d'analyse complète
###########    # extractor.preprocess_match_data("path/to/match.html")  # Optionnel si déjà fait
###########    # analysis_files = extractor.generate_complete_player_analysis("Vitinha")
###########    # team_analysis = extractor.generate_team_comparative_analysis()
###########    
###########    print("WhoScoredDataExtractor Enhanced - Nouvelles fonctionnalités disponibles:")
###########    print("1. preprocess_match_data() - Prétraite les données pour l'analyse")
###########    print("2. generate_complete_player_analysis(player_name) - Génère JSON + rapport MD complet")
###########    print("3. generate_team_comparative_analysis() - Analyse comparative d'équipe")
###########    print("\nToutes les méthodes existantes sont conservées et fonctionnent comme avant!")
###########
###########if __name__ == "__main__":
###########    example_usage()
















