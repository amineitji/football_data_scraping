import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.image as mpimg
import numpy as np
import matplotlib.colors as mcolors
import json
import json
import os
from mplsoccer import Pitch, VerticalPitch
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.gridspec import GridSpec
import matplotlib.colors as mcolors
import matplotlib.image as mpimg
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy.ndimage import gaussian_filter
import cmasher as cmr
from player_image_downloader import PlayerProfileScraper
import re
from match_data_extractor import MatchDataExtractor

from matplotlib.animation import FuncAnimation
import matplotlib.patches as mpatches

class PlayerSeasonVisualizer:
    def __init__(self, player_data, color1="#000000", color2="#5a5403"):
        self.player_data = player_data
        self.color1 = color1
        self.color2 = color2


    def _add_horizontal_bar(self, ax, label, value, max_value):
        bar_height = 0.2
        filled_length = 0

        if max_value != 0:
            filled_length = value / max_value

        # Vérifier si la barre concerne les fautes commises
        if 'Fautes commises' in label:
            # Palette de couleurs pour les fautes (toujours rouge)
            cmap = mcolors.LinearSegmentedColormap.from_list('red', ['#FF0000', '#FF0000'])  # Palette entièrement rouge
        else:
            # Palette de couleurs pour les autres événements (du rouge à vert)
            cmap = mcolors.LinearSegmentedColormap.from_list('orange', ['orange', '#6DF176'])  # Rouge -> Vert

        # Couleur interpolée en fonction de la longueur remplie
        bar_color = cmap(filled_length)

        # Barre de fond (gris) sans coins arrondis
        ax.barh(0, 1, height=bar_height, color='#505050', edgecolor='none')

        # Barre remplie avec la couleur interpolée sans coins arrondis
        ax.barh(0, filled_length, height=bar_height, color=bar_color, edgecolor='none')

        # Ajouter l'étiquette à gauche de la barre (très proche de la barre)
        ax.text(-0.005, 0.6, label, va='center', ha='left', fontsize=20, color='white', fontweight='bold', transform=ax.transAxes)  # Position de l'étiquette à gauche

        # Ajouter la valeur à droite de la barre (très proche de la barre)
        ax.text(1.005, 0.6, f'{value}/{max_value}', va='center', ha='right', fontsize=20, color='white', fontweight='bold', transform=ax.transAxes)  # Position de la valeur à droite

        # Supprimer les axes
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, 1.0)  # Ajuster les limites verticales pour bien aligner le texte au-dessus de la barre
        ax.axis('off')

    def plot_visualization(self):
        """Génère une visualisation avec deux lignes et deux colonnes."""
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))

        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        fig = plt.figure(figsize=(16, 16))
        gs = GridSpec(7, 2,  height_ratios=[1,1,1,1,1,1,1])

        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        # Player Info (0,0)
        ax_info = fig.add_subplot(gs[0, 0])
        ax_info.axis('off')


        # Load the player photo
        PlayerProfileScraper(self.player_data['player_name']).save_player_profile()
        image_path = f"data/photo/{self.player_data['player_name'].replace(' ', '_')}_profile_image.jpg"
        player_photo = mpimg.imread(image_path)

        # Display player photo in the (0,0) position
        ax_image = fig.add_subplot(gs[:4, 0])
        ax_image.imshow(player_photo, aspect='equal')  # Ensure the aspect ratio of the image is maintained
        ax_image.set_anchor('W')  # Align the image to the left side
        ax_image.axis('off')  # Hide the axes for the image

        player_info = [
            f"{self.player_data['player_name']}",
            f"{self.player_data['age']} ans",
            f"{self.player_data['club']}",
            f"{self.player_data['nationality']}",
            f"{self.player_data['goals']} But(s)",
            f"{self.player_data['assists']} Passe(s) décisive(s)"
        ]

        y_pos = 0.8
        y_step = 1

        for text in player_info:
            ax_info.text(0.45, y_pos, text, fontsize=17, color='white', transform=ax_info.transAxes, fontweight="bold")
            y_pos -= y_step

        # Offensive Stats (0,1)
        axes_offensive = []
        offensive_stats = [
            ('Key Passes', self.player_data['offensive_stats']['key_passes'], self.player_data['offensive_stats']['total_key_passes']),
            ('Dribbles', self.player_data['offensive_stats']['successful_dribbles'], self.player_data['offensive_stats']['total_dribbles']),
            ('Shots on Target', self.player_data['offensive_stats']['shots_on_target'], self.player_data['offensive_stats']['total_shots']),
            ('Big Chances Created', self.player_data['offensive_stats']['big_chances'], self.player_data['offensive_stats']['total_big_chances'])
        ]

        # Dynamically create axes and add horizontal bars
        for idx, stat in enumerate(offensive_stats):
            row = idx * 2  # Position rows dynamically based on index (e.g., 0, 2, 4, ...)
            ax = fig.add_subplot(gs[row, 1])
            ax.axis('off')
            self._add_horizontal_bar(ax, stat[0], stat[1], stat[2])
            axes_offensive.append(ax)



        ## Defensive Stats (1,0)
        #ax_defensive = fig.add_subplot(gs[1, 0])
        #ax_defensive.axis('off')
#
        #defensive_stats = [
        #    ('Tackles', self.player_data['defensive_stats']['successful_tackles'], self.player_data['defensive_stats']['total_tackles']),
        #    ('Interceptions', self.player_data['defensive_stats']['successful_interceptions'], self.player_data['defensive_stats']['total_interceptions']),
        #    ('Clearances', self.player_data['defensive_stats']['clearances'], self.player_data['defensive_stats']['total_clearances']),
        #    ('Blocks', self.player_data['defensive_stats']['blocks'], self.player_data['defensive_stats']['total_blocks'])
        #]
#
        #for stat in defensive_stats:
        #    self._add_horizontal_bar(ax_defensive, stat[0], stat[1], stat[2])
#
        ## Special Stats (1,1)
        #ax_special = fig.add_subplot(gs[1, 1])
        #ax_special.axis('off')
#
        #special_stats = [
        #    ('Pass Accuracy', self.player_data['special_stats']['accurate_passes'], self.player_data['special_stats']['total_passes']),
        #    ('Aerial Duels Won', self.player_data['special_stats']['aerial_duels_won'], self.player_data['special_stats']['total_aerial_duels']),
        #    ('Fouls Won', self.player_data['special_stats']['fouls_won'], self.player_data['special_stats']['total_fouls']),
        #    ('Crosses Accurate', self.player_data['special_stats']['accurate_crosses'], self.player_data['special_stats']['total_crosses'])
        #]
#
        #for stat in special_stats:
        #    self._add_horizontal_bar(ax_special, stat[0], stat[1], stat[2])

        plt.tight_layout()
        plt.show()

# Charger les données JSON
json_path = "player_data/player_season.json"
with open(json_path, "r", encoding="utf-8") as file:
    raw_data = json.load(file)

# Transformer les données
player_data = {
    "player_name": "Vitinha",
    "age": 23,
    "club": "Paris Saint-Germain",
    "nationality": "Portugal",
    "goals": sum(t["Goals"] for t in raw_data["tournaments"]),
    "assists": sum(t["Assists"] for t in raw_data["tournaments"]),
    "offensive_stats": {
        "key_passes": sum(t["KeyPasses"] for t in raw_data["tournaments"]),
        "total_key_passes": sum(t["TotalPasses"] for t in raw_data["tournaments"]),
        "successful_dribbles": sum(t["Dribbles"] for t in raw_data["tournaments"]),
        "total_dribbles": sum(t["TotalPasses"] for t in raw_data["tournaments"]),
        "shots_on_target": sum(t["ShotsOnTarget"] for t in raw_data["tournaments"]),
        "total_shots": sum(t["TotalShots"] for t in raw_data["tournaments"]),
        "big_chances": sum(t["Assists"] for t in raw_data["tournaments"]),
        "total_big_chances": len(raw_data["tournaments"])
    },
    "defensive_stats": {
        "successful_tackles": sum(t["TotalTackles"] for t in raw_data["tournaments"]),
        "total_tackles": len(raw_data["tournaments"]),
        "successful_interceptions": sum(t["Interceptions"] for t in raw_data["tournaments"]),
        "total_interceptions": len(raw_data["tournaments"]),
        "clearances": sum(t["TotalClearances"] for t in raw_data["tournaments"]),
        "total_clearances": len(raw_data["tournaments"]),
        "blocks": sum(t["ShotsBlocked"] for t in raw_data["tournaments"]),
        "total_blocks": len(raw_data["tournaments"])
    },
    "special_stats": {
        "accurate_passes": sum(t["AccuratePasses"] for t in raw_data["tournaments"]),
        "total_passes": sum(t["TotalPasses"] for t in raw_data["tournaments"]),
        "aerial_duels_won": sum(t["AerialWon"] for t in raw_data["tournaments"]),
        "total_aerial_duels": sum(t["AerialWon"] + t["AerialLost"] for t in raw_data["tournaments"]),
        "fouls_won": sum(t["WasFouled"] for t in raw_data["tournaments"]),
        "total_fouls": sum(t["Fouls"] for t in raw_data["tournaments"]),
        "accurate_crosses": sum(t["AccurateCrosses"] for t in raw_data["tournaments"]),
        "total_crosses": sum(t["TotalCrosses"] for t in raw_data["tournaments"])
    }
}

visualizer = PlayerSeasonVisualizer(player_data)
visualizer.plot_visualization()
