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
        raise NotImplementedError("Cette méthode doit être implémentée dans les classes héritées.")
    

    def extract_match_teams(self):
        # Expression régulière pour capturer tout ce qui vient après la date "yyyy-yyyy-"
        match = re.search(r'\d{4}-\d{4}-(.+)', self.html_path)
        if match:
            # Récupérer tout ce qui est après la date "yyyy-yyyy-"
            return match.group(1)
        return None

    def get_competition_from_filename(self):
        """Extracts and formats the competition name from the HTML filename."""
        filename = os.path.basename(self.html_path)
        competition_keywords = [
            "France-Ligue-1", "England-Premier-League", "Italy-Serie-A", "Spain-LaLiga", "Germany-Bundesliga",
            "Europe-Champions-League", "Europe-Europa-League", "Europe-Conference-League", "Angleterre-League-Cup", "Portugal-Liga-Portugal"
        ]

        for keyword in competition_keywords:
            if keyword.lower() in filename.lower():
                parts = keyword.split('-')[1:]
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
            return "#000000", "#5a5403"  # Default colors in case of an error

        competition_colors = colors_data.get("competitions", {}).get(competition_name)
        if competition_colors:
            return competition_colors["color1"], competition_colors["color2"]
        else:
            return "#000000", "#5a5403"  # Default colors if not found

    def get_competition_and_colors(self):
        """Combines competition extraction and color loading."""
        competition = self.get_competition_from_filename()
        if competition:
            color1, color2 = self.load_colors_for_competition(competition)
            return competition, color1, color2
        else:
            return "Unknown Competition", "#000000", "#5a5403"

    def extract_player_stats_and_events(self, player_name, output_dir="player_data"):
        raise NotImplementedError("Cette méthode doit être implémentée dans les classes héritées.")
