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
from player_visualizer import PlayerVisualizer
from collections import defaultdict, Counter



class SeasonVisualizer(PlayerVisualizer):
    def __init__(self, player_data_path, competition, color1, color2, match_name,match_teams):
        self.player_data_path = player_data_path
        self.player_data = self._load_player_data()

        # Charger les informations passées directement (au lieu d'utiliser MatchDataExtractor)
        self.competition = competition
        self.color1 = color1
        self.color2 = color2
        self.match_name = match_name
        self.match_teams = match_teams

    def _load_player_data(self):
        with open(self.player_data_path, 'r') as file:
            data = json.load(file)
        return data

    def _classify_passes(self, passes):
        forward_passes, lateral_passes, backward_passes = [], [], []
        successful_passes, failed_passes = [], []

        for pas in passes:
            x_start, y_start = pas['x'], pas['y']
            x_end, y_end = pas['endX'], pas['endY']
            
            # Calcul de l'angle
            angle = np.degrees(np.arctan2(y_end - y_start, x_end - x_start))
            # Définir les catégories de passes
            if 30 <= angle <= 150:
                forward_passes.append(pas)
            elif -150 <= angle <= -30:  
                backward_passes.append(pas)
            else:
                lateral_passes.append(pas)
                
            if pas['outcomeType']['displayName'] == 'Successful':
                successful_passes.append(pas)
            else:
                failed_passes.append(pas)

        return forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes


    def _get_dominant_position(self, position_data):
        """
        Extrait la position dominante d'un joueur depuis les données de position

        Args:
            position_data: peut être un dict {position: nombre_matchs} ou une string

        Returns:
            string: la position avec le plus grand nombre de matchs joués
        """
        if isinstance(position_data, dict):
            if not position_data:
                return 'Unknown'
            # Retourner la position avec la plus grande valeur (nombre de matchs)
            dominant_position = max(position_data, key=position_data.get)
            return dominant_position
        elif isinstance(position_data, str):
            return position_data
        else:
            return 'Unknown'

    def plot_passes_heatmap_and_bar_charts(self, save_path, type_data, nb_passe_d): #type_data = DEF,MIL,ATT
        
        total_matches = sum(self.player_data["position"].values())
            
        events = self.player_data.get('events', [])
        passes = [event for event in events if event['type']['displayName'] == 'Pass']

        # Détection des passes décisives (IntentionalGoalAssist ou BigChanceCreated)
        assists = [
            event for event in passes if any(
                q['type']['displayName'] in ['IntentionalGoalAssist', 'BigChanceCreated']
                for q in event.get('qualifiers', [])
            )
        ]
        #nb_passe_d = len(assists)

        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        total_passes = len(passes)

        # Filtrage des événements offensifs
        offensive_events = [
            event for event in events if event['type']['displayName'] in ['TakeOn', 'MissedShots', 'SavedShot', 'Goal', 'Foul', 'Pass']
        ]

        # Compter les événements offensifs par type
        takeons = [event for event in offensive_events if event['type']['displayName'] == 'TakeOn']
        successful_takeons = [event for event in takeons if event.get('outcomeType', {}).get('displayName') == 'Successful']

        missed_shots = [event for event in offensive_events if event['type']['displayName'] == 'MissedShots']
        saved_shots = [event for event in offensive_events if event['type']['displayName'] == 'SavedShot']
        goals = [event for event in offensive_events if event['type']['displayName'] == 'Goal']

        # Filtrage des événements défensifs
        defensive_events = [
            event for event in events if event['type']['displayName'] in ['BallRecovery', 'Interception', 'Tackle', 'Foul']
        ]

        # Compter les événements défensifs par type
        ball_recoveries = [event for event in defensive_events if event['type']['displayName'] == 'BallRecovery']
        successful_ball_recoveries = [event for event in ball_recoveries if event.get('outcomeType', {}).get('displayName') == 'Successful']

        interceptions = [event for event in defensive_events if event['type']['displayName'] == 'Interception']
        successful_interceptions = [event for event in interceptions if event.get('outcomeType', {}).get('displayName') == 'Successful']

        tackles = [event for event in defensive_events if event['type']['displayName'] == 'Tackle']
        successful_tackles = [event for event in tackles if event.get('outcomeType', {}).get('displayName') == 'Successful']

        fouls = [event for event in defensive_events if event['type']['displayName'] == 'Foul']
        committed_fouls = [event for event in fouls if event.get('outcomeType', {}).get('displayName') == 'Unsuccessful']
        submitted_fouls = [event for event in fouls if event.get('outcomeType', {}).get('displayName') == 'Successful']

        # Filtrer les passes clés (KeyPass)
        key_passes = [
            event for event in offensive_events if event['type']['displayName'] == 'Pass' and
            any(q['type']['displayName'] == 'KeyPass' for q in event.get('qualifiers', []))
        ]

        # Filtrer les passes clés réussies
        key_passes_successful = [
            event for event in key_passes if event.get('outcomeType', {}).get('displayName') == 'Successful'
        ]
    
        # Créer un gradient vertical (de haut en bas)
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))

        # Créer un colormap personnalisé à partir des couleurs hexadécimales
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        # Créer une figure
        fig = plt.figure(figsize=(16, 16))

        # Ajouter un axe qui occupe toute la figure
        ax = fig.add_axes([0, 0, 1, 1])

        # Désactiver les axes
        ax.axis('off')

        # Appliquer le gradient vertical avec les couleurs choisies
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        # Creating a grid to place data visualizations on the first line and pitches on the second line
        gs = GridSpec(7, 2,  height_ratios=[1,1,1,1,4,4,4])

        # Load the player photo
        PlayerProfileScraper(self.player_data['player_name']).save_player_profile()
        image_path = f"data/photo/{self.player_data['player_name'].replace(' ', '_')}_profile_image.jpg"
        player_photo = mpimg.imread(image_path)

        # Display player photo in the (0,0) position
        ax_image = fig.add_subplot(gs[:4, 0])
        ax_image.imshow(player_photo, aspect='equal')  # Ensure the aspect ratio of the image is maintained
        ax_image.set_anchor('W')  # Align the image to the left side
        ax_image.axis('off')  # Hide the axes for the image

        # Initial Y position for the first text line
        y_position = 0.96
        y_step = 0.03  # Step between text lines

        # List of text items to display
        text_items = [
            f"{self.player_data['player_name']}",
            f"{self.player_data['age']} ans - {self.player_data['height']}cm",
            f"{self.match_teams}",
            f"{len(goals)} but(s)" if len(goals) >= 1 else None,
            f"{nb_passe_d} passe(s) décisive(s)" if nb_passe_d >= 1 else None,
            f"{total_matches} match(s) joué(s)",
        ]

        # Loop through text items and display them if they are not None
        for text in text_items:
            if text:  # Only display non-None items
                # Check if the text is match_teams to apply a different fontsize
                if text == self.match_teams:
                    ax.text(0.23, y_position, text, fontsize=16, color='white', fontweight='bold', ha='left', transform=ax.transAxes)
                else:
                    ax.text(0.23, y_position, text, fontsize=19, color='white', fontweight='bold', ha='left', transform=ax.transAxes)

                y_position -= y_step  # Update the Y position for the next line


        # Display your tag or source at a fixed position
        ax.text(0.425, 0.72, f"@TarbouchData", fontsize=20, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        # Horizontal bars for forward, lateral, and backward passes
        ax_bar1 = fig.add_subplot(gs[0, 1])
        ax_bar2 = fig.add_subplot(gs[1, 1])
        ax_bar3 = fig.add_subplot(gs[2, 1])
        ax_bar4 = fig.add_subplot(gs[3, 1])

        # Liste des statistiques avec leur ordre de priorité
        all_stats = [
            ("Passes clés", len(key_passes_successful), len(key_passes)),
            ('Récuperations', len(successful_ball_recoveries), len(ball_recoveries)),
            ('Tacles réussis', len(successful_tackles), len(tackles)),
            ('Interceptions', len(successful_interceptions), len(interceptions)),
            ('Passes réussies', len(successful_passes), total_passes),
            ('Dribbles', len(successful_takeons), len(takeons)),
            ('Tirs cadrés', len(saved_shots) + len(goals), len(missed_shots) + len(saved_shots) + len(goals)),
            ('Fautes commises', len(committed_fouls), len(committed_fouls)),
            ('Fautes subies', len(submitted_fouls), len(submitted_fouls))
        ]

        # Priorités par type de joueur
        priorities = {
            'DEF': ['Dribbles', 'Interceptions', 'Passes clés', 'Récuperations'],
            'MIL': ['Dribbles', 'Interceptions', 'Passes clés', 'Récuperations'],
            'ATT': ['Dribbles', 'Interceptions', 'Passes clés', 'Récuperations'],
        }

        # Récupère la liste des priorités pour le type de joueur
        priority_stats = priorities.get(type_data, [])

        # Statistiques classées par priorité
        selected_stats = []

        # 1. D'abord, on sélectionne les stats dans l'ordre de priorité pour les stats non nulles
        for priority in priority_stats:
            for stat in all_stats:
                label, value, total = stat
                if label == priority and value > 0:  # Si la stat correspond à la priorité et qu'elle n'est pas à 0
                    selected_stats.append(stat)
                    break
                
        # 2. Si on n'a pas 4 statistiques, on complète avec des stats ayant la plus grande "total value" 
        # tout en évitant les priorités déjà sélectionnées (y compris celles avec une valeur nulle).
        if len(selected_stats) < 4:
            # Statistiques non prioritaires mais avec des valeurs non nulles
            remaining_stats = [stat for stat in all_stats if stat not in selected_stats]

            # Classement des statistiques restantes par le total (pour avoir les plus grandes totales en premier)
            remaining_stats = sorted(remaining_stats, key=lambda x: x[2], reverse=True)

            # Ajouter ces stats jusqu'à atteindre 4
            for stat in remaining_stats:
                if len(selected_stats) >= 4:
                    break
                label, value, total = stat
                selected_stats.append(stat)

        # 3. Filtrer les statistiques selon les priorités
        non_zero_stats = [stat for stat in all_stats if stat[1] > 0]  # Statistiques avec value > 0
        zero_value_non_zero_total_stats = [stat for stat in all_stats if stat[1] == 0 and stat[2] > 0]  # Statistiques avec value == 0 mais total > 0
        zero_stats = [stat for stat in all_stats if stat[1] == 0 and stat[2] == 0]  # Statistiques avec value == 0 et total == 0

        # Complète avec des stats où value == 0 mais total > 0, si nécessaire
        if len(selected_stats) < 4:
            selected_stats += zero_value_non_zero_total_stats[:4 - len(selected_stats)]

        # Complète avec des stats totalement nulles si nécessaire
        if len(selected_stats) < 4:
            selected_stats += zero_stats[:4 - len(selected_stats)]

        # Affichage des 4 stats selon l'ordre de priorité
        ax_bars = [ax_bar1, ax_bar2, ax_bar3, ax_bar4]  # Liste des axes pour afficher les barres
        for i in range(4):
            label, value, total = selected_stats[i]
            self._add_horizontal_bar(ax_bars[i], label, value, total)


        pitch = Pitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[4:, :])  # Étend sur les 2 colonnes
        pitch.draw(ax=ax_pitch)
        
        # Ajouter une flèche pour le sens du jeu
        ax_pitch.annotate('', xy=(0.75, 0.01), xytext=(0.25, 0.01), xycoords='axes fraction',
                          arrowprops=dict(edgecolor='white', facecolor='none', width=10, headwidth=25, headlength=25))

        # 1. HEATMAP COMBINÉE (tous les events)
        ######touchs = [event for event in events]
        ######x_coords = [t['x'] for t in touchs]
        ######y_coords = [t['y'] for t in touchs]
######
        ####### Bin + smooth
        ######bin_stat = pitch.bin_statistic(x_coords, y_coords, statistic='count', bins=(20, 20))
        ######bin_stat['statistic'] = gaussian_filter(bin_stat['statistic'], 1)
######
        ####### Colormap custom avec transparence
        ######heatmap_cmap = mcolors.LinearSegmentedColormap.from_list(
        ######    "Transparent-Orange-Red",
        ######    [(1, 1, 1, 0), (1, 0.65, 0, 1), (1, 0, 0, 1)],
        ######    N=10
        ######)
        ######pitch.heatmap(bin_stat, ax=ax_pitch, cmap=heatmap_cmap)

        # Parcours des événements offensifs
        for event in offensive_events:
            x, y = event['x'], event['y']
            event_type = event['type']['displayName']
            outcome = event['outcomeType']['displayName']
            
            if outcome == "Successful":
                color = '#6DF176'
    
                if event_type == 'TakeOn':
                    # Carré pour les dribbles
                    marker = 's'
                    pitch.scatter(x, y, s=250, marker=marker, color="#78ff00", edgecolor='white', linewidth=2, ax=ax_pitch)

                elif event_type == 'Goal':
                    # Ronds pour les tirs et les buts
                    marker = 'o'

                    # Ajouter le point de tir
                    pitch.scatter(x, y, s=250, marker=marker, color="#78ff00", edgecolor='white', linewidth=2, ax=ax_pitch)

                    # Trajectoire du tir avec une flèche
                    goalmouth_y = next((float(q['value']) for q in event['qualifiers'] if q['type']['displayName'] == 'GoalMouthY'), None)

                    if goalmouth_y is not None:
                        end_x = 100  # Les tirs se terminent à la ligne de but
                        end_y = (goalmouth_y / 100) * pitch.dim.pitch_length
                        pitch.arrows(x, y, end_x, end_y, width=2, headwidth=3, headlength=3, color="#78ff00", ax=ax_pitch)


        for event in defensive_events:
            x, y = event['x'], event['y']
            event_type = event['type']['displayName']
            outcome = event['outcomeType']['displayName']
            
            if outcome == "Successful":
                color = '#6DF176'

                if event_type == 'Interception':
                    marker = '*'
                    color = '#ff0000'
                    if outcome == 'Successful':
                        pitch.scatter(x, y, s=250, marker=marker, color=color, edgecolor='white', linewidth=2, ax=ax_pitch)
                        
                elif event_type == 'BallRecovery':
                    marker = '^'
                    color = '#ffa900'
                    if outcome == 'Successful':
                        pitch.scatter(x, y, s=250, marker=marker, color=color, edgecolor='white', linewidth=2, ax=ax_pitch)

        # Affichage des passes clés en vert
        for pass_event in key_passes_successful:
            x_start, y_start = pass_event['x'], pass_event['y']
            x_end = next((float(q['value']) for q in pass_event['qualifiers'] if q['type']['displayName'] == 'PassEndX'), None)
            y_end = next((float(q['value']) for q in pass_event['qualifiers'] if q['type']['displayName'] == 'PassEndY'), None)
    
            if x_end is not None and y_end is not None:
                pitch.arrows(x_start, y_start, x_end, y_end, width=2, headwidth=3, headlength=3, color='#fff600', ax=ax_pitch, alpha=0.5)
                

        # Création de la légende sur une seule ligne
        legend_handles = [
            plt.Line2D([0], [0], marker='s', color='black', label='Dribble', markerfacecolor='#78ff00', markersize=15, linestyle='None'),
            plt.Line2D([0], [0], marker='o', color='black', label='But', markerfacecolor='#78ff00', markersize=15, linestyle='None'),
            plt.Line2D([0], [0], marker='*', color='black', label='Interception', markerfacecolor='#ff0000', markersize=15, linestyle='None'),
            plt.Line2D([0], [0], marker='^', color='black', label='Récuperation', markerfacecolor='#ffa900', markersize=15, linestyle='None'),
            plt.Line2D([0], [0], color='#fff600', lw=4, label='Passe clé')
        ]

        # Affichage horizontal de la légende
        ax_pitch.legend(
            handles=legend_handles,
            loc='upper center',
            bbox_to_anchor=(0.5, 0.96),  # Centré juste au-dessus du terrain
            ncol=len(legend_handles),   # Tout sur une ligne
            fontsize=12,
        )

                
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.show()
        
        
    def hate_plot_passes_heatmap_and_bar_charts(self, save_path, type_data, nb_passe_d): #type_data = DEF,MIL,ATT
            
        total_matches = sum(self.player_data["position"].values())
        
        events = self.player_data.get('events', [])
        passes = [event for event in events if event['type']['displayName'] == 'Pass']

        # Détection des passes décisives (IntentionalGoalAssist ou BigChanceCreated)
        assists = [
            event for event in passes if any(
                q['type']['displayName'] in ['IntentionalGoalAssist', 'BigChanceCreated']
                for q in event.get('qualifiers', [])
            )
        ]
        #nb_passe_d = len(assists)

        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        total_passes = len(passes)

        # Filtrage des événements offensifs
        offensive_events = [
            event for event in events if event['type']['displayName'] in ['TakeOn', 'MissedShots', 'SavedShot', 'Goal', 'Foul', 'Pass']
        ]

        # Compter les événements offensifs par type
        takeons = [event for event in offensive_events if event['type']['displayName'] == 'TakeOn']
        successful_takeons = [event for event in takeons if event.get('outcomeType', {}).get('displayName') == 'Unsuccessful']

        missed_shots = [event for event in offensive_events if event['type']['displayName'] == 'MissedShots']
        saved_shots = [event for event in offensive_events if event['type']['displayName'] == 'SavedShot']
        goals = [event for event in offensive_events if event['type']['displayName'] == 'Goal']

        # Filtrage des événements défensifs
        defensive_events = [
            event for event in events if event['type']['displayName'] in ['BallRecovery', 'Interception', 'Tackle', 'Foul']
        ]

        # Compter les événements défensifs par type
        ball_recoveries = [event for event in defensive_events if event['type']['displayName'] == 'BallRecovery']
        successful_ball_recoveries = [event for event in ball_recoveries if event.get('outcomeType', {}).get('displayName') == 'Unsuccessful']

        interceptions = [event for event in defensive_events if event['type']['displayName'] == 'Interception']
        successful_interceptions = [event for event in interceptions if event.get('outcomeType', {}).get('displayName') == 'Unsuccessful']

        tackles = [event for event in defensive_events if event['type']['displayName'] == 'Tackle']
        successful_tackles = [event for event in tackles if event.get('outcomeType', {}).get('displayName') == 'Unsuccessful']

        fouls = [event for event in defensive_events if event['type']['displayName'] == 'Foul']
        committed_fouls = [event for event in fouls if event.get('outcomeType', {}).get('displayName') == 'Unsuccessful']
        submitted_fouls = [event for event in fouls if event.get('outcomeType', {}).get('displayName') == 'Unsuccessful']

        # Filtrer les passes clés (KeyPass)
        key_passes = [
            event for event in offensive_events if event['type']['displayName'] == 'Pass' and
            any(q['type']['displayName'] == 'KeyPass' for q in event.get('qualifiers', []))
        ]

        # Filtrer les passes clés réussies
        key_passes_successful = [
            event for event in key_passes if event.get('outcomeType', {}).get('displayName') == 'Unsuccessful'
        ]
    
        # Créer un gradient vertical (de haut en bas)
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))

        # Créer un colormap personnalisé à partir des couleurs hexadécimales
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        # Créer une figure
        fig = plt.figure(figsize=(16, 16))

        # Ajouter un axe qui occupe toute la figure
        ax = fig.add_axes([0, 0, 1, 1])

        # Désactiver les axes
        ax.axis('off')

        # Appliquer le gradient vertical avec les couleurs choisies
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        # Creating a grid to place data visualizations on the first line and pitches on the second line
        gs = GridSpec(7, 2,  height_ratios=[1,1,1,1,4,4,4])

        # Load the player photo
        PlayerProfileScraper(self.player_data['player_name']).save_player_profile()
        image_path = f"data/photo/{self.player_data['player_name'].replace(' ', '_')}_profile_image.jpg"
        player_photo = mpimg.imread(image_path)

        # Display player photo in the (0,0) position
        ax_image = fig.add_subplot(gs[:4, 0])
        ax_image.imshow(player_photo, aspect='equal')  # Ensure the aspect ratio of the image is maintained
        ax_image.set_anchor('W')  # Align the image to the left side
        ax_image.axis('off')  # Hide the axes for the image

        # Initial Y position for the first text line
        y_position = 0.96
        y_step = 0.03  # Step between text lines

        # List of text items to display
        text_items = [
            f"{self.player_data['player_name']}",
            f"{self.player_data['age']} ans - {self.player_data['height']}cm",
            f"{self.match_teams}",
            f"{len(goals)} but(s)" if len(goals) >= 1 else None,
            f"{nb_passe_d} passe(s) décisive(s)" if nb_passe_d >= 1 else None,
            f"{total_matches} match(s) joué(s)",
            
        ]

        # Loop through text items and display them if they are not None
        for text in text_items:
            if text:  # Only display non-None items
                # Check if the text is match_teams to apply a different fontsize
                if text == self.match_teams:
                    ax.text(0.23, y_position, text, fontsize=16, color='white', fontweight='bold', ha='left', transform=ax.transAxes)
                else:
                    ax.text(0.23, y_position, text, fontsize=19, color='white', fontweight='bold', ha='left', transform=ax.transAxes)

                y_position -= y_step  # Update the Y position for the next line


        # Display your tag or source at a fixed position
        ax.text(0.425, 0.72, f"@TarbouchData", fontsize=20, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        # Horizontal bars for forward, lateral, and backward passes
        ax_bar1 = fig.add_subplot(gs[0, 1])
        ax_bar2 = fig.add_subplot(gs[1, 1])
        ax_bar3 = fig.add_subplot(gs[2, 1])
        ax_bar4 = fig.add_subplot(gs[3, 1])

        # Liste des statistiques avec leur ordre de priorité
        all_stats = [
            ("Passes clés", len(key_passes_successful), len(key_passes)),
            ('Récuperations', len(successful_ball_recoveries), len(ball_recoveries)),
            ('Tacles ratés', len(successful_tackles), len(tackles)),
            ('Interceptions', len(successful_interceptions), len(interceptions)),
            ('Passes réussies', len(successful_passes), total_passes),
            ('Dribbles ratés', len(successful_takeons), len(takeons)),
            ('Tirs hors cadre', len(missed_shots), len(missed_shots) + len(saved_shots) + len(goals)),
            ('Fautes commises', len(committed_fouls), len(committed_fouls)),
            ('Fautes subies', len(submitted_fouls), len(submitted_fouls))
        ]

        # Priorités par type de joueur
        priorities = {
            'DEF': ['Dribbles ratés', 'Tirs hors cadre', 'Fautes commises', 'Tacles ratés'],
            'MIL': ['Dribbles ratés', 'Tirs hors cadre', 'Fautes commises', 'Tacles ratés'],
            'ATT': ['Dribbles ratés', 'Tirs hors cadre', 'Fautes commises', 'Tacles ratés'],
        }

        # Récupère la liste des priorités pour le type de joueur
        priority_stats = priorities.get(type_data, [])

        # Statistiques classées par priorité
        selected_stats = []

        # 1. D'abord, on sélectionne les stats dans l'ordre de priorité pour les stats non nulles
        for priority in priority_stats:
            for stat in all_stats:
                label, value, total = stat
                if label == priority and value > 0:  # Si la stat correspond à la priorité et qu'elle n'est pas à 0
                    selected_stats.append(stat)
                    break
                
        # 2. Si on n'a pas 4 statistiques, on complète avec des stats ayant la plus grande "total value" 
        # tout en évitant les priorités déjà sélectionnées (y compris celles avec une valeur nulle).
        if len(selected_stats) < 4:
            # Statistiques non prioritaires mais avec des valeurs non nulles
            remaining_stats = [stat for stat in all_stats if stat not in selected_stats]

            # Classement des statistiques restantes par le total (pour avoir les plus grandes totales en premier)
            remaining_stats = sorted(remaining_stats, key=lambda x: x[2], reverse=True)

            # Ajouter ces stats jusqu'à atteindre 4
            for stat in remaining_stats:
                if len(selected_stats) >= 4:
                    break
                label, value, total = stat
                selected_stats.append(stat)

        # 3. Filtrer les statistiques selon les priorités
        non_zero_stats = [stat for stat in all_stats if stat[1] > 0]  # Statistiques avec value > 0
        zero_value_non_zero_total_stats = [stat for stat in all_stats if stat[1] == 0 and stat[2] > 0]  # Statistiques avec value == 0 mais total > 0
        zero_stats = [stat for stat in all_stats if stat[1] == 0 and stat[2] == 0]  # Statistiques avec value == 0 et total == 0

        # Complète avec des stats où value == 0 mais total > 0, si nécessaire
        if len(selected_stats) < 4:
            selected_stats += zero_value_non_zero_total_stats[:4 - len(selected_stats)]

        # Complète avec des stats totalement nulles si nécessaire
        if len(selected_stats) < 4:
            selected_stats += zero_stats[:4 - len(selected_stats)]

        # Affichage des 4 stats selon l'ordre de priorité
        ax_bars = [ax_bar1, ax_bar2, ax_bar3, ax_bar4]  # Liste des axes pour afficher les barres
        for i in range(4):
            label, value, total = selected_stats[i]
            self._add_horizontal_bar(ax_bars[i], label, value, total)


        pitch = Pitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[4:, :])  # Étend sur les 2 colonnes
        pitch.draw(ax=ax_pitch)
        
        # Ajouter une flèche pour le sens du jeu
        ax_pitch.annotate('', xy=(0.75, 0.01), xytext=(0.25, 0.01), xycoords='axes fraction',
                          arrowprops=dict(edgecolor='white', facecolor='none', width=10, headwidth=25, headlength=25))

        # Parcours des événements offensifs
        for event in offensive_events:
            x, y = event['x'], event['y']
            event_type = event['type']['displayName']
            outcome = event['outcomeType']['displayName']
            
            if outcome == "Unsuccessful":
    
                if event_type == 'TakeOn':
                    # Carré pour les dribbles
                    marker = 's'
                    pitch.scatter(x, y, s=250, marker=marker, color="#ffab00", edgecolor='white', linewidth=2, ax=ax_pitch)

            if event_type == 'MissedShots':
                # Ronds pour les tirs et les buts
                marker = 'o'
                # Ajouter le point de tir
                pitch.scatter(x, y, s=250, marker=marker, color="#ff0000", edgecolor='white', linewidth=2, ax=ax_pitch)
                # Trajectoire du tir avec une flèche
                goalmouth_y = next((float(q['value']) for q in event['qualifiers'] if q['type']['displayName'] == 'GoalMouthY'), None)
                if goalmouth_y is not None:
                    end_x = 100  # Les tirs se terminent à la ligne de but
                    end_y = (goalmouth_y / 100) * pitch.dim.pitch_length
                    pitch.arrows(x, y, end_x, end_y, width=2, headwidth=3, headlength=3, color="#ff0000", ax=ax_pitch)


        for event in defensive_events:
            x, y = event['x'], event['y']
            event_type = event['type']['displayName']
            outcome = event['outcomeType']['displayName']
            
            if outcome == "Unsuccessful":
                color = '#6DF176'

                if event_type == 'Foul':
                    marker = '*'
                    color = '#ff0000'
                    if outcome != 'Successful':
                        pitch.scatter(x, y, s=250, marker=marker, color=color, edgecolor='white', linewidth=2, ax=ax_pitch)
                        
                elif event_type == 'Tackle':
                    marker = '^'
                    color = '#ffdc00'
                    if outcome == 'Unsuccessful':
                        pitch.scatter(x, y, s=250, marker=marker, color=color, edgecolor='white', linewidth=2, ax=ax_pitch)
                

        # Création de la légende sur une seule ligne
        legend_handles = [
            plt.Line2D([0], [0], marker='s', color='black', label='Dribble raté', markerfacecolor='#ffab00', markersize=15, linestyle='None'),
            plt.Line2D([0], [0], marker='o', color='black', label='Tir hors cadre', markerfacecolor='#ff0000', markersize=15, linestyle='None'),
            plt.Line2D([0], [0], marker='*', color='black', label='Faute commise', markerfacecolor='#ff0000', markersize=15, linestyle='None'),
            plt.Line2D([0], [0], marker='^', color='black', label='Tacle raté', markerfacecolor='#ffdc00', markersize=15, linestyle='None'),
        ]

        # Affichage horizontal de la légende
        ax_pitch.legend(
            handles=legend_handles,
            loc='upper center',
            bbox_to_anchor=(0.5, 0.96),  # Centré juste au-dessus du terrain
            ncol=len(legend_handles),   # Tout sur une ligne
            fontsize=12,
        )

                
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.show()


    def plot_passes_and_bar_charts(self, save_path):
        events = self.player_data.get('events', [])
        passes = [event for event in events if event['type']['displayName'] == 'Pass']
        
        # Filtrage des événements offensifs
        offensive_events = [
            event for event in events if event['type']['displayName'] in ['TakeOn', 'MissedShots', 'SavedShot', 'Goal', 'Foul', 'Pass']
        ]
    
        if not passes:
            print(f"Pas de passes trouvées pour {self.player_data['player_name']}. Aucun visuel généré.")
            return
    
        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        total_passes = len(passes)

        # Filtrer les passes clés (KeyPass)
        key_passes = [
            event for event in offensive_events if event['type']['displayName'] == 'Pass' and
            any(q['type']['displayName'] == 'KeyPass' for q in event.get('qualifiers', []))
        ]

        # Filtrer les passes clés réussies
        key_passes_successful = [
            event for event in key_passes if event.get('outcomeType', {}).get('displayName') == 'Successful'
        ]
    
        # Créer un gradient vertical (de haut en bas)
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
    
        # Créer un colormap personnalisé à partir des couleurs hexadécimales
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
    
        # Créer une figure
        fig = plt.figure(figsize=(12, 9))
    
        # Ajouter un axe qui occupe toute la figure
        ax = fig.add_axes([0, 0, 1, 1])
    
        # Désactiver les axes
        ax.axis('off')
    
        # Appliquer le gradient vertical avec les couleurs choisies
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
    
        # Creating a grid to place the pitch on the left and visualizations on the right
        gs = GridSpec(6, 2, width_ratios=[2, 2])  # 6 rows, 2 columns (3:1 ratio)
    
        # 1. Plotting the pitch on the left side
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[:, 0])
        pitch.draw(ax=ax_pitch)
    
        ax_pitch.annotate('', xy=(-0.05, 0.75), xytext=(-0.05, 0.25), xycoords='axes fraction',
                          arrowprops=dict(edgecolor='white', facecolor='none', width=10, headwidth=25, headlength=25))

        throughball_count = 0
        other_passes_count = 0

        for pas in successful_passes:
            y_start = pas['x']
            x_start = pas['y']
            y_end = pas['endX']
            x_end = pas['endY']
            alpha_pass = 1

            # Vérifier si le qualifier "Throughball" est présent
            is_throughball = any(q['type']['displayName'] == 'Throughball' for q in pas.get('qualifiers', []))

            # Définir la couleur et l'épaisseur selon le type de passe
            if is_throughball and pas.get('outcomeType', {}).get('displayName') == 'Successful':
                color = '#78ff00'  
                arrow_width = 2
                throughball_count += 1
                            
                pitch.arrows(
                    y_start, x_start, y_end, x_end,
                    width=arrow_width, headwidth=arrow_width * 1.5, headlength=arrow_width * 1.5,
                    color=color, ax=ax_pitch, alpha=alpha_pass )
            
            if is_throughball and pas.get('outcomeType', {}).get('displayName') == 'Unsuccessful':
                color = '#FF0000' 
                arrow_width = 2
                other_passes_count += 1
                
                pitch.arrows(
                    y_start, x_start, y_end, x_end,
                    width=arrow_width, headwidth=arrow_width * 1.5, headlength=arrow_width * 1.5,
                    color=color, ax=ax_pitch, alpha=alpha_pass )

    
        p_1 = mpatches.Patch(color='#78ff00', label='Passes en profondeur réussies')
        p_2 = mpatches.Patch(color='#FF0000', label='Passes en profondeur ratées')
        ax_pitch.legend(handles=[p_1, p_2], loc='upper right', bbox_to_anchor=(1.425, 1), fontsize=12)
        ax_pitch.set_title("@MaData_fr", fontsize=20, color=(1, 1, 1, 0), fontweight='bold', loc='center')

        # Ajoutez cette ligne à la place
        ax.text(0.5, 0.96, f"Passes de {self.player_data['player_name']}", fontsize=20, color='white', fontweight='bold', ha='center', transform=ax.transAxes)

        # Display your tag or source at a fixed position
        ax.text(0.425, 0.77, f"@TarbouchData", fontsize=14, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)


        # 2. Plotting data visualizations on the right side
    
        # Move the semi-circular gauge lower (closer to the first bar plot)
        ax_gauge = fig.add_subplot(gs[1:5, 1], polar=True)  # Now taking up only the third row, right above the bar chart
        self._plot_semi_circular_gauge(ax_gauge, "Taux de passes réussies", len(successful_passes), total_passes)
    

        # 2. Modifier les visualisations en barres
        ax_bar1 = fig.add_subplot(gs[3, 1])
        ax_bar2 = fig.add_subplot(gs[4, 1])

        self._add_horizontal_bar(ax_bar1, 'En profondeur', throughball_count, total_passes)
        self._add_horizontal_bar(ax_bar2, 'Dans les pieds', total_passes-throughball_count, total_passes)

    
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.show()
        
    def plot_crosses_and_bar_charts(self, save_path): ###########################################################################################################################################################
        events = self.player_data.get('events', [])
        passes = [event for event in events if event['type']['displayName'] == 'Pass']
        
        # Filtrage des événements offensifs
        offensive_events = [
            event for event in events if event['type']['displayName'] in ['TakeOn', 'MissedShots', 'SavedShot', 'Goal', 'Foul', 'Pass']
        ]
    
        if not passes:
            print(f"Pas de passes trouvées pour {self.player_data['player_name']}. Aucun visuel généré.")
            return
    
        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        total_passes = len(passes)

        # Filtrer les passes clés (Cross)
        crosses = [
            event for event in passes if event['type']['displayName'] == 'Pass' and
            any(q['type']['displayName'] == 'Cross' for q in event.get('qualifiers', []))
        ]

        # Filtrer les passes clés réussies
        crosses_successful = [
            event for event in crosses if event.get('outcomeType', {}).get('displayName') == 'Successful'
        ]
        
        # Filtrer les passes clés (KeyPass) qui sont aussi des Cross
        key_passes_cross = [
            event for event in offensive_events if event['type']['displayName'] == 'Pass' and
            any(q['type']['displayName'] == 'KeyPass' for q in event.get('qualifiers', [])) and
            any(q['type']['displayName'] == 'Cross' for q in event.get('qualifiers', []))
        ]

        # Filtrer les passes clés réussies qui sont aussi des Cross
        key_passes_cross_successful = [
            event for event in key_passes_cross if event.get('outcomeType', {}).get('displayName') == 'Successful'
        ]
    
        # Créer un gradient vertical (de haut en bas)
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
    
        # Créer un colormap personnalisé à partir des couleurs hexadécimales
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
    
        # Créer une figure
        fig = plt.figure(figsize=(12, 9))
    
        # Ajouter un axe qui occupe toute la figure
        ax = fig.add_axes([0, 0, 1, 1])
    
        # Désactiver les axes
        ax.axis('off')
    
        # Appliquer le gradient vertical avec les couleurs choisies
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
    
        # Creating a grid to place the pitch on the left and visualizations on the right
        gs = GridSpec(6, 2, width_ratios=[2, 2])  # 6 rows, 2 columns (3:1 ratio)
    
        # 1. Plotting the pitch on the left side
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[:, 0])
        pitch.draw(ax=ax_pitch)
    
        ax_pitch.annotate('', xy=(-0.05, 0.75), xytext=(-0.05, 0.25), xycoords='axes fraction',
                          arrowprops=dict(edgecolor='white', facecolor='none', width=10, headwidth=25, headlength=25))

        key_passes_count = 0  # Compteur pour les passes clés
        other_passes_count = 0  # Compteur pour les passes échouées (non clés)

        for pas in crosses:
            y_start = pas['x']
            x_start = pas['y']
            y_end = pas['endX']
            x_end = pas['endY']

            if pas.get('outcomeType', {}).get('displayName') == 'Unsuccessful':
                color = '#FF0000'  # Rouge pour les centres ratés
                arrow_width = 2
                other_passes_count += 1
                pitch.arrows(
                    y_start, x_start, y_end, x_end,
                    width=arrow_width, headwidth=arrow_width * 1.5, headlength=arrow_width * 1.5,
                    color=color, ax=ax_pitch, alpha=0.5
                )

            elif pas.get('outcomeType', {}).get('displayName') == 'Successful':
                color = '#78ff00'  # Vert pour les centres réussis
                arrow_width = 2
                pitch.arrows(
                    y_start, x_start, y_end, x_end,
                    width=arrow_width, headwidth=arrow_width * 1.5, headlength=arrow_width * 1.5,
                    color=color, ax=ax_pitch, alpha=1
                )


        # Ajouter la légende
        p_1 = mpatches.Patch(color='#78ff00', label='Centre réussi')
        p_2 = mpatches.Patch(color='#FF0000', label='Centre raté')
        ax_pitch.legend(handles=[p_1, p_2], loc='upper right', bbox_to_anchor=(1.425, 1), fontsize=12)
        ax_pitch.set_title("@MaData_fr", fontsize=20, color=(1, 1, 1, 0), fontweight='bold', loc='center')


        # Ajoutez cette ligne à la place
        ax.text(0.5, 0.96, f"Centres de {self.player_data['player_name']}", fontsize=20, color='white', fontweight='bold', ha='center', transform=ax.transAxes)

        # Display your tag or source at a fixed position
        ax.text(0.425, 0.77, f"@TarbouchData", fontsize=14, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)


        # 2. Plotting data visualizations on the right side
    
        # Move the semi-circular gauge lower (closer to the first bar plot)
        ax_gauge = fig.add_subplot(gs[1:5, 1], polar=True)  # Now taking up only the third row, right above the bar chart
        self._plot_semi_circular_gauge(ax_gauge, "Taux de centres réussies", len(crosses_successful), len(crosses))
    

        # 2. Modifier les visualisations en barres
        ax_bar1 = fig.add_subplot(gs[3, 1])
        ax_bar2 = fig.add_subplot(gs[4, 1])

        self._add_horizontal_bar(ax_bar1, 'Centres réussis', len(crosses_successful), len(crosses))
        self._add_horizontal_bar(ax_bar2, 'Centres clés', len(key_passes_cross_successful), len(crosses))

    
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.show()


    def _plot_semi_circular_gauge(self, ax, label, successful_passes, total_passes):
        ax.set_facecolor('none')  # Background color for the gauge
        if total_passes == 0:
            total_passes = 0.001
        percentage = successful_passes / total_passes

        # Create the angle for the semi-circle (from pi to 0 for right-to-left)
        theta = np.linspace(np.pi, 0, 100)

        # Create a color map from red to custom green (#6DF176)
        cmap = mcolors.LinearSegmentedColormap.from_list('orange', ['orange', '#6DF176'])

        # Get the interpolated color based on the percentage (0 is red, 1 is #6DF176)
        color = cmap(percentage)

        # Plot the full background arc (gray, representing 100%)
        ax.plot(theta, np.ones_like(theta) * 10, lw=80, color='#505050', solid_capstyle='butt')

        # Plot only the arc showing successful passes with interpolated color
        end_theta_index = int(percentage * len(theta))
        ax.plot(theta[:end_theta_index], np.ones_like(theta)[:end_theta_index] * 10, 
                lw=80, color=color, solid_capstyle='butt')

        # Add the percentage value in the center of the gauge
        ax.text(0, 0, f'{int(percentage * 100)}%', ha='center', va='center', fontsize=35, 
                color=color, fontweight='bold')

        # Remove any axis labels, ticks, or spines
        ax.set_ylim(0, 10)
        ax.set_yticks([])  # Remove y-ticks
        ax.set_xticks([])  # Remove x-ticks
        ax.spines['polar'].set_visible(False)  # Hide the polar spines (borders)

        # Add a title above the gauge
        ax.set_title(label, fontsize=20, color="white", fontweight='bold', pad=20)

    def _add_horizontal_bar(self, ax, label, value, max_value):
        bar_height = 0.2
        filled_length = 0

        if max_value != 0:
            filled_length = value / max_value

        # Vérifier si la barre concerne les fautes commises
        if label in ['Dribbles ratés', 'Tirs hors cadre', 'Fautes commises', 'Tacles ratés']:
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

    def plot_defensive_activity(self, save_path):
        events = self.player_data.get('events', [])

        # Filtrage des événements défensifs
        defensive_events = [
            event for event in events if event['type']['displayName'] in ['BallRecovery', 'Interception', 'Tackle', 'Foul']
        ]

        if not defensive_events:
            print(f"Aucune activité défensive trouvée pour {self.player_data['player_name']}. Aucun visuel généré.")
            return

        # Compter les événements défensifs par type
        ball_recoveries = [event for event in defensive_events if event['type']['displayName'] == 'BallRecovery']
        successful_ball_recoveries = [event for event in ball_recoveries if event.get('outcomeType', {}).get('displayName') == 'Successful']

        interceptions = [event for event in defensive_events if event['type']['displayName'] == 'Interception']
        successful_interceptions = [event for event in interceptions if event.get('outcomeType', {}).get('displayName') == 'Successful']

        tackles = [event for event in defensive_events if event['type']['displayName'] == 'Tackle']
        successful_tackles = [event for event in tackles if event.get('outcomeType', {}).get('displayName') == 'Successful']

        fouls = [event for event in defensive_events if event['type']['displayName'] == 'Foul']
        committed_fouls = [event for event in fouls if event.get('outcomeType', {}).get('displayName') == 'Successful']

        passes = [event for event in events if event['type']['displayName'] == 'Pass']

        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        total_passes = len(passes)

        total_events = len(defensive_events)

        # Définir les symboles et couleurs
        symbol_map = {
            'BallRecovery': 'o',  # Rond
            'Interception': 's',     # Carré
            'Tackle': '^',        # Triangle
            'Foul': '*'           # Étoile
        }
        color_map = {
            'Successful': '#6DF176',
            'Unsuccessful': 'red'
        }

        # Créer un gradient vertical (de haut en bas)
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))

        # Créer un colormap personnalisé à partir des couleurs hexadécimales
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        # Créer une figure
        fig = plt.figure(figsize=(12, 9))

        # Ajouter un axe qui occupe toute la figure
        ax = fig.add_axes([0, 0, 1, 1])

        # Désactiver les axes
        ax.axis('off')

        # Appliquer le gradient vertical avec les couleurs choisies
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        # Création d'une grille pour placer le terrain à gauche et les visualisations à droite
        gs = GridSpec(6, 2, width_ratios=[2, 2])  # 6 rangées, 2 colonnes (rapport 3:1)

        # 1. Tracé du terrain à gauche
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[:, 0])
        pitch.draw(ax=ax_pitch)

        # Ajouter une flèche pour le sens du jeu
        ax_pitch.annotate('', xy=(-0.05, 0.75), xytext=(-0.05, 0.25), xycoords='axes fraction',
                          arrowprops=dict(edgecolor='white', facecolor='none', width=10, headwidth=25, headlength=25))
        
        # Parcours des événements défensifs
        for event in defensive_events:
            x, y = event['x'], event['y']
            event_type = event['type']['displayName']
            outcome = event['outcomeType']['displayName'] if 'outcomeType' in event else 'Successful'  # Assume success if not stated

            marker = symbol_map[event_type]
            
            if outcome == 'Successful' and event_type != 'Foul':
                color = color_map.get(outcome, '#6DF176')
                pitch.scatter(x, y, s=200, marker=marker, color=color, edgecolor='white', linewidth=1.5, ax=ax_pitch)

        # Création de la légende
        legend_handles = [
            plt.Line2D([0], [0], marker='o', color='w', label='Récupération', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='s', color='w', label='Interception', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='^', color='w', label='Tacle', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='*', color='w', label='Faute', markerfacecolor='black', markersize=15),
        ]
        ax_pitch.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1.2925, 1), fontsize=12)
        ax_pitch.set_title("@TarbouchData", fontsize=20, color=(1, 1, 1, 0), fontweight='bold', loc='center')

        # Ajoutez cette ligne à la place
        ax.text(0.5, 0.96, f"Activité défensive de {self.player_data['player_name']}", fontsize=20, color='white', fontweight='bold', ha='center', transform=ax.transAxes)

        # Display your tag or source at a fixed position
        ax.text(0.445, 0.76, f"@TarbouchData", fontsize=14, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        # 2. Visualisation des données sur le côté droit

        # Jauge semi-circulaire pour les récupérations de balle réussies
        ax_gauge = fig.add_subplot(gs[1:5, 1], polar=True)  # Prend la troisième rangée à droite
        self._plot_semi_circular_gauge(ax_gauge, "Taux de passes réussies", len(successful_passes), total_passes)

        # Barres horizontales pour les autres événements défensifs
        ax_bar1 = fig.add_subplot(gs[3, 1])
        ax_bar2 = fig.add_subplot(gs[4, 1])
        ax_bar3 = fig.add_subplot(gs[5, 1])

        # Ajout des barres avec des pourcentages spécifiques à chaque type d'événement
        self._add_horizontal_bar(ax_bar1, 'Interceptions réussies', len(interceptions), len(successful_interceptions))
        self._add_horizontal_bar(ax_bar2, 'Tacles réussis', len(successful_tackles), len(tackles))
        self._add_horizontal_bar(ax_bar3, 'Récupérations réussies', len(successful_ball_recoveries), len(ball_recoveries))

        plt.tight_layout()
        plt.savefig(save_path)
        plt.show()

    def plot_offensive_activity(self, save_path_pitch, save_path_goal):
        events = self.player_data.get('events', [])
    
        # Filtrage des événements offensifs
        offensive_events = [
            event for event in events if event['type']['displayName'] in ['TakeOn', 'MissedShots', 'SavedShot', 'Goal', 'Foul', 'Pass']
        ]
    
        if not offensive_events:
            print(f"Aucune activité offensive trouvée pour {self.player_data['player_name']}. Aucun visuel généré.")
            return
    
        # Filtrer les passes clés (KeyPass)
        key_passes = [
            event for event in offensive_events if event['type']['displayName'] == 'Pass' and
            any(q['type']['displayName'] == 'KeyPass' for q in event.get('qualifiers', []))
        ]

        # Filtrer les passes clés réussies
        key_passes_successful = [
            event for event in key_passes if event.get('outcomeType', {}).get('displayName') == 'Successful'
        ]
    
        # Compter les événements offensifs par type
        takeons = [event for event in offensive_events if event['type']['displayName'] == 'TakeOn']
        successful_takeons = [event for event in takeons if event.get('outcomeType', {}).get('displayName') == 'Successful']
    
        missed_shots = [event for event in offensive_events if event['type']['displayName'] == 'MissedShots']
        saved_shots = [event for event in offensive_events if event['type']['displayName'] == 'SavedShot']
        goals = [event for event in offensive_events if event['type']['displayName'] == 'Goal']
    
        fouls = [event for event in offensive_events if event['type']['displayName'] == 'Foul']
        submitted_fouls = [event for event in fouls if event.get('outcomeType', {}).get('displayName') == 'Successful']

        passes = [event for event in events if event['type']['displayName'] == 'Pass']

        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        total_passes = len(passes)
    
        total_events = len(offensive_events)
    
        # Créer un gradient vertical (de haut en bas)
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
    
        # Créer un colormap personnalisé à partir des couleurs hexadécimales
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
    
        # Créer une figure
        fig = plt.figure(figsize=(12, 9))
    
        # Ajouter un axe qui occupe toute la figure
        ax = fig.add_axes([0, 0, 1, 1])
    
        # Désactiver les axes
        ax.axis('off')
    
        # Appliquer le gradient vertical avec les couleurs choisies
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
    
        # Création d'une grille pour placer le terrain à gauche et les visualisations à droite
        gs = GridSpec(6, 2, width_ratios=[2, 2])  # 6 rangées, 2 colonnes (rapport 3:1)
    
        # 1. Tracé du terrain à gauche
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[:, 0])
        pitch.draw(ax=ax_pitch)
    
        # Ajouter une flèche pour le sens du jeu
        ax_pitch.annotate('', xy=(-0.05, 0.75), xytext=(-0.05, 0.25), xycoords='axes fraction',
                          arrowprops=dict(edgecolor='white', facecolor='none', width=10, headwidth=25, headlength=25))
    
        # Parcours des événements offensifs
        for event in offensive_events:
            x, y = event['x'], event['y']
            event_type = event['type']['displayName']
            outcome = event['outcomeType']['displayName']
            
            if outcome == "Successful":
                color = '#6DF176'
    
                if event_type == 'TakeOn':
                    # Carré pour les dribbles
                    marker = 's'
                    pitch.scatter(x, y, s=200, marker=marker, color=color, edgecolor='white', linewidth=1.5, ax=ax_pitch)

                elif event_type == 'Goal':
                    # Ronds pour les tirs et les buts
                    marker = 'o'

                    # Ajouter le point de tir
                    pitch.scatter(x, y, s=200, marker=marker, color=color, edgecolor='white', linewidth=1.5, ax=ax_pitch)

                    # Trajectoire du tir avec une flèche
                    goalmouth_y = next((float(q['value']) for q in event['qualifiers'] if q['type']['displayName'] == 'GoalMouthY'), None)

                    if goalmouth_y is not None:
                        end_x = 100  # Les tirs se terminent à la ligne de but
                        end_y = (goalmouth_y / 100) * pitch.dim.pitch_length
                        pitch.arrows(x, y, end_x, end_y, width=2, headwidth=3, headlength=3, color=color, ax=ax_pitch)

                elif event_type == 'Foul':
                    # Étoiles pour les fautes subies
                    marker = '*'
                    color = '#6DF176'
                    if outcome == 'Successful':
                        pitch.scatter(x, y, s=200, marker=marker, color=color, edgecolor='white', linewidth=1.5, ax=ax_pitch)
    
        # Affichage des passes clés en vert
        for pass_event in key_passes_successful:
            x_start, y_start = pass_event['x'], pass_event['y']
            x_end = next((float(q['value']) for q in pass_event['qualifiers'] if q['type']['displayName'] == 'PassEndX'), None)
            y_end = next((float(q['value']) for q in pass_event['qualifiers'] if q['type']['displayName'] == 'PassEndY'), None)
    
            if x_end is not None and y_end is not None:
                pitch.arrows(x_start, y_start, x_end, y_end, width=2, headwidth=3, headlength=3, color='#6DF176', ax=ax_pitch)
    
        # Création de la légende
        legend_handles = [
            plt.Line2D([0], [0], marker='s', color='w', label='Dribble', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='o', color='w', label='Tir', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='*', color='w', label='Faute subie', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], color='#6DF176', lw=2, label='Passe clé')
        ]
        ax_pitch.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1.265, 1), fontsize=12)
        ax_pitch.set_title("@MaData_fr", fontsize=20, color=(1, 1, 1, 0), fontweight='bold', loc='center')
    
        # Ajoutez cette ligne à la place
        ax.text(0.5, 0.96, f"Activité offensive de {self.player_data['player_name']}", fontsize=20, color='white', fontweight='bold', ha='center', transform=ax.transAxes)
    
        # Display your tag or source at a fixed position
        ax.text(0.45, 0.76, f"@TarbouchData", fontsize=14, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        # 2. Visualisation des données sur le côté droit
    
        # Jauge semi-circulaire pour les buts
        ax_gauge = fig.add_subplot(gs[1:5, 1], polar=True)
        self._plot_semi_circular_gauge(ax_gauge, "Taux de passes réussies", len(successful_passes), total_passes)
    
        # Barres horizontales pour les dribbles et tirs manqués
        ax_bar1 = fig.add_subplot(gs[3, 1])
        ax_bar2 = fig.add_subplot(gs[4, 1])
        ax_bar3 = fig.add_subplot(gs[5, 1])
    
        # Ajout des barres avec des pourcentages spécifiques à chaque type d'événement
        self._add_horizontal_bar(ax_bar1, 'Dribbles réussis', len(successful_takeons), len(takeons))
        self._add_horizontal_bar(ax_bar2, 'Passes clés', len(key_passes_successful), len(key_passes))      
        self._add_horizontal_bar(ax_bar3, 'Tirs cadrés', len(saved_shots) + len(goals), len(missed_shots) + len(goals) + len(saved_shots))

        plt.tight_layout()
        plt.savefig(save_path_pitch)
        plt.show()

    def plot_shots_heatmap_and_bar_charts(self, save_path, type_data, nb_passe_d):
        """Visualize shots and heatmap for a player's match performance, with bar plots for key stats."""

        events = self.player_data.get('events', [])
        stats = self.player_data.get('stats', {})

        # Stats extracted from the JSON structure
        total_passes = stats.get("totalPass", 0)
        accurate_passes = stats.get("accuratePass", 0)
        shots_off_target = stats.get("shotOffTarget", 0)
        shots_on_target = stats.get("onTargetScoringAttempt", 0)
        goals = stats.get("goals", 0)

        # Additional stats you provided
        total_long_balls = stats.get("totalLongBalls", 0)
        accurate_long_balls = stats.get("accurateLongBalls", 0)
        total_duels = stats.get("duelWon", 0) + stats.get("duelLost", 0)
        duels_won = stats.get("duelWon", 0)
        won_contests = stats.get("wonContest", 0)
        total_contests = stats.get("totalContest", 0)
        total_tackles = stats.get("totalTackle", 0)
        touches = stats.get("touches", 0)
        key_passes = stats.get("keyPass", 0)

        # Visualization setup (using the same layout as before)
        fig = plt.figure(figsize=(16, 16))
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        gs = GridSpec(11, 2, height_ratios=[1, 1, 1, 1, 1, 1, 1, 1, 4, 4, 4])

        # Load and display player photo
        PlayerProfileScraper(self.player_data['player_name']).save_player_profile()
        image_path = f"data/photo/{self.player_data['player_name'].replace(' ', '_')}_profile_image.jpg"
        player_photo = mpimg.imread(image_path)
        ax_image = fig.add_subplot(gs[:4, 0])
        ax_image.imshow(player_photo, aspect='equal')
        ax_image.set_anchor('W')
        ax_image.axis('off')

        # Display player info
        status_text = "Titulaire" if self.player_data["isFirstEleven"] else "Substitute"
        text_items = [
            f"{self.player_data['player_name']}",# - N°{self.player_data['shirtNo']}",
            f"{self.player_data['age']} ans - {self.player_data['height']}cm",
            f"{status_text}",
            f"Temps de jeu: {stats['minutesPlayed']} minutes",
            f"{goals} but(s)" if goals >= 1 else "",
            f"{nb_passe_d} passe(s) décisive(s)" if nb_passe_d >= 1 else "",
            f"Man of the Match" if self.player_data['isManOfTheMatch'] else ""
        ]

        y_position = 0.96
        y_step = 0.03
        for text in text_items:
            if text:
                ax.text(0.2, y_position, text, fontsize=20, color='white', fontweight='bold', ha='left', transform=ax.transAxes)
                y_position -= y_step

        # Horizontal bars for the stats
        ax_bar1 = fig.add_subplot(gs[4, 0])
        ax_bar2 = fig.add_subplot(gs[5, 0])
        ax_bar3 = fig.add_subplot(gs[6, 0])
        ax_bar4 = fig.add_subplot(gs[7, 0])

        # Select key stats for display based on player type (DEF, MIL, ATT)
        all_stats = [
            ('Passes réussies', accurate_passes, total_passes),
            ('Tirs cadrés', shots_on_target, shots_on_target + shots_off_target),
            ('But(s)', goals, goals),  # Goals stats
            ('Possession perdue', stats.get("possessionLostCtrl", 0), stats.get("possessionLostCtrl", 0)),
            ('Longs ballons réussis', accurate_long_balls, total_long_balls),  # Long ball stats
            ('Duels gagnés', duels_won, total_duels),  # Duels won stats
            ('Dribbles réussis', won_contests, total_contests),  # Contests won stats
            ('Tacles', total_tackles, total_tackles),  # Tackles stats
            ('Touches de balle', touches, touches),  # Touches stats
            ('Passes clés', key_passes, key_passes),  # Key passes stats
        ]

        # Update priorities based on player type (DEF, MIL, ATT)
        priorities = {
            'DEF': ['Passes réussies', 'Tacles', 'Duels gagnés', 'Long balls réussis'],
            'MIL': ['Passes réussies', 'Dribbles réussis', 'Duels gagnés', 'Passes clés'],
            'ATT': ['Tirs cadrés', 'But(s)', 'Passes clés', 'Dribbles réussis']
        }

        # Select stats based on the player's type
        selected_stats = []
        priority_stats = priorities.get(type_data, [])
        for priority in priority_stats:
            for stat in all_stats:
                label, value, total = stat
                if label == priority and value > 0:
                    selected_stats.append(stat)
                    break
                
        # Ensure we have at least 4 stats to display
        for stat in all_stats:
            if len(selected_stats) >= 4:
                break
            if stat not in selected_stats and stat[1] > 0:
                selected_stats.append(stat)

        # Plot the selected stats in horizontal bars
        ax_bars = [ax_bar1, ax_bar2, ax_bar3, ax_bar4]
        for i in range(4):
            label, value, total = selected_stats[i]
            self._add_horizontal_bar(ax_bars[i], label, value, total)


        # Plot the pitch and shots visualization
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        pitch_2 = VerticalPitch(half=True, pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch_left = fig.add_subplot(gs[6:, 0], aspect=1)
        pitch_2.draw(ax=ax_pitch_left)

        # Plotting shots and goals with a point and an arrow for direction
        for event in events:
            if event['type']['displayName'] in ['Shot', 'Goal']:
                x = 100 - event['x']  # Start position of the shot
                y = 100 - event['y']  # Start position of the shot
                event_type = event['type']['displayName']
                color = '#6DF176' if event_type == 'Goal' else 'red'

                # Draw the point (start of the shot)
                pitch_2.scatter(x, y, s=200, marker='o', color=color, edgecolor='white', linewidth=1.5, ax=ax_pitch_left)

                end_y = 100 - event['endX']
                end_x = 100 - event['endY']
                # Draw the arrow from the start position to the goal mouth
                pitch_2.arrows(x, y, end_x, end_y, width=2, headwidth=3, headlength=3, color=color, ax=ax_pitch_left)

        # Adding legend for shots
        legend_handles = [
            plt.Line2D([0], [0], marker='o', color='w', label='Tir', markerfacecolor='red', markersize=15),
            plt.Line2D([0], [0], marker='o', color='w', label='But', markerfacecolor='#6DF176', markersize=15)
        ]
        ax_pitch_left.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(0.97, 0.98), fontsize=12)

        # Heatmap on the right pitch
        ax_pitch_right = fig.add_subplot(gs[0:, 1], aspect=1)
        pitch.draw(ax=ax_pitch_right)

        ball_touches = [event for event in events if event['type']['displayName'] == 'BallTouch']
        x_coords = [t['x'] for t in ball_touches]
        y_coords = [t['y'] for t in ball_touches]

        bin_statistic = pitch.bin_statistic(x_coords, y_coords, statistic='count', bins=(20, 20))
        bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)

        el_greco_transparent_orange_red = mcolors.LinearSegmentedColormap.from_list(
            "Transparent-Orange-Red",
            [(1, 1, 1, 0), (1, 0.65, 0, 1), (1, 0, 0, 1)],  # Transparent to orange to red
            N=1000
        )

        pitch.heatmap(bin_statistic, ax=ax_pitch_right, cmap=el_greco_transparent_orange_red)
        
        # Display your tag or source at a fixed position
        ax.text(0.35, 0.775, f"@TarbouchData", fontsize=20, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)


        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.show()



    def plot_goalkeeper_activity(self, save_path, type_data):
        events = self.player_data.get('events', [])

        # Filtrage des événements défensifs
        gk_events = [
            event for event in events if event['type']['displayName'] in ['BallRecovery', 'KeeperPickup', 'Save', 'CornerAwarded', 'Clearance']
        ]

        if not gk_events:
            print(f"Aucune activité défensive trouvée pour {self.player_data['player_name']}. Aucun visuel généré.")
            return

        # Compter les événements défensifs par type
        ball_recoveries = [event for event in gk_events if event['type']['displayName'] == 'BallRecovery']
        successful_ball_recoveries = [event for event in ball_recoveries if event.get('outcomeType', {}).get('displayName') == 'Successful']

        keeper_pickup = [event for event in gk_events if event['type']['displayName'] == 'KeeperPickup']
        successful_keeper_pickup = [event for event in keeper_pickup if event.get('outcomeType', {}).get('displayName') == 'Successful']

        save = [event for event in gk_events if event['type']['displayName'] == 'Save']
        successful_save = [event for event in save if event.get('outcomeType', {}).get('displayName') == 'Successful']

        corner_awarded = [event for event in gk_events if event['type']['displayName'] == 'CornerAwarded']
        successful_corner_awarded = [event for event in corner_awarded if event.get('outcomeType', {}).get('displayName') == 'Successful']

        clearance = [event for event in gk_events if event['type']['displayName'] == 'Clearance']
        successful_clearance = [event for event in clearance if event.get('outcomeType', {}).get('displayName') == 'Successful']

        passes = [event for event in events if event['type']['displayName'] == 'Pass']

        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        total_passes = len(passes)

        # Définir les symboles et couleurs
        symbol_map = {
            'BallRecovery': 'o',
            'KeeperPickup': 's',
            'Save': '^',
            'CornerAwarded': '*',
            'Clearance': 'D'
        }
        color_map = {
            'Successful': '#6DF176',
            'Unsuccessful': 'red'
        }

        # Détection des passes décisives
        assists = [
            event for event in passes if any(
                q['type']['displayName'] in ['IntentionalGoalAssist', 'BigChanceCreated']
                for q in event.get('qualifiers', [])
            )
        ]
        nb_passe_d = len(assists)

        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        total_passes = len(passes)

        # Filtrage des événements offensifs
        offensive_events = [
            event for event in events if event['type']['displayName'] in ['TakeOn', 'MissedShots', 'SavedShot', 'Goal', 'Foul', 'Pass']
        ]
        goals = [event for event in offensive_events if event['type']['displayName'] == 'Goal']

        # Filtrer les passes clés (KeyPass)
        key_passes = [
            event for event in offensive_events if event['type']['displayName'] == 'Pass' and
            any(q['type']['displayName'] == 'KeyPass' for q in event.get('qualifiers', []))
        ]
        key_passes_successful = [
            event for event in key_passes if event.get('outcomeType', {}).get('displayName') == 'Successful'
        ]

        # Créer un gradient vertical
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        # Créer une figure
        fig = plt.figure(figsize=(16, 16))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        # Configuration de la grille
        gs = GridSpec(8, 3, height_ratios=[1, 1, 1, 1, 4, 4, 4, 4], width_ratios=[1,1,2])

        # Affichage de la photo du joueur
        PlayerProfileScraper(self.player_data['player_name']).save_player_profile()
        image_path = f"data/photo/{self.player_data['player_name'].replace(' ', '_')}_profile_image.jpg"
        player_photo = mpimg.imread(image_path)

        ax_image = fig.add_subplot(gs[:4, 0])
        ax_image.imshow(player_photo, aspect='equal')
        ax_image.set_anchor('W')
        ax_image.axis('off')

        # Statut du joueur et texte
        if self.player_data["isFirstEleven"]:
            status_text = "Titulaire"
            start_minute = 0
        else:
            first_minute = min(self.player_data["stats"]["ratings"].keys())
            status_text = f'Rentré {first_minute}"'
            start_minute = first_minute

        last_minute = list(self.player_data["stats"]["ratings"].keys())[-1]
        playing_time = int(last_minute) - int(start_minute)
        assists = sum(1 for event in self.player_data['events'] if any(qualifier['type']['displayName'] == 'IntentionalGoalAssist' for qualifier in event.get('qualifiers', [])))

        y_position = 0.96
        y_step = 0.03
        text_items = [
            f"{self.player_data['player_name']} - N°{self.player_data['shirtNo']}",
            f"{self.player_data['age']} ans - {self.player_data['height']}cm",
            f"{status_text} ",
            f"{self.match_teams}",
            f"Temps de jeu: {playing_time} minutes",
            f"{len(goals)} but(s)" if len(goals) >= 1 else None,
            f"{nb_passe_d} passe(s) décisive(s)" if nb_passe_d >= 1 else None,
            f"Man of the Match" if self.player_data['isManOfTheMatch'] else None
        ]

        for text in text_items:
            if text:
                fontsize = 16 if text == self.match_teams else 19
                ax.text(0.23, y_position, text, fontsize=fontsize, color='white', fontweight='bold', ha='left', transform=ax.transAxes)
                y_position -= y_step

        ax.text(0.425, 0.72, "@TarbouchData", fontsize=20, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        # Configuration des axes pour les statistiques
        ax_bars = [fig.add_subplot(gs[i, 2]) for i in range(4)]
        all_stats = [
            ("Passes clés", len(key_passes_successful), len(key_passes)),
            ('Passes réussies', len(successful_passes), total_passes),
            ('Récuperations', len(successful_ball_recoveries), len(ball_recoveries)),
            ('Arrets', len(successful_save), len(save)),
            ('Recuperations à la main', len(successful_keeper_pickup), len(keeper_pickup)),
            ('Corners gagnés', len(successful_corner_awarded), len(corner_awarded)),
            ('Dégagements', len(successful_clearance), len(clearance)),
        ]

        priorities = {'GK': ['Récuperations', 'Arrets', 'Passes réussies', "Ramassages de balle sécurisées"]}
        priority_stats = priorities.get(type_data, [])
        selected_stats = [stat for stat in all_stats if stat[0] in priority_stats and stat[1] > 0][:4]

        if len(selected_stats) < 4:
            remaining_stats = sorted([stat for stat in all_stats if stat not in selected_stats], key=lambda x: x[2], reverse=True)
            selected_stats.extend(remaining_stats[:4 - len(selected_stats)])

        for i, (label, value, total) in enumerate(selected_stats):
            self._add_horizontal_bar(ax_bars[i], label, value, total)

        # Premier terrain (passes)
        pitch_1 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch_left = fig.add_subplot(gs[4:, :2], aspect=1)
        pitch_1.draw(ax=ax_pitch_left)
        for pas in passes:
            y_start, x_start, y_end, x_end = pas['x'], pas['y'], pas['endX'], pas['endY']
            color = '#6DF176' if pas['outcomeType']['displayName'] == 'Successful' else 'red'
            pitch_1.arrows(y_start, x_start, y_end, x_end, width=3, headwidth=3, headlength=3, color=color, ax=ax_pitch_left)

        # Deuxième terrain inversé en bas à droite avec symboles pour les événements défensifs
        pitch_bottom = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2, half=True)
        ax_pitch_bottom = fig.add_subplot(gs[5:, 2])
        pitch_bottom.draw(ax=ax_pitch_bottom)

        # Ajouter les symboles pour les événements défensifs
        for event in gk_events:
            # Inversion des coordonnées pour correspondre à la rotation de 180 degrés
            y = 100 - event['x']
            x = 100 - event['y']
            event_type = event['type']['displayName']
            outcome = event.get('outcomeType', {}).get('displayName', 'Unsuccessful')

            # Définir la couleur et le symbole de chaque type d'événement
            color = color_map.get(outcome, 'red')
            symbol = symbol_map.get(event_type, 'o')

            # Si l'événement est une faute, définir la couleur en rouge et ignorer les fautes réussies
            if event_type == 'Foul' and outcome == 'Successful':
                continue
            elif event_type == 'Foul':
                color = 'red'

            # Affichage des événements avec symboles et couleurs
            ax_pitch_bottom.scatter(x, y, color=color, marker=symbol, s=300, edgecolor='white')

                # Ajouter une légende pour les symboles
        legend_handles = [
            plt.Line2D([0], [0], marker='o', color='w', label='Récupérations', markerfacecolor='black', markersize=20),
            plt.Line2D([0], [0], marker='s', color='w', label='Recuperations à la main', markerfacecolor='black', markersize=20),
            plt.Line2D([0], [0], marker='^', color='w', label='Arrêts', markerfacecolor='black', markersize=20),
            plt.Line2D([0], [0], marker='*', color='w', label='Corners gagnés', markerfacecolor='black', markersize=20),
            plt.Line2D([0], [0], marker='D', color='w', label='Dégagements', markerfacecolor='black', markersize=20)
        ]
        ax_pitch_bottom.legend(handles=legend_handles, loc='upper right', fontsize=20)

        # Inverser les axes pour obtenir la rotation de 180 degrés
        ax_pitch_bottom.invert_xaxis()
        ax_pitch_bottom.invert_yaxis()


        # Affichage final
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.show()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    def _normalize_position(self, position):
        """
        Normalise les codes de postes pour correspondre au système attendu
        """
        position_mapping = {
            # Gardiens
            'GK': 'GK', 'G': 'GK',

            # Défenseurs centraux
            'DC': 'CB', 'CB': 'CB', 'LCB': 'LCB', 'RCB': 'RCB',

            # Défenseurs latéraux
            'DR': 'RB', 'RB': 'RB', 'DL': 'LB', 'LB': 'LB',
            'RWB': 'RWB', 'LWB': 'LWB',

            # Milieux défensifs
            'DMC': 'DMC', 'DM': 'DM', 'MDC': 'DMC',

            # Milieux centraux
            'MC': 'MC', 'CM': 'CM', 'M': 'MC', 'ML': 'LM', 'MR': 'RM',

            # Milieux offensifs
            'AMC': 'AMC', 'CAM': 'CAM', 'MO': 'AMC', 'MOC': 'AMC',

            # Ailiers
            'LM': 'LM', 'RM': 'RM', 'LW': 'LW', 'RW': 'RW',
            'AG': 'LW', 'AD': 'RW',  # Ailier gauche/droite

            # Attaquants
            'CF': 'CF', 'ST': 'ST', 'FW': 'CF', 'BU': 'CF',  # FW = Forward, BU = Buteur
            'LF': 'LF', 'RF': 'RF'
        }

        # Retourner la position normalisée ou la position originale si pas trouvée
        return position_mapping.get(position, position)

# ===== SYSTÈME D'ÉVALUATION SCIENTIFIQUE DES STYLES DE JOUEUR - VERSION SIMPLIFIÉE =====

    def _evaluate_player_style_by_position(self, player_data):
        """Analyse scientifique du profil de joueur selon métriques objectives et contexte"""
        # CORRECTION: Récupérer la position dominante
        original_position = player_data.get('position', 'Unknown')
        position = self._get_dominant_position(original_position)

        # Normaliser la position avant analyse
        normalized_position = self._normalize_position(position)

        # Mettre à jour temporairement la position dans player_data pour les autres fonctions
        player_data_copy = player_data.copy()
        player_data_copy['position'] = normalized_position

        advanced_metrics = player_data.get('advanced_metrics', {})
        age = player_data.get('age', 25)
        match_info = player_data.get('match_info', {})
        basic_info = player_data.get('player_basic_info', {})

        # Variables contextuelles pour l'analyse
        context = {
            'age': age,
            'is_motm': basic_info.get('isManOfTheMatch', False),
            'is_starter': basic_info.get('isFirstEleven', True),
            'team_score': match_info.get('home_score', 0) if basic_info.get('team') == 'home' else match_info.get('away_score', 0),
            'opponent_score': match_info.get('away_score', 0) if basic_info.get('team') == 'home' else match_info.get('home_score', 0),
            'match_result': None
        }

        context['match_result'] = 'victory' if context['team_score'] > context['opponent_score'] else 'defeat' if context['team_score'] < context['opponent_score'] else 'draw'

        # Distribution par poste avec les positions normalisées
        position_mapping = {
            'GK': self._analyze_goalkeeper_profile,
            'CB': self._analyze_centerback_profile, 'LCB': self._analyze_centerback_profile, 'RCB': self._analyze_centerback_profile,
            'LB': self._analyze_fullback_profile, 'RB': self._analyze_fullback_profile, 'LWB': self._analyze_fullback_profile, 'RWB': self._analyze_fullback_profile,
            'DMC': self._analyze_defensive_midfielder_profile, 'DM': self._analyze_defensive_midfielder_profile,
            'MC': self._analyze_central_midfielder_profile, 'CM': self._analyze_central_midfielder_profile,
            'AMC': self._analyze_attacking_midfielder_profile, 'CAM': self._analyze_attacking_midfielder_profile,
            'LM': self._analyze_winger_profile, 'RM': self._analyze_winger_profile, 'LW': self._analyze_winger_profile, 'RW': self._analyze_winger_profile,
            'CF': self._analyze_forward_profile, 'ST': self._analyze_forward_profile, 'LF': self._analyze_forward_profile, 'RF': self._analyze_forward_profile
        }

        analyzer = position_mapping.get(normalized_position, self._analyze_generic_profile)
        return analyzer(advanced_metrics, context)

    def _analyze_goalkeeper_profile(self, metrics, context):
        """Analyse scientifique du profil gardien de but - Version phrase unique"""
        defensive = metrics.get('defensive', {})
        passing = metrics.get('passing', {})
        pressure = metrics.get('pressure', {})

        clearances = defensive.get('clearances', 0)
        pass_accuracy = passing.get('pass_accuracy', 50)
        pressure_success = pressure.get('pressure_success_rate', 50)
        long_balls = passing.get('long_balls', 0)

        if clearances > 8 and pressure_success > 80:
            profile = "PROFIL RÉACTIF SOUS CONTRAINTE"
            color = "#FF0000"
            analysis = f"Gardien très sollicité avec {clearances} dégagements et {pressure_success:.0f}% d'efficacité sous pression."

        elif pass_accuracy > 85 and long_balls > 3:
            profile = "PROFIL DISTRIBUTEUR LONGUE DISTANCE"
            color = "#00FF80"
            analysis = f"Spécialiste relance longue avec {pass_accuracy:.0f}% de précision et {long_balls} ballons longs."

        elif pass_accuracy > 85 and long_balls <= 2:
            profile = "PROFIL CONSTRUCTEUR COURT"
            color = "#00BFFF"
            analysis = f"Gardien moderne privilégiant la construction courte avec {pass_accuracy:.0f}% de précision."

        elif pressure_success < 65:
            profile = "PROFIL EN DIFFICULTÉ SOUS PRESSION"
            color = "#FF6B35"
            analysis = f"Efficacité réduite sous contrainte avec {pressure_success:.0f}% sous pression."

        else:
            profile = "PROFIL ÉQUILIBRÉ STANDARD"
            color = "#FFD700"
            analysis = f"Performance équilibrée sans spécialisation technique marquée."

        return profile, color, analysis

    def _analyze_centerback_profile(self, metrics, context):
        """Analyse scientifique du profil défenseur central - Version phrase unique"""
        defensive = metrics.get('defensive', {})
        passing = metrics.get('passing', {})
        pressure = metrics.get('pressure', {})

        tackles_won = defensive.get('tackles_won', 0)
        tackle_success = defensive.get('tackle_success_rate', 0)
        interceptions = defensive.get('interceptions', 0)
        ball_recoveries = defensive.get('ball_recoveries', 0)
        pass_accuracy = passing.get('pass_accuracy', 50)
        forward_pct = passing.get('risk_analysis', {}).get('forward_percentage', 0)
        pressure_success = pressure.get('pressure_success_rate', 50)

        total_defensive = tackles_won + interceptions + ball_recoveries
        intervention_ratio = interceptions / max(tackles_won, 1)

        if total_defensive > 12 and tackle_success > 75:
            profile = "PROFIL INTERVENTIONNISTE HAUTE EFFICACITÉ"
            color = "#FF0000"
            analysis = f"Défenseur très actif avec {total_defensive} actions défensives et {tackle_success:.0f}% d'efficacité."

        elif pass_accuracy > 90 and forward_pct > 35:
            profile = "PROFIL CONSTRUCTEUR PROGRESSIF"
            color = "#00FF80"
            analysis = f"Défenseur moderne avec {pass_accuracy:.0f}% de précision et {forward_pct:.0f}% de passes progressives."

        elif intervention_ratio > 2.0:
            profile = "PROFIL ANTICIPATEUR PRÉVENTIF"
            color = "#00BFFF"
            analysis = f"Défenseur intelligent avec ratio interceptions/tacles de {intervention_ratio:.1f}."

        elif pressure_success < 70:
            profile = "PROFIL EN DIFFICULTÉ SOUS PRESSION"
            color = "#FF6B35"
            analysis = f"Efficacité réduite avec {pressure_success:.0f}% sous pression, adaptation tactique nécessaire."

        else:
            profile = "PROFIL DÉFENSIF POLYVALENT"
            color = "#FFD700"
            analysis = f"Défenseur équilibré combinant solidité défensive et relance efficace."

        return profile, color, analysis

    def _analyze_fullback_profile(self, metrics, context):
        """Analyse scientifique du profil latéral - Version phrase unique"""
        offensive = metrics.get('offensive', {})
        defensive = metrics.get('defensive', {})
        spatial = metrics.get('spatial', {})
        passing = metrics.get('passing', {})

        dribble_success = offensive.get('dribble_success_rate', 0)
        crosses = passing.get('crosses', 0)
        defensive_actions = defensive.get('total_defensive_actions', 0)
        zones = spatial.get('zones_coverage', {})
        attacking_third = zones.get('attacking_third', 0)
        own_third = zones.get('own_third', 0)
        mobility_score = spatial.get('mobility_score', 0)

        offensive_engagement = attacking_third / max(own_third, 1)

        if attacking_third > 30 and crosses > 5:
            profile = "PROFIL OFFENSIF SPÉCIALISÉ CENTRES"
            color = "#FF0080"
            analysis = f"Latéral offensif avec {attacking_third} actions offensives et {crosses} centres."

        elif mobility_score > 25 and offensive_engagement > 1.5:
            profile = "PROFIL HYBRIDE HAUTE MOBILITÉ"
            color = "#FFD700"
            analysis = f"Joueur bi-phasique avec mobilité {mobility_score:.1f} et ratio off/déf {offensive_engagement:.1f}."

        elif defensive_actions > 8 and attacking_third < 20:
            profile = "PROFIL DÉFENSIF CONSERVATEUR"
            color = "#00FF80"
            analysis = f"Latéral défensif avec {defensive_actions} actions défensives et peu de présence offensive."

        else:
            profile = "PROFIL LATÉRAL ÉQUILIBRÉ"
            color = "#00BFFF"
            analysis = f"Profil équilibré avec contributions régulières sur les deux phases."

        return profile, color, analysis

    def _analyze_defensive_midfielder_profile(self, metrics, context):
        """Analyse scientifique du profil milieu défensif - Version phrase unique"""
        defensive = metrics.get('defensive', {})
        passing = metrics.get('passing', {})
        spatial = metrics.get('spatial', {})
        pressure = metrics.get('pressure', {})

        ball_recoveries = defensive.get('ball_recoveries', 0)
        interceptions = defensive.get('interceptions', 0)
        pass_accuracy = passing.get('pass_accuracy', 50)
        risk_analysis = passing.get('risk_analysis', {})
        backward_pct = risk_analysis.get('backward_percentage', 0)
        forward_pct = risk_analysis.get('forward_percentage', 0)
        pressure_success = pressure.get('pressure_success_rate', 50)
        field_coverage = spatial.get('field_coverage_percentage', 0)

        recovery_efficiency = ball_recoveries + interceptions

        if recovery_efficiency > 10 and pressure_success > 85:
            profile = "PROFIL RÉCUPÉRATEUR HAUTE PERFORMANCE"
            color = "#FF0000"
            analysis = f"Récupérateur efficace avec {recovery_efficiency} récupérations et {pressure_success:.0f}% sous pression."

        elif pass_accuracy > 90 and forward_pct > 40:
            profile = "PROFIL DISTRIBUTEUR PROGRESSIF"
            color = "#00FF80"
            analysis = f"Relanceur technique avec {pass_accuracy:.0f}% de précision et {forward_pct:.0f}% vers l'avant."

        elif backward_pct > 55 and pass_accuracy > 88:
            profile = "PROFIL SÉCURITAIRE TECHNIQUE"
            color = "#00BFFF"
            analysis = f"Joueur discipliné avec {backward_pct:.0f}% de passes sécurisées à {pass_accuracy:.0f}%."

        elif field_coverage > 35:
            profile = "PROFIL COUVREUR SPATIAL"
            color = "#FFD700"
            analysis = f"Gros volume de jeu avec {field_coverage:.0f}% de couverture du terrain."

        else:
            profile = "PROFIL MILIEU DÉFENSIF STANDARD"
            color = "#FF6B35"
            analysis = f"Profil équilibré avec métriques stables sans dominance claire."

        return profile, color, analysis

    def _analyze_central_midfielder_profile(self, metrics, context):
        """Analyse scientifique du profil milieu central - Version phrase unique"""
        passing = metrics.get('passing', {})
        spatial = metrics.get('spatial', {})
        basic = metrics.get('basic', {})

        total_passes = passing.get('total_passes', 0)
        pass_accuracy = passing.get('pass_accuracy', 50)
        mobility_score = spatial.get('mobility_score', 0)
        field_coverage = spatial.get('field_coverage_percentage', 0)
        success_rate = basic.get('success_rate', 50)
        forward_pct = passing.get('risk_analysis', {}).get('forward_percentage', 0)

        if mobility_score > 25 and field_coverage > 35:
            profile = "PROFIL BOX-TO-BOX HAUTE INTENSITÉ"
            color = "#FF0080"
            analysis = f"Joueur très mobile avec mobilité {mobility_score:.1f} et {field_coverage:.0f}% de couverture terrain."

        elif total_passes > 60 and pass_accuracy > 90:
            profile = "PROFIL MÉTRONOME TECHNIQUE"
            color = "#00FF80"
            analysis = f"Spécialiste circulation avec {total_passes} passes et {pass_accuracy:.0f}% de précision."

        elif forward_pct > 45 and success_rate > 85:
            profile = "PROFIL CRÉATEUR PROGRESSIF"
            color = "#FFD700"
            analysis = f"Créateur avec {forward_pct:.0f}% de passes progressives et {success_rate:.0f}% d'efficacité."

        else:
            profile = "PROFIL MILIEU POLYVALENT"
            color = "#00BFFF"
            analysis = f"Joueur polyvalent avec métriques équilibrées et profil flexible."

        return profile, color, analysis

    def _analyze_attacking_midfielder_profile(self, metrics, context):
        """Analyse scientifique du profil milieu offensif - Version phrase unique"""
        offensive = metrics.get('offensive', {})
        basic = metrics.get('basic', {})
        spatial = metrics.get('spatial', {})
        pressure = metrics.get('pressure', {})

        goals = offensive.get('goals', 0)
        key_passes = offensive.get('key_passes', 0)
        dribble_success = offensive.get('dribble_success_rate', 0)
        dribbles_attempted = offensive.get('dribbles_attempted', 0)
        shots_total = offensive.get('shots_total', 0)
        mobility_score = spatial.get('mobility_score', 0)
        total_actions = basic.get('total_actions', 0)
        success_rate = basic.get('success_rate', 50)
        pressure_success = pressure.get('pressure_success_rate', 50)

        if goals >= 2:
            profile = "PROFIL FINISSEUR HAUTE EFFICACITÉ"
            color = "#FF0000"
            analysis = f"Joueur décisif avec {goals} buts sur {shots_total} tirs, efficacité maximale en finition."

        elif total_actions > 80 and success_rate > 80:
            profile = "PROFIL HYPERACTIF TECHNIQUE"
            color = "#00FF80"
            analysis = f"Meneur très actif avec {total_actions} actions et {success_rate:.0f}% d'efficacité."

        elif mobility_score > 25:
            profile = "PROFIL MOBILE HAUTE INTENSITÉ"
            color = "#FFD700"
            analysis = f"Joueur très mobile avec score {mobility_score:.1f} et maintien de patterns complexes."

        elif pressure_success > 85:
            profile = "PROFIL RÉSISTANT AU STRESS SITUATIONNEL"
            color = "#FF0080"
            analysis = f"Excellente gestion sous pression avec {pressure_success:.0f}% d'efficacité sous contrainte."

        else:
            profile = "PROFIL OFFENSIF POLYVALENT"
            color = "#00BFFF"
            analysis = f"Joueur offensif polyvalent cherchant l'efficacité dans toutes les phases."

        return profile, color, analysis

    def _analyze_winger_profile(self, metrics, context):
        """Analyse scientifique du profil ailier - Version phrase unique"""
        offensive = metrics.get('offensive', {})
        passing = metrics.get('passing', {})
        spatial = metrics.get('spatial', {})

        dribble_success = offensive.get('dribble_success_rate', 0)
        dribbles_attempted = offensive.get('dribbles_attempted', 0)
        crosses = passing.get('crosses', 0)
        goals = offensive.get('goals', 0)
        zones = spatial.get('zones_coverage', {})
        wing_actions = zones.get('left_wing', 0) + zones.get('right_wing', 0)
        center_actions = zones.get('center', 0)

        lateral_specialization = wing_actions / max(center_actions, 1)

        if dribble_success > 70 and dribbles_attempted > 5:
            profile = "PROFIL DRIBBLEUR TECHNIQUE SPÉCIALISÉ"
            color = "#FF0080"
            analysis = f"Spécialiste élimination avec {dribbles_attempted} tentatives et {dribble_success:.0f}% de réussite."

        elif crosses > 8 and lateral_specialization > 2:
            profile = "PROFIL CENTREUR LATÉRAL SPÉCIALISÉ"
            color = "#00FF80"
            analysis = f"Expert centres avec {crosses} centres et latéralité {lateral_specialization:.1f}."

        elif goals > 3 and center_actions > wing_actions:
            profile = "PROFIL AILIER RENTRANT FINISSEUR"
            color = "#FF0000"
            analysis = f"Ailier finisseur avec {goals} buts et prédominance d'actions centrales."

        else:
            profile = "PROFIL AILIER POLYVALENT"
            color = "#00BFFF"
            analysis = f"Profil adaptable avec répartition équilibrée des actions latérales et centrales."

        return profile, color, analysis

    def _analyze_forward_profile(self, metrics, context):
        """Analyse scientifique du profil attaquant - Version phrase unique"""
        offensive = metrics.get('offensive', {})
        spatial = metrics.get('spatial', {})
        passing = metrics.get('passing', {})

        goals = offensive.get('goals', 0)
        shots_total = offensive.get('shots_total', 0)
        shooting_accuracy = offensive.get('shooting_accuracy', 0)
        key_passes = offensive.get('key_passes', 0)
        zones = spatial.get('zones_coverage', {})
        attacking_third = zones.get('attacking_third', 0)

        conversion_rate = (goals / max(shots_total, 1)) * 100

        if goals > 2 and shooting_accuracy > 70:
            profile = "PROFIL FINISSEUR HAUTE PRÉCISION"
            color = "#FF0000"
            analysis = f"Finisseur précis avec {goals} buts sur {shots_total} tirs et {shooting_accuracy:.0f}% de précision."

        elif shots_total > 8 and conversion_rate < 25:
            profile = "PROFIL ATTAQUANT VOLUME À FAIBLE CONVERSION"
            color = "#FF6B35"
            analysis = f"Approche quantitative avec {shots_total} tirs mais {conversion_rate:.0f}% de conversion."

        elif key_passes > 5:
            profile = "PROFIL ATTAQUANT CRÉATEUR"
            color = "#00FF80"
            analysis = f"Spécialiste création avec {key_passes} passes décisives, profil moderne."

        elif attacking_third > 40 and goals > 1:
            profile = "PROFIL SPÉCIALISTE SURFACE DE RÉPARATION"
            color = "#00BFFF"
            analysis = f"Expert zone de finition avec {attacking_third} actions offensives et {goals} buts."

        else:
            profile = "PROFIL ATTAQUANT POLYVALENT"
            color = "#FFD700"
            analysis = f"Attaquant adaptatif avec métriques équilibrées sans spécialisation marquée."

        return profile, color, analysis

    def _analyze_generic_profile(self, metrics, context):
        """Analyse scientifique générique pour postes non spécifiés - Version phrase unique"""
        basic = metrics.get('basic', {})
        pressure = metrics.get('pressure', {})

        success_rate = basic.get('success_rate', 50)
        total_actions = basic.get('total_actions', 0)
        pressure_success = pressure.get('pressure_success_rate', 50)

        action_density = total_actions / 90 if total_actions > 0 else 0

        if success_rate > 85 and pressure_success > 80:
            profile = "PROFIL HAUTE FIABILITÉ TECHNIQUE"
            color = "#00FF80"
            analysis = f"Performance de haut niveau avec {success_rate:.0f}% d'efficacité et {pressure_success:.0f}% sous contrainte."

        elif total_actions > 80:
            profile = "PROFIL HAUTE DENSITÉ D'ACTIONS"
            color = "#FF0080"
            analysis = f"Implication exceptionnelle avec {total_actions} actions ({action_density:.1f}/minute)."

        elif success_rate < 65:
            profile = "PROFIL À DÉVELOPPER TECHNIQUEMENT"
            color = "#FF6B35"
            analysis = f"Marge de progression avec {success_rate:.0f}% d'efficacité technique globale."

        else:
            profile = "PROFIL STANDARD ÉQUILIBRÉ"
            color = "#00BFFF"
            analysis = f"Performance dans les standards avec {success_rate:.0f}% d'efficacité technique."

        return profile, color, analysis

    # ===== FONCTIONS D'INTÉGRATION DANS LES ANALYSES EXISTANTES - VERSION SIMPLIFIÉE =====

    def _get_position_adapted_creativity_analysis(self, player_data, creativity_ratio):
        """Analyse adaptée de la créativité selon le poste - Version phrase unique avec position normalisée"""
        original_position = player_data.get('position', 'Unknown')

        # CORRECTION: Récupérer la position dominante
        position = self._get_dominant_position(original_position)
        normalized_position = self._normalize_position(position)

        # Seuils adaptatifs selon le poste normalisé
        position_creativity_thresholds = {
            'GK': {'low': 15, 'high': 35},
            'CB': {'low': 20, 'high': 40}, 'LCB': {'low': 20, 'high': 40}, 'RCB': {'low': 20, 'high': 40},
            'LB': {'low': 35, 'high': 55}, 'RB': {'low': 35, 'high': 55}, 'LWB': {'low': 40, 'high': 65}, 'RWB': {'low': 40, 'high': 65},
            'DMC': {'low': 25, 'high': 45}, 'DM': {'low': 25, 'high': 45},
            'MC': {'low': 35, 'high': 55}, 'CM': {'low': 35, 'high': 55},
            'AMC': {'low': 45, 'high': 70}, 'CAM': {'low': 45, 'high': 70},
            'LM': {'low': 50, 'high': 75}, 'RM': {'low': 50, 'high': 75}, 'LW': {'low': 55, 'high': 80}, 'RW': {'low': 55, 'high': 80},
            'CF': {'low': 40, 'high': 65}, 'ST': {'low': 40, 'high': 65}, 'LF': {'low': 45, 'high': 70}, 'RF': {'low': 45, 'high': 70}
        }

        thresholds = position_creativity_thresholds.get(normalized_position, {'low': 35, 'high': 55})

        if creativity_ratio > thresholds['high']:
            level = "CRÉATIVITÉ ÉLEVÉE POUR LE POSTE"
            color = "#FF0080"
            interpretation = f"Joueur très créatif avec {creativity_ratio:.0f}% d'actions risquées, au-dessus du standard {normalized_position}."

        elif creativity_ratio < thresholds['low']:
            level = "CRÉATIVITÉ CONSERVATRICE ADAPTÉE"
            color = "#00FF80"
            interpretation = f"Approche disciplinée avec {creativity_ratio:.0f}% d'actions créatives, conforme aux exigences du poste {normalized_position}."

        else:
            level = "CRÉATIVITÉ ÉQUILIBRÉE POSITIONNELLE"
            color = "#FFD700"
            interpretation = f"Équilibre optimal avec {creativity_ratio:.0f}% d'actions créatives pour un {normalized_position}."

        return level, color, interpretation

    def _get_position_adapted_efficiency_thresholds(self, position, age):
        """Retourne les seuils d'efficacité adaptés au poste et à l'âge avec position normalisée"""
        # CORRECTION: Récupérer la position dominante
        dominant_position = self._get_dominant_position(position)
        normalized_position = self._normalize_position(dominant_position)

        base_thresholds = {
            'GK': [95, 85, 75, 65, 55],
            'CB': [90, 80, 70, 60, 50], 'LCB': [90, 80, 70, 60, 50], 'RCB': [90, 80, 70, 60, 50],
            'LB': [80, 70, 60, 50, 40], 'RB': [80, 70, 60, 50, 40], 'LWB': [75, 65, 55, 45, 35], 'RWB': [75, 65, 55, 45, 35],
            'DMC': [85, 75, 65, 55, 45], 'DM': [85, 75, 65, 55, 45],
            'MC': [80, 70, 60, 50, 40], 'CM': [80, 70, 60, 50, 40],
            'AMC': [70, 60, 50, 40, 30], 'CAM': [70, 60, 50, 40, 30],
            'LM': [75, 65, 55, 45, 35], 'RM': [75, 65, 55, 45, 35], 'LW': [70, 60, 50, 40, 30], 'RW': [70, 60, 50, 40, 30],
            'CF': [65, 55, 45, 35, 25], 'ST': [65, 55, 45, 35, 25], 'LF': [70, 60, 50, 40, 30], 'RF': [70, 60, 50, 40, 30]
        }

        thresholds = base_thresholds.get(normalized_position, [80, 70, 60, 50, 40])

        # Ajustement selon l'âge (simplifié)
        if age > 32:
            thresholds = [t - 5 for t in thresholds]
        elif age < 23:
            thresholds = [t - 3 for t in thresholds]

        return thresholds
    
    
    


    # ===== SYSTÈME DE BOÎTES EXPLICATIVES ULTRA-FLEXIBLE =====

    def create_explanation_box(self, ax, x, y, width, height, title, main_stat, explanation, color):
        """
        Fonction optimisée pour créer des boîtes explicatives ultra-flexibles - VERSION AGRANDIE
        """

        # Rectangle de fond principal
        rect = plt.Rectangle((x, y), width, height, facecolor='black', alpha=0.9, 
                        edgecolor=color, linewidth=3, transform=ax.transAxes)
        ax.add_patch(rect)

        # EN-TÊTE COLORÉ
        header_height = 0.14  # Légèrement augmenté pour le texte plus grand
        title_rect = plt.Rectangle((x, y + height - header_height), width, header_height, 
                                facecolor=color, alpha=0.85, transform=ax.transAxes)
        ax.add_patch(title_rect)

        # TITRE dans l'en-tête
        title_fontsize = 18 if len(title) <= 20 else 16
        ax.text(x + width/2, y + height - header_height/2, title, fontsize=title_fontsize, 
            color='white', fontweight='bold', ha='center', va='center', transform=ax.transAxes)

        # STATISTIQUE PRINCIPALE
        stat_y_position = y + height - header_height - 0.13
        stat_fontsize = 26 if len(main_stat) < 15 else 22
        ax.text(x + width/2, stat_y_position, main_stat, fontsize=stat_fontsize, 
            color='white', fontweight='bold', ha='center', va='center', transform=ax.transAxes)

        # TEXTE D'INTERPRÉTATION
        processed_text = self._process_explanation_text_full(explanation, width)
        text_y_position = y + height * 0.34  # Ajusté pour garder un bon équilibre
        ax.text(x + width/2, text_y_position, processed_text, fontsize=18, color='white', 
            fontweight='bold', ha='center', va='center', transform=ax.transAxes,
            linespacing=1.4)


    def _process_explanation_text_full(self, explanation, box_width):
        """
        Version améliorée qui évite la troncature en "..." et optimise pour des boîtes plus grandes

        Paramètres:
        - explanation: texte brut à traiter
        - box_width: largeur de la boîte pour calculer la limite de caractères

        Retourne: texte formaté optimisé SANS troncature
        """

        # Calcul dynamique SANS limite stricte de lignes
        if box_width <= 0.25:  # Boîte étroite
            char_limit = 25
        elif box_width <= 0.35:  # Boîte moyenne
            char_limit = 35
        else:  # Boîte large
            char_limit = 45

        # Séparer les lignes pré-formatées
        lines = explanation.split('\n')
        processed_lines = []

        for line in lines:
            line = line.strip()  # Supprimer espaces en début/fin

            if not line:  # Ligne vide = saut de ligne intentionnel
                processed_lines.append("")
                continue

            # Si la ligne dépasse la limite, la découper intelligemment
            if len(line) > char_limit:
                words = line.split(' ')
                current_line = ""

                for word in words:
                    # Test si ajouter ce mot dépasse la limite
                    test_line = current_line + (" " + word if current_line else word)

                    if len(test_line) <= char_limit:
                        current_line = test_line
                    else:
                        # Sauvegarder la ligne actuelle et commencer une nouvelle
                        if current_line:
                            processed_lines.append(current_line)
                        current_line = word

                # Ajouter la dernière ligne
                if current_line:
                    processed_lines.append(current_line)
            else:
                processed_lines.append(line)

        # SUPPRESSION de la limitation du nombre de lignes - tout le texte s'affiche
        return '\n'.join(processed_lines)


    # ===== FONCTIONS D'AIDE POUR GÉNÉRER DU CONTENU INTELLIGENT =====

    def _evaluate_performance_level(self, percentage):
        """Évalue un pourcentage et retourne niveau + couleur"""
        if percentage >= 85:
            return "EXCEPTIONNEL", "#00FF00"
        elif percentage >= 75:
            return "EXCELLENT", "#7FFF00"
        elif percentage >= 65:
            return "TRÈS BON", "#FFD700"
        elif percentage >= 55:
            return "BON", "#FFA500"
        elif percentage >= 45:
            return "MOYEN", "#FF6347"
        else:
            return "FAIBLE", "#FF0000"

    def _evaluate_frequency_level(self, count, total):
        """Évalue une fréquence et retourne niveau + couleur"""
        ratio = (count / total * 100) if total > 0 else 0

        if ratio >= 70:
            return "TRÈS FRÉQUENT", ratio, "#FF0080"
        elif ratio >= 50:
            return "FRÉQUENT", ratio, "#FF6B35"
        elif ratio >= 30:
            return "MODÉRÉ", ratio, "#FFD700"
        elif ratio >= 15:
            return "OCCASIONNEL", ratio, "#00BFFF"
        else:
            return "RARE", ratio, "#00FF80"

    def _evaluate_mobility_level(self, mobility_score):
        """Évalue la mobilité et retourne niveau + couleur + interprétation"""
        if mobility_score > 30:
            level = "TRÈS MOBILE"
            color = "#FF0080"
            interpretation = f"Se déplace énormément sur le terrain (score: {mobility_score:.1f}). Joueur imprévisible qui couvre beaucoup d'espace. Difficile à marquer car change constamment de position."
        elif mobility_score > 20:
            level = "MOBILE"
            color = "#FFD700"
            interpretation = f"Bouge régulièrement de position (score: {mobility_score:.1f}). Bon équilibre entre stabilité positionnelle et mouvement. Apporte de la variété au jeu."
        elif mobility_score > 10:
            level = "POSITIONNEL"
            color = "#00BFFF"
            interpretation = f"Reste principalement dans sa zone (score: {mobility_score:.1f}). Joueur stable qui maîtrise bien son secteur. Fiable dans son positionnement."
        else:
            level = "TRÈS STATIQUE"
            color = "#00FF80"
            interpretation = f"Position très fixe sur le terrain (score: {mobility_score:.1f}). Spécialiste de sa zone, très prévisible mais solide dans son rôle."

        return level, color, interpretation

    def _generate_tactical_interpretation(self, forward_pct, lateral_pct, backward_pct):
        """Génère une interprétation tactique basée sur les directions de passes"""

        if forward_pct > 60:
            style = "PROGRESSISTE"
            color = "#00FF80"
            interpretation = f"Cherche constamment la progression ({forward_pct:.0f}% vers l'avant). Joueur offensif qui prend des risques pour faire avancer l'équipe. Créateur d'occasions mais parfois imprécis."
        elif forward_pct > 45:
            style = "ÉQUILIBRÉ"
            color = "#FFD700"
            interpretation = f"Mélange progression et sécurité ({forward_pct:.0f}% avant, {lateral_pct:.0f}% latéral). Vision tactique mature, adapte son jeu selon les situations."
        elif lateral_pct > 50:
            style = "CONSERVATEUR"
            color = "#00BFFF"
            interpretation = f"Privilégie la conservation ({lateral_pct:.0f}% latéral, {backward_pct:.0f}% arrière). Joueur sûr qui évite les pertes de balle, excellent pour garder le contrôle."
        else:
            style = "SÉCURITAIRE"
            color = "#FF6B35"
            interpretation = f"Joue très prudemment ({backward_pct:.0f}% vers l'arrière). Défenseur ou milieu défensif qui sécurise le jeu. Très peu de pertes de balle."

        return style, color, interpretation

    def _analyze_pressure_resistance(self, pressure_efficiency, normal_efficiency):
        """Analyse la résistance à la pression"""
        diff = pressure_efficiency - normal_efficiency

        if diff > 10:
            level = "CLUTCH"
            color = "#00FF00"
            interpretation = f"Encore plus fort sous pression ! ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}% normal). Joueur exceptionnel qui élève son niveau dans les moments difficiles. Mental d'acier."
        elif diff > 0:
            level = "SOLIDE"
            color = "#7FFF00"
            interpretation = f"Maintient son niveau sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%). Fiable dans les moments chauds, ne craque pas mentalement."
        elif diff > -5:
            level = "STABLE"
            color = "#FFD700"
            interpretation = f"Légère baisse sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%). Performance honorable mais peut progresser mentalement."
        elif diff > -15:
            level = "FRAGILE"
            color = "#FFA500"
            interpretation = f"Efficacité réduite sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%). Doit travailler sa gestion du stress et la prise de décision rapide."
        else:
            level = "TRÈS FRAGILE"
            color = "#FF0000"
            interpretation = f"S'effondre sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%). Problème mental majeur, évite les situations de stress."

        return level, color, interpretation

    # ===== FONCTION UTILITAIRE AMÉLIORÉE =====

    def generate_advanced_analysis_suite(self, save_dir="advanced_analysis"):
        """Génère toutes les analyses avancées d'un coup - Version améliorée"""
        import os

        os.makedirs(save_dir, exist_ok=True)
        player_name_clean = self.player_data['player_name'].replace(' ', '_')

        print(f"Génération de la suite d'analyses avancées pour {self.player_data['player_name']}...")

        try:
            # 1. Analyse spatiale
            spatial_path = os.path.join(save_dir, f"{player_name_clean}_spatial_intelligence.png")
            self.plot_positional_intelligence(spatial_path)
            print("✅ Analyse spatiale générée")

            # 2. Analyse de pression
            pressure_path = os.path.join(save_dir, f"{player_name_clean}_pressure_analysis.png")
            self.plot_pressure_analysis(pressure_path)
            print("✅ Analyse de pression générée")

            # 3. Analyse prédictive
            prediction_path = os.path.join(save_dir, f"{player_name_clean}_predictive_analysis.png")
            self.plot_next_action_prediction(prediction_path)
            print("✅ Analyse prédictive générée")

            print(f"🎉 Suite d'analyses complète disponible dans: {save_dir}")

            return {
                "spatial": spatial_path,
                "pressure": pressure_path, 
                "predictive": prediction_path
            }

        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")
            return None

    # ===== FONCTION BONUS AMÉLIORÉE =====

    def compare_players_advanced_metrics(self, other_players_data, save_path):
        """Compare les métriques avancées entre plusieurs joueurs - Version ultra-stylisée"""

        def extract_player_metrics(player_data):
            """Extrait les métriques clés d'un joueur"""
            events = player_data.get('events', [])
            if not events:
                return None

            # Métriques de base
            total_actions = len(events)
            successful_actions = len([e for e in events if e.get('outcomeType', {}).get('displayName') == 'Successful'])
            success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0

            # Analyse de pression (simplifié)
            pressure_events = 0
            for i, event in enumerate(events):
                current_time = event['minute'] * 60 + event.get('second', 0)
                for j in range(max(0, i-5), i):
                    prev_time = events[j]['minute'] * 60 + events[j].get('second', 0)
                    if current_time - prev_time <= 3:
                        pressure_events += 1
                        break
                    
            pressure_ratio = (pressure_events / total_actions * 100) if total_actions > 0 else 0

            # Diversité d'actions
            action_diversity = len(set([e['type']['displayName'] for e in events]))

            # Zone de confort (efficacité par zone)
            zones = {'Défensive': [], 'Milieu': [], 'Offensive': []}
            for event in events:
                if 'x' in event and 'y' in event:
                    y = event['y']
                    zone = 'Défensive' if y < 33 else 'Milieu' if y < 66 else 'Offensive'
                    zones[zone].append(event)

            zone_efficiencies = {}
            for zone, zone_events in zones.items():
                if zone_events:
                    successful = len([e for e in zone_events if e.get('outcomeType', {}).get('displayName') == 'Successful'])
                    zone_efficiencies[zone] = (successful / len(zone_events)) * 100
                else:
                    zone_efficiencies[zone] = 0

            best_zone_efficiency = max(zone_efficiencies.values()) if zone_efficiencies else 0

            return {
                'name': player_data.get('player_name', 'Unknown'),
                'total_actions': total_actions,
                'success_rate': success_rate,
                'pressure_ratio': pressure_ratio,
                'action_diversity': action_diversity,
                'best_zone_efficiency': best_zone_efficiency
            }

        # Extraire les métriques pour tous les joueurs
        all_players = [self.player_data] + other_players_data
        players_metrics = []

        for player_data in all_players:
            metrics = extract_player_metrics(player_data)
            if metrics:
                players_metrics.append(metrics)

        if len(players_metrics) < 2:
            print("Pas assez de joueurs pour la comparaison")
            return

        # Créer la visualisation comparative ultra-stylisée
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        fig = plt.figure(figsize=(18, 12))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        gs = GridSpec(3, 2, height_ratios=[1, 2, 2])

        # Titre ultra-stylisé
        ax.text(0.5, 0.95, "COMPARAISON MULTI-JOUEURS AVANCÉE", 
                fontsize=28, color='white', fontweight='bold', ha='center', transform=ax.transAxes)

        # ===== RADAR CHART COMPARATIF =====
        ax_radar = fig.add_subplot(gs[1, 0], projection='polar')
        ax_radar.set_facecolor('none')

        # Préparer les données du radar
        metrics_names = ['Efficacité', 'Résistance', 'Diversité', 'Zone Max', 'Volume']
        angles = np.linspace(0, 2 * np.pi, len(metrics_names), endpoint=False).tolist()
        angles += angles[:1]  # Fermer le cercle

        colors = ['#FF6B35', '#00FF80', '#FFD700', '#FF0080', '#00BFFF']

        for i, player_metrics in enumerate(players_metrics[:5]):  # Max 5 joueurs
            # Normaliser les métriques (0-100)
            values = [
                player_metrics['success_rate'],
                100 - player_metrics['pressure_ratio'],  # Inverser car moins de pression = mieux
                min(100, player_metrics['action_diversity'] * 10),  # Normaliser diversité
                player_metrics['best_zone_efficiency'],
                min(100, player_metrics['total_actions'] / 2)  # Normaliser volume
            ]
            values += values[:1]  # Fermer le cercle

            ax_radar.plot(angles, values, 'o-', linewidth=4, label=player_metrics['name'], 
                        color=colors[i], markersize=8)
            ax_radar.fill(angles, values, alpha=0.25, color=colors[i])

        ax_radar.set_xticks(angles[:-1])
        ax_radar.set_xticklabels(metrics_names, color='white', fontsize=12, fontweight='bold')
        ax_radar.set_ylim(0, 100)
        ax_radar.grid(True, alpha=0.3, color='white')

        # Légende avec fond noir
        legend_radar = ax_radar.legend(loc='upper right', bbox_to_anchor=(1, 1), fontsize=12,
                                    frameon=True, facecolor='black', edgecolor='white')
        for text in legend_radar.get_texts():
            text.set_color('white')

        ax_radar.set_title('Profils Comparatifs', color='white', fontsize=20, fontweight='bold', pad=30)

        # ===== CLASSEMENT GÉNÉRAL =====
        ax_ranking = fig.add_subplot(gs[1:, 1])
        ax_ranking.axis('off')

        # Calculer un score composite
        for player_metrics in players_metrics:
            composite_score = (
                player_metrics['success_rate'] * 0.3 +
                (100 - player_metrics['pressure_ratio']) * 0.2 +
                min(100, player_metrics['action_diversity'] * 10) * 0.2 +
                player_metrics['best_zone_efficiency'] * 0.2 +
                min(100, player_metrics['total_actions'] / 2) * 0.1
            )
            player_metrics['composite_score'] = composite_score

        # Trier par score composite
        players_metrics.sort(key=lambda x: x['composite_score'], reverse=True)

        # Créer le classement stylisé
        ranking_text = "🏆 CLASSEMENT GÉNÉRAL\n" + "="*50 + "\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

        for i, player in enumerate(players_metrics):
            medal = medals[i] if i < 5 else f"{i+1}️⃣"

            # Évaluation du score
            score = player['composite_score']
            if score > 85:
                grade = "EXCEPTIONNEL ⭐"
            elif score > 75:
                grade = "EXCELLENT 🔥"
            elif score > 65:
                grade = "TRÈS BON 💪"
            elif score > 55:
                grade = "BON ✅"
            else:
                grade = "MOYEN 📈"

            ranking_text += f"{medal} {player['name']}\n"
            ranking_text += f"     Score: {score:.1f}/100 - {grade}\n"
            ranking_text += f"     Efficacité: {player['success_rate']:.1f}% | "
            ranking_text += f"Actions: {player['total_actions']} | "
            ranking_text += f"Diversité: {player['action_diversity']}\n\n"

        # Créer une boîte stylisée pour le classement
        ranking_box = plt.Rectangle((0.05, 0.1), 0.9, 0.8, facecolor='black', alpha=0.9, 
                                edgecolor='white', linewidth=3, transform=ax_ranking.transAxes)
        ax_ranking.add_patch(ranking_box)

        ax_ranking.text(0.5, 0.5, ranking_text, fontsize=14, color='white', 
                    fontweight='bold', ha='center', va='center', transform=ax_ranking.transAxes,
                    linespacing=1.5)

        # Tag et source ultra-stylisé
        ax.text(0.4, 0.25, f"@TarbouchData", fontsize=30, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()

        return players_metrics


















































































# ===== FONCTIONS D'ANALYSE COMPORTEMENTALE SPÉCIALISÉES - VERSION SIMPLIFIÉE =====

    def _analyze_predictability_by_age_position(self, position, predictability_score, action_diversity):
        """Analyse la prévisibilité selon le poste - Version phrase unique"""
        
        if predictability_score > 75:
            title = "COMPORTEMENT TRÈS PRÉVISIBLE"
            color = "#FF6B35"
            analysis = f"Schémas répétitifs avec {predictability_score:.0f}% de prévisibilité et {action_diversity} types d'actions."

        elif predictability_score > 60:
            title = "COMPORTEMENT PARTIELLEMENT LISIBLE"
            color = "#FFD700"
            analysis = f"Prévisibilité modérée à {predictability_score:.0f}% avec diversité de {action_diversity} actions."

        else:
            title = "COMPORTEMENT IMPRÉVISIBLE"
            color = "#00FF80"
            analysis = f"Joueur imprévisible avec {predictability_score:.0f}% de prévisibilité et {action_diversity} types d'actions."

        return {'title': title, 'color': color, 'analysis': analysis}

    def _analyze_tactical_patterns_by_position(self, position, movement_patterns, comfort_zone):
        """Analyse les patterns tactiques spécifiques au poste - Version phrase unique"""
        
        max_pattern = max(movement_patterns.items(), key=lambda x: x[1]) if movement_patterns else ("Aucun", 0)
        total_patterns = sum(movement_patterns.values()) if sum(movement_patterns.values()) > 0 else 1
        dominant_pattern_pct = (max_pattern[1] / total_patterns) * 100
        zone_name, zone_efficiency = comfort_zone
        
        if max_pattern[0] == 'centre_vers_aile' and dominant_pattern_pct > 40:
            title = "SPÉCIALISTE OUVERTURE DU JEU"
            color = "#FF6B35"
            analysis = f"Expert ouverture latérale avec {dominant_pattern_pct:.0f}% d'actions vers l'aile, efficace en {zone_name}."

        elif max_pattern[0] == 'changement_aile' and dominant_pattern_pct > 30:
            title = "MAÎTRE DES RETOURNEMENTS"
            color = "#FFD700"
            analysis = f"Spécialiste changements d'aile ({dominant_pattern_pct:.0f}%) avec vision panoramique développée."

        elif zone_efficiency > 85:
            title = "SPÉCIALISTE ZONAL HAUTE EFFICACITÉ"
            color = "#00FF80"
            analysis = f"Performance exceptionnelle en {zone_name} avec {zone_efficiency:.0f}% d'efficacité."

        else:
            title = "PROFIL TACTIQUE GÉNÉRALISTE"
            color = "#00BFFF"
            analysis = f"Jeu équilibré avec efficacité maximale en {zone_name} ({zone_efficiency:.0f}%)."

        return {'title': title, 'color': color, 'analysis': analysis}
    
    def _analyze_risk_tolerance_by_position(self, position, forward_pct, backward_pct, lateral_pct):
        """Analyse la tolérance au risque selon le poste - Version phrase unique avec position normalisée"""
        # CORRECTION: Récupérer la position dominante
        dominant_position = self._get_dominant_position(position)
        normalized_position = self._normalize_position(dominant_position)

        # Seuils de risque attendus par poste normalisé
        position_risk_expectations = {
            'GK': {'safe_threshold': 80, 'risky_threshold': 15},
            'CB': {'safe_threshold': 70, 'risky_threshold': 25}, 'LCB': {'safe_threshold': 70, 'risky_threshold': 25}, 'RCB': {'safe_threshold': 70, 'risky_threshold': 25},
            'LB': {'safe_threshold': 45, 'risky_threshold': 40}, 'RB': {'safe_threshold': 45, 'risky_threshold': 40},
            'DMC': {'safe_threshold': 60, 'risky_threshold': 30}, 'DM': {'safe_threshold': 60, 'risky_threshold': 30},
            'MC': {'safe_threshold': 40, 'risky_threshold': 45}, 'CM': {'safe_threshold': 40, 'risky_threshold': 45},
            'AMC': {'safe_threshold': 25, 'risky_threshold': 60}, 'CAM': {'safe_threshold': 25, 'risky_threshold': 60},
            'LW': {'safe_threshold': 20, 'risky_threshold': 65}, 'RW': {'safe_threshold': 20, 'risky_threshold': 65},
            'CF': {'safe_threshold': 30, 'risky_threshold': 55}, 'ST': {'safe_threshold': 30, 'risky_threshold': 55}
        }

        expectations = position_risk_expectations.get(normalized_position, {'safe_threshold': 50, 'risky_threshold': 40})

        if forward_pct > expectations['risky_threshold']:
            title = "PROFIL PROGRESSISTE SELON POSTE"
            color = "#00FF80"
            analysis = f"Joueur offensif avec {forward_pct:.0f}% de passes progressives, au-dessus du standard {normalized_position}."

        elif backward_pct > expectations['safe_threshold']:
            title = "PROFIL SÉCURITAIRE ADAPTÉ"
            color = "#FFD700"
            analysis = f"Approche disciplinée avec {backward_pct:.0f}% de passes sécuritaires, conforme aux exigences du poste."

        else:
            title = "PROFIL ÉQUILIBRÉ RISQUE-SÉCURITÉ"
            color = "#FF0080"
            analysis = f"Équilibre optimal entre passes progressives ({forward_pct:.0f}%) et sécuritaires ({backward_pct:.0f}%)."

        return {'title': title, 'color': color, 'analysis': analysis}

    # ===== ANALYSES SUPPLÉMENTAIRES SIMPLIFIÉES =====

    def _analyze_mobility_simple(self, mobility_score):
        """Analyse de mobilité - Version phrase unique"""
        
        if mobility_score > 25:
            title = "TRÈS MOBILE"
            color = "#FF0080"
            analysis = f"Joueur très mobile (score {mobility_score:.1f}) couvrant énormément d'espace sur le terrain."

        elif mobility_score > 15:
            title = "MOBILE"
            color = "#FFD700"
            analysis = f"Bonne mobilité (score {mobility_score:.1f}) avec déplacements réguliers sur le terrain."

        else:
            title = "POSITIONNEL"
            color = "#00BFFF"
            analysis = f"Joueur stable (score {mobility_score:.1f}) maîtrisant parfaitement sa zone de jeu."

        return {'title': title, 'color': color, 'analysis': analysis}

    def _analyze_pressure_resistance_simple(self, pressure_efficiency, normal_efficiency):
        """Analyse de résistance à la pression - Version phrase unique"""
        diff = pressure_efficiency - normal_efficiency

        if diff > 5:
            title = "RÉSISTANCE EXCEPTIONNELLE AU STRESS"
            color = "#00FF00"
            analysis = f"Performance supérieure sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%), mental d'exception."

        elif diff > -5:
            title = "RÉSISTANCE STABLE AU STRESS"
            color = "#FFD700"
            analysis = f"Maintien du niveau sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%), profil stable."

        else:
            title = "FRAGILITÉ SOUS CONTRAINTE"
            color = "#FF6B35"
            analysis = f"Baisse notable sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%), à améliorer."

        return {'title': title, 'color': color, 'analysis': analysis}

    def _analyze_efficiency_simple(self, efficiency_rate, total_actions, position):
        """Analyse d'efficacité globale - Version phrase unique"""
        
        # Seuils adaptatifs selon le poste
        if position in ['GK', 'CB', 'LCB', 'RCB']:
            excellent_threshold = 85
        elif position in ['MC', 'CM', 'DMC', 'DM']:
            excellent_threshold = 80
        else:
            excellent_threshold = 75

        if efficiency_rate > excellent_threshold:
            title = "EFFICACITÉ EXCEPTIONNELLE"
            color = "#00FF00"
            analysis = f"Performance remarquable avec {efficiency_rate:.0f}% d'efficacité sur {total_actions} actions."

        elif efficiency_rate > excellent_threshold - 15:
            title = "EFFICACITÉ SATISFAISANTE"
            color = "#FFD700"
            analysis = f"Niveau correct avec {efficiency_rate:.0f}% d'efficacité technique sur {total_actions} actions."

        else:
            title = "EFFICACITÉ INSUFFISANTE"
            color = "#FF6B35"
            analysis = f"Performance en-deçà des attentes avec {efficiency_rate:.0f}% sur {total_actions} actions."

        return {'title': title, 'color': color, 'analysis': analysis}

    def _analyze_zone_adaptability_simple(self, zone_efficiency, comfort_zone):
        """Analyse de l'adaptabilité zonale - Version phrase unique"""
        zone_name, zone_perf = comfort_zone
        effective_zones = len([z for z, eff in zone_efficiency.items() if eff > 70]) if zone_efficiency else 0
        total_zones = len(zone_efficiency) if zone_efficiency else 0
        
        if effective_zones == total_zones and total_zones > 2:
            title = "POLYVALENCE ZONALE TOTALE"
            color = "#00FF00"
            analysis = f"Efficace sur toutes les zones ({effective_zones}/{total_zones}), polyvalence spatiale précieuse."

        elif effective_zones > 1:
            title = "ADAPTABILITÉ ZONALE CORRECTE"
            color = "#FFD700"
            analysis = f"Efficace sur {effective_zones}/{total_zones} zones, spécialisation en {zone_name} ({zone_perf:.0f}%)."

        else:
            title = "SPÉCIALISATION ZONALE MARQUÉE"
            color = "#FF6B35"
            analysis = f"Efficace principalement en {zone_name} ({zone_perf:.0f}%), spécialisation spatiale nette."

        return {'title': title, 'color': color, 'analysis': analysis}

    def _analyze_action_diversity_simple(self, action_diversity, total_actions):
        """Analyse de la diversité d'actions - Version phrase unique"""
        
        if action_diversity > 8:
            title = "RÉPERTOIRE TRÈS RICHE"
            color = "#00FF00"
            analysis = f"Polyvalence technique remarquable avec {action_diversity} types d'actions sur {total_actions} totales."

        elif action_diversity > 6:
            title = "RÉPERTOIRE ÉQUILIBRÉ"
            color = "#FFD700"
            analysis = f"Répertoire adapté avec {action_diversity} types d'actions différentes."

        else:
            title = "RÉPERTOIRE LIMITÉ"
            color = "#FF6B35"
            analysis = f"Spécialisation marquée avec seulement {action_diversity} types d'actions."

        return {'title': title, 'color': color, 'analysis': analysis}
































































































































    # ===== SYSTÈME DE BOÎTES EXPLICATIVES ULTRA-FLEXIBLE =====

    def create_explanation_box(self, ax, x, y, width, height, title, main_stat, explanation, color):
        """
        Fonction optimisée pour créer des boîtes explicatives ultra-flexibles - VERSION AGRANDIE
        """

        # Rectangle de fond principal
        rect = plt.Rectangle((x, y), width, height, facecolor='black', alpha=0.9, 
                        edgecolor=color, linewidth=3, transform=ax.transAxes)
        ax.add_patch(rect)

        # EN-TÊTE COLORÉ
        header_height = 0.14  # Légèrement augmenté pour le texte plus grand
        title_rect = plt.Rectangle((x, y + height - header_height), width, header_height, 
                                facecolor=color, alpha=0.85, transform=ax.transAxes)
        ax.add_patch(title_rect)

        # TITRE dans l'en-tête
        title_fontsize = 18 if len(title) <= 20 else 16
        ax.text(x + width/2, y + height - header_height/2, title, fontsize=title_fontsize, 
            color='white', fontweight='bold', ha='center', va='center', transform=ax.transAxes)

        # STATISTIQUE PRINCIPALE
        stat_y_position = y + height - header_height - 0.13
        stat_fontsize = 26 if len(main_stat) < 15 else 22
        ax.text(x + width/2, stat_y_position, main_stat, fontsize=stat_fontsize, 
            color='white', fontweight='bold', ha='center', va='center', transform=ax.transAxes)

        # TEXTE D'INTERPRÉTATION
        processed_text = self._process_explanation_text_full(explanation, width)
        text_y_position = y + height * 0.34  # Ajusté pour garder un bon équilibre
        ax.text(x + width/2, text_y_position, processed_text, fontsize=18, color='white', 
            fontweight='bold', ha='center', va='center', transform=ax.transAxes,
            linespacing=1.4)


    def _process_explanation_text_full(self, explanation, box_width):
        """
        Version améliorée qui évite la troncature en "..." et optimise pour des boîtes plus grandes

        Paramètres:
        - explanation: texte brut à traiter
        - box_width: largeur de la boîte pour calculer la limite de caractères

        Retourne: texte formaté optimisé SANS troncature
        """

        # Calcul dynamique SANS limite stricte de lignes
        if box_width <= 0.25:  # Boîte étroite
            char_limit = 25
        elif box_width <= 0.35:  # Boîte moyenne
            char_limit = 35
        else:  # Boîte large
            char_limit = 45

        # Séparer les lignes pré-formatées
        lines = explanation.split('\n')
        processed_lines = []

        for line in lines:
            line = line.strip()  # Supprimer espaces en début/fin

            if not line:  # Ligne vide = saut de ligne intentionnel
                processed_lines.append("")
                continue

            # Si la ligne dépasse la limite, la découper intelligemment
            if len(line) > char_limit:
                words = line.split(' ')
                current_line = ""

                for word in words:
                    # Test si ajouter ce mot dépasse la limite
                    test_line = current_line + (" " + word if current_line else word)

                    if len(test_line) <= char_limit:
                        current_line = test_line
                    else:
                        # Sauvegarder la ligne actuelle et commencer une nouvelle
                        if current_line:
                            processed_lines.append(current_line)
                        current_line = word

                # Ajouter la dernière ligne
                if current_line:
                    processed_lines.append(current_line)
            else:
                processed_lines.append(line)

        # SUPPRESSION de la limitation du nombre de lignes - tout le texte s'affiche
        return '\n'.join(processed_lines)


    # ===== FONCTIONS D'AIDE POUR GÉNÉRER DU CONTENU INTELLIGENT =====

    def _evaluate_performance_level(self, percentage):
        """Évalue un pourcentage et retourne niveau + couleur"""
        if percentage >= 85:
            return "EXCEPTIONNEL", "#00FF00"
        elif percentage >= 75:
            return "EXCELLENT", "#7FFF00"
        elif percentage >= 65:
            return "TRÈS BON", "#FFD700"
        elif percentage >= 55:
            return "BON", "#FFA500"
        elif percentage >= 45:
            return "MOYEN", "#FF6347"
        else:
            return "FAIBLE", "#FF0000"

    def _evaluate_frequency_level(self, count, total):
        """Évalue une fréquence et retourne niveau + couleur"""
        ratio = (count / total * 100) if total > 0 else 0

        if ratio >= 70:
            return "TRÈS FRÉQUENT", ratio, "#FF0080"
        elif ratio >= 50:
            return "FRÉQUENT", ratio, "#FF6B35"
        elif ratio >= 30:
            return "MODÉRÉ", ratio, "#FFD700"
        elif ratio >= 15:
            return "OCCASIONNEL", ratio, "#00BFFF"
        else:
            return "RARE", ratio, "#00FF80"

    def _evaluate_mobility_level(self, mobility_score):
        """Évalue la mobilité et retourne niveau + couleur + interprétation"""
        if mobility_score > 30:
            level = "TRÈS MOBILE"
            color = "#FF0080"
            interpretation = f"Se déplace énormément sur le terrain (score: {mobility_score:.1f}). Joueur imprévisible qui couvre beaucoup d'espace. Difficile à marquer car change constamment de position."
        elif mobility_score > 20:
            level = "MOBILE"
            color = "#FFD700"
            interpretation = f"Bouge régulièrement de position (score: {mobility_score:.1f}). Bon équilibre entre stabilité positionnelle et mouvement. Apporte de la variété au jeu."
        elif mobility_score > 10:
            level = "POSITIONNEL"
            color = "#00BFFF"
            interpretation = f"Reste principalement dans sa zone (score: {mobility_score:.1f}). Joueur stable qui maîtrise bien son secteur. Fiable dans son positionnement."
        else:
            level = "TRÈS STATIQUE"
            color = "#00FF80"
            interpretation = f"Position très fixe sur le terrain (score: {mobility_score:.1f}). Spécialiste de sa zone, très prévisible mais solide dans son rôle."

        return level, color, interpretation

    def _generate_tactical_interpretation(self, forward_pct, lateral_pct, backward_pct):
        """Génère une interprétation tactique basée sur les directions de passes"""

        if forward_pct > 60:
            style = "PROGRESSISTE"
            color = "#00FF80"
            interpretation = f"Cherche constamment la progression ({forward_pct:.0f}% vers l'avant). Joueur offensif qui prend des risques pour faire avancer l'équipe. Créateur d'occasions mais parfois imprécis."
        elif forward_pct > 45:
            style = "ÉQUILIBRÉ"
            color = "#FFD700"
            interpretation = f"Mélange progression et sécurité ({forward_pct:.0f}% avant, {lateral_pct:.0f}% latéral). Vision tactique mature, adapte son jeu selon les situations."
        elif lateral_pct > 50:
            style = "CONSERVATEUR"
            color = "#00BFFF"
            interpretation = f"Privilégie la conservation ({lateral_pct:.0f}% latéral, {backward_pct:.0f}% arrière). Joueur sûr qui évite les pertes de balle, excellent pour garder le contrôle."
        else:
            style = "SÉCURITAIRE"
            color = "#FF6B35"
            interpretation = f"Joue très prudemment ({backward_pct:.0f}% vers l'arrière). Défenseur ou milieu défensif qui sécurise le jeu. Très peu de pertes de balle."

        return style, color, interpretation

    def _analyze_pressure_resistance(self, pressure_efficiency, normal_efficiency):
        """Analyse la résistance à la pression"""
        diff = pressure_efficiency - normal_efficiency

        if diff > 10:
            level = "CLUTCH"
            color = "#00FF00"
            interpretation = f"Encore plus fort sous pression ! ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}% normal). Joueur exceptionnel qui élève son niveau dans les moments difficiles. Mental d'acier."
        elif diff > 0:
            level = "SOLIDE"
            color = "#7FFF00"
            interpretation = f"Maintient son niveau sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%). Fiable dans les moments chauds, ne craque pas mentalement."
        elif diff > -5:
            level = "STABLE"
            color = "#FFD700"
            interpretation = f"Légère baisse sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%). Performance honorable mais peut progresser mentalement."
        elif diff > -15:
            level = "FRAGILE"
            color = "#FFA500"
            interpretation = f"Efficacité réduite sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%). Doit travailler sa gestion du stress et la prise de décision rapide."
        else:
            level = "TRÈS FRAGILE"
            color = "#FF0000"
            interpretation = f"S'effondre sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%). Problème mental majeur, évite les situations de stress."

        return level, color, interpretation

    # ===== FONCTION UTILITAIRE AMÉLIORÉE =====

    def generate_advanced_analysis_suite(self, save_dir="advanced_analysis"):
        """Génère toutes les analyses avancées d'un coup - Version améliorée"""
        import os

        os.makedirs(save_dir, exist_ok=True)
        player_name_clean = self.player_data['player_name'].replace(' ', '_')

        print(f"Génération de la suite d'analyses avancées pour {self.player_data['player_name']}...")

        try:
            # 1. Analyse spatiale
            spatial_path = os.path.join(save_dir, f"{player_name_clean}_spatial_intelligence.png")
            self.plot_positional_intelligence(spatial_path)
            print("✅ Analyse spatiale générée")

            # 2. Analyse de pression
            pressure_path = os.path.join(save_dir, f"{player_name_clean}_pressure_analysis.png")
            self.plot_pressure_analysis(pressure_path)
            print("✅ Analyse de pression générée")

            # 3. Analyse prédictive
            prediction_path = os.path.join(save_dir, f"{player_name_clean}_predictive_analysis.png")
            self.plot_next_action_prediction(prediction_path)
            print("✅ Analyse prédictive générée")

            print(f"🎉 Suite d'analyses complète disponible dans: {save_dir}")

            return {
                "spatial": spatial_path,
                "pressure": pressure_path, 
                "predictive": prediction_path
            }

        except Exception as e:
            print(f"❌ Erreur lors de la génération: {e}")
            return None

    # ===== FONCTION BONUS AMÉLIORÉE =====

    def compare_players_advanced_metrics(self, other_players_data, save_path):
        """Compare les métriques avancées entre plusieurs joueurs - Version ultra-stylisée"""

        def extract_player_metrics(player_data):
            """Extrait les métriques clés d'un joueur"""
            events = player_data.get('events', [])
            if not events:
                return None

            # Métriques de base
            total_actions = len(events)
            successful_actions = len([e for e in events if e.get('outcomeType', {}).get('displayName') == 'Successful'])
            success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0

            # Analyse de pression (simplifié)
            pressure_events = 0
            for i, event in enumerate(events):
                current_time = event['minute'] * 60 + event.get('second', 0)
                for j in range(max(0, i-5), i):
                    prev_time = events[j]['minute'] * 60 + events[j].get('second', 0)
                    if current_time - prev_time <= 3:
                        pressure_events += 1
                        break
                    
            pressure_ratio = (pressure_events / total_actions * 100) if total_actions > 0 else 0

            # Diversité d'actions
            action_diversity = len(set([e['type']['displayName'] for e in events]))

            # Zone de confort (efficacité par zone)
            zones = {'Défensive': [], 'Milieu': [], 'Offensive': []}
            for event in events:
                if 'x' in event and 'y' in event:
                    y = event['y']
                    zone = 'Défensive' if y < 33 else 'Milieu' if y < 66 else 'Offensive'
                    zones[zone].append(event)

            zone_efficiencies = {}
            for zone, zone_events in zones.items():
                if zone_events:
                    successful = len([e for e in zone_events if e.get('outcomeType', {}).get('displayName') == 'Successful'])
                    zone_efficiencies[zone] = (successful / len(zone_events)) * 100
                else:
                    zone_efficiencies[zone] = 0

            best_zone_efficiency = max(zone_efficiencies.values()) if zone_efficiencies else 0

            return {
                'name': player_data.get('player_name', 'Unknown'),
                'total_actions': total_actions,
                'success_rate': success_rate,
                'pressure_ratio': pressure_ratio,
                'action_diversity': action_diversity,
                'best_zone_efficiency': best_zone_efficiency
            }

        # Extraire les métriques pour tous les joueurs
        all_players = [self.player_data] + other_players_data
        players_metrics = []

        for player_data in all_players:
            metrics = extract_player_metrics(player_data)
            if metrics:
                players_metrics.append(metrics)

        if len(players_metrics) < 2:
            print("Pas assez de joueurs pour la comparaison")
            return

        # Créer la visualisation comparative ultra-stylisée
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        fig = plt.figure(figsize=(18, 12))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        gs = GridSpec(3, 2, height_ratios=[1, 2, 2])

        # Titre ultra-stylisé
        ax.text(0.5, 0.95, "COMPARAISON MULTI-JOUEURS AVANCÉE", 
                fontsize=28, color='white', fontweight='bold', ha='center', transform=ax.transAxes)

        # ===== RADAR CHART COMPARATIF =====
        ax_radar = fig.add_subplot(gs[1, 0], projection='polar')
        ax_radar.set_facecolor('none')

        # Préparer les données du radar
        metrics_names = ['Efficacité', 'Résistance', 'Diversité', 'Zone Max', 'Volume']
        angles = np.linspace(0, 2 * np.pi, len(metrics_names), endpoint=False).tolist()
        angles += angles[:1]  # Fermer le cercle

        colors = ['#FF6B35', '#00FF80', '#FFD700', '#FF0080', '#00BFFF']

        for i, player_metrics in enumerate(players_metrics[:5]):  # Max 5 joueurs
            # Normaliser les métriques (0-100)
            values = [
                player_metrics['success_rate'],
                100 - player_metrics['pressure_ratio'],  # Inverser car moins de pression = mieux
                min(100, player_metrics['action_diversity'] * 10),  # Normaliser diversité
                player_metrics['best_zone_efficiency'],
                min(100, player_metrics['total_actions'] / 2)  # Normaliser volume
            ]
            values += values[:1]  # Fermer le cercle

            ax_radar.plot(angles, values, 'o-', linewidth=4, label=player_metrics['name'], 
                        color=colors[i], markersize=8)
            ax_radar.fill(angles, values, alpha=0.25, color=colors[i])

        ax_radar.set_xticks(angles[:-1])
        ax_radar.set_xticklabels(metrics_names, color='white', fontsize=12, fontweight='bold')
        ax_radar.set_ylim(0, 100)
        ax_radar.grid(True, alpha=0.3, color='white')

        # Légende avec fond noir
        legend_radar = ax_radar.legend(loc='upper right', bbox_to_anchor=(1, 1), fontsize=12,
                                    frameon=True, facecolor='black', edgecolor='white')
        for text in legend_radar.get_texts():
            text.set_color('white')

        ax_radar.set_title('Profils Comparatifs', color='white', fontsize=20, fontweight='bold', pad=30)

        # ===== CLASSEMENT GÉNÉRAL =====
        ax_ranking = fig.add_subplot(gs[1:, 1])
        ax_ranking.axis('off')

        # Calculer un score composite
        for player_metrics in players_metrics:
            composite_score = (
                player_metrics['success_rate'] * 0.3 +
                (100 - player_metrics['pressure_ratio']) * 0.2 +
                min(100, player_metrics['action_diversity'] * 10) * 0.2 +
                player_metrics['best_zone_efficiency'] * 0.2 +
                min(100, player_metrics['total_actions'] / 2) * 0.1
            )
            player_metrics['composite_score'] = composite_score

        # Trier par score composite
        players_metrics.sort(key=lambda x: x['composite_score'], reverse=True)

        # Créer le classement stylisé
        ranking_text = "🏆 CLASSEMENT GÉNÉRAL\n" + "="*50 + "\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]

        for i, player in enumerate(players_metrics):
            medal = medals[i] if i < 5 else f"{i+1}️⃣"

            # Évaluation du score
            score = player['composite_score']
            if score > 85:
                grade = "EXCEPTIONNEL ⭐"
            elif score > 75:
                grade = "EXCELLENT 🔥"
            elif score > 65:
                grade = "TRÈS BON 💪"
            elif score > 55:
                grade = "BON ✅"
            else:
                grade = "MOYEN 📈"

            ranking_text += f"{medal} {player['name']}\n"
            ranking_text += f"     Score: {score:.1f}/100 - {grade}\n"
            ranking_text += f"     Efficacité: {player['success_rate']:.1f}% | "
            ranking_text += f"Actions: {player['total_actions']} | "
            ranking_text += f"Diversité: {player['action_diversity']}\n\n"

        # Créer une boîte stylisée pour le classement
        ranking_box = plt.Rectangle((0.05, 0.1), 0.9, 0.8, facecolor='black', alpha=0.9, 
                                edgecolor='white', linewidth=3, transform=ax_ranking.transAxes)
        ax_ranking.add_patch(ranking_box)

        ax_ranking.text(0.5, 0.5, ranking_text, fontsize=14, color='white', 
                    fontweight='bold', ha='center', va='center', transform=ax_ranking.transAxes,
                    linespacing=1.5)

        # Tag et source ultra-stylisé
        ax.text(0.4, 0.25, f"@TarbouchData", fontsize=30, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()

        return players_metrics





















































































    def plot_positional_intelligence(self, save_path):
        """Analyse du positionnement tactique et de l'intelligence spatiale - Version simplifiée"""
        events = self.player_data.get('events', [])
    
        if not events:
            print(f"Aucun événement trouvé pour {self.player_data['player_name']}.")
            return
    
        # Séparer les phases de jeu
        possession_events = []
        defensive_events = []
    
        for event in events:
            event_type = event['type']['displayName']
            if event_type in ['Pass', 'TakeOn', 'Goal', 'MissedShots', 'SavedShot']:
                possession_events.append(event)
            elif event_type in ['Tackle', 'Interception', 'BallRecovery', 'Clearance']:
                defensive_events.append(event)
    
        # Analyse des zones de prédilection
        all_positions = [(e['x'], e['y']) for e in events if 'x' in e and 'y' in e]
        possession_positions = [(e['x'], e['y']) for e in possession_events if 'x' in e and 'y' in e]
        defensive_positions = [(e['x'], e['y']) for e in defensive_events if 'x' in e and 'y' in e]
    
        # Calcul des centres de gravité
        def calculate_center_of_gravity(positions):
            if not positions:
                return None, None
            avg_x = sum(pos[0] for pos in positions) / len(positions)
            avg_y = sum(pos[1] for pos in positions) / len(positions)
            return avg_x, avg_y
    
        cog_all = calculate_center_of_gravity(all_positions)
        cog_possession = calculate_center_of_gravity(possession_positions)
        cog_defensive = calculate_center_of_gravity(defensive_positions)
    
        # Analyse de la mobilité
        def calculate_mobility_metrics(positions):
            if len(positions) < 2:
                return 0, 0, 0
    
            x_coords = [pos[0] for pos in positions]
            y_coords = [pos[1] for pos in positions]
    
            x_range = max(x_coords) - min(x_coords)
            y_range = max(y_coords) - min(y_coords)
            area_covered = x_range * y_range
    
            # Calcul de la variance pour mesurer la dispersion
            x_var = np.var(x_coords)
            y_var = np.var(y_coords)
            mobility_score = np.sqrt(x_var + y_var)
    
            return x_range, y_range, mobility_score
    
        x_range, y_range, mobility_score = calculate_mobility_metrics(all_positions)
    
        # Analyse de créativité/efficacité pour le 3ème terrain
        def analyze_creativity_efficiency():
            """Analyse la créativité vs efficacité du joueur"""
            creative_actions = 0
            safe_actions = 0
            successful_creative = 0
            successful_safe = 0
    
            for event in events:
                event_type = event['type']['displayName']
                is_successful = event.get('outcomeType', {}).get('displayName') == 'Successful'
    
                # Actions créatives/risquées
                if event_type in ['TakeOn', 'ThroughBall', 'Cross', 'LongPass']:
                    creative_actions += 1
                    if is_successful:
                        successful_creative += 1
                # Actions sûres
                elif event_type in ['Pass', 'ShortPass']:
                    # Analyser la distance si disponible
                    if 'endX' in event and 'endY' in event:
                        distance = np.sqrt((event['endX'] - event['x'])**2 + (event['endY'] - event['y'])**2)
                        if distance < 20:  # Passe courte
                            safe_actions += 1
                            if is_successful:
                                successful_safe += 1
                        else:  # Passe longue = créative
                            creative_actions += 1
                            if is_successful:
                                successful_creative += 1
                    else:
                        safe_actions += 1
                        if is_successful:
                            successful_safe += 1
    
            creative_success_rate = (successful_creative / creative_actions * 100) if creative_actions > 0 else 0
            safe_success_rate = (successful_safe / safe_actions * 100) if safe_actions > 0 else 0
            creativity_ratio = (creative_actions / len(events) * 100) if events else 0
    
            return {
                'creative_actions': creative_actions,
                'safe_actions': safe_actions,
                'creative_success_rate': creative_success_rate,
                'safe_success_rate': safe_success_rate,
                'creativity_ratio': creativity_ratio
            }
    
        creativity_data = analyze_creativity_efficiency()
    
        # Création de la visualisation
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
    
        fig = plt.figure(figsize=(18, 16))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
    
        # GridSpec avec plus d'espace pour les boîtes
        gs = GridSpec(3, 3, height_ratios=[2.5, 1.2, 1.2], width_ratios=[1, 1, 1])
    
        # ===== TERRAIN 1: HEATMAP GLOBALE =====
        pitch1 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=3)
        ax_pitch1 = fig.add_subplot(gs[0, 0])
        pitch1.draw(ax=ax_pitch1)
    
        if all_positions:
            x_coords = [pos[0] for pos in all_positions]
            y_coords = [pos[1] for pos in all_positions]
    
            bin_statistic = pitch1.bin_statistic(x_coords, y_coords, statistic='count', bins=(15, 20))
            bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1.5)
    
            # Heatmap avec dégradé stylisé amélioré
            heatmap_cmap = mcolors.LinearSegmentedColormap.from_list(
                "custom_heat", [(0, 0, 0, 0), (0.1, 0.2, 1, 0.4), (0.8, 0.9, 0.1, 0.7), (1, 0.1, 0.1, 1)], N=100)
            pitch1.heatmap(bin_statistic, ax=ax_pitch1, cmap=heatmap_cmap)
    
            # Centre de gravité global avec style VERT et plus grand
            if cog_all[0] is not None:
                pitch1.scatter(cog_all[0], cog_all[1], s=1000, marker='*', 
                            color='#00FF00', edgecolor='white', linewidth=6, ax=ax_pitch1)
    
        # Légende terrain 1
        legend_elements1 = [
            plt.Line2D([0], [0], marker='*', color='w', label='Position Moyenne', 
                    markerfacecolor='#00FF00', markersize=25, markeredgecolor='white', markeredgewidth=3),
            plt.Rectangle((0, 0), 1, 1, facecolor='red', alpha=0.9, label='Zone d\'Activité Maximale'),
            plt.Rectangle((0, 0), 1, 1, facecolor='yellow', alpha=0.7, label='Zone d\'Activité Élevée'),
            plt.Rectangle((0, 0), 1, 1, facecolor='blue', alpha=0.4, label='Zone d\'Activité Modérée')
        ]
        legend1 = ax_pitch1.legend(handles=legend_elements1, loc='upper right', bbox_to_anchor=(1, 1), 
                        fontsize=12, frameon=True, facecolor='black', edgecolor='white')
        for text in legend1.get_texts():
            text.set_color('white')
    
        ax_pitch1.set_title("Zones d'activité", fontsize=22, color='white', fontweight='bold', pad=20)
    
        # ===== TERRAIN 2: PHASES DE JEU =====
        pitch2 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=3)
        ax_pitch2 = fig.add_subplot(gs[0, 1])
        pitch2.draw(ax=ax_pitch2)
    
        # Positions en possession
        if possession_positions:
            x_poss = [pos[0] for pos in possession_positions]
            y_poss = [pos[1] for pos in possession_positions]
            pitch2.scatter(x_poss, y_poss, s=150, alpha=0.8, color='#00BFFF', 
                        edgecolor='white', linewidth=2.5, ax=ax_pitch2)
    
            if cog_possession[0] is not None:
                pitch2.scatter(cog_possession[0], cog_possession[1], s=800, marker='o', 
                            color='#00BFFF', edgecolor='white', linewidth=5, ax=ax_pitch2)
    
        # Positions défensives
        if defensive_positions:
            x_def = [pos[0] for pos in defensive_positions]
            y_def = [pos[1] for pos in defensive_positions]
            pitch2.scatter(x_def, y_def, s=150, alpha=0.8, color='#FF1493', 
                        edgecolor='white', linewidth=2.5, ax=ax_pitch2)
    
            if cog_defensive[0] is not None:
                pitch2.scatter(cog_defensive[0], cog_defensive[1], s=800, marker='s', 
                            color='#FF1493', edgecolor='white', linewidth=5, ax=ax_pitch2)
    
        # Légende terrain 2
        legend_elements2 = [
            plt.Line2D([0], [0], marker='o', color='w', label='Actions Ballon', 
                    markerfacecolor='#00BFFF', markersize=16, markeredgecolor='white', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', label='Centre Attaque', 
                    markerfacecolor='#00BFFF', markersize=20, markeredgecolor='white', markeredgewidth=3),
            plt.Line2D([0], [0], marker='o', color='w', label='Actions Défense', 
                    markerfacecolor='#FF1493', markersize=16, markeredgecolor='white', markeredgewidth=2),
            plt.Line2D([0], [0], marker='s', color='w', label='Centre Défense', 
                    markerfacecolor='#FF1493', markersize=18, markeredgecolor='white', markeredgewidth=3)
        ]
        legend2 = ax_pitch2.legend(handles=legend_elements2, loc='upper right', bbox_to_anchor=(1, 1), 
                        fontsize=12, frameon=True, facecolor='black', edgecolor='white')
        for text in legend2.get_texts():
            text.set_color('white')
    
        ax_pitch2.set_title("Phases Offensives vs Défensives", fontsize=22, color='white', fontweight='bold', pad=20)
    
        # ===== TERRAIN 3: CRÉATIVITÉ VS EFFICACITÉ =====
        ax_creativity = fig.add_subplot(gs[0, 2])
        ax_creativity.set_facecolor('none')
    
        # Diagramme en barres pour créativité vs sécurité
        categories = ['Actions\nCréatives', 'Actions\nSûres']
        counts = [creativity_data['creative_actions'], creativity_data['safe_actions']]
        success_rates = [creativity_data['creative_success_rate'], creativity_data['safe_success_rate']]
    
        # Barres avec couleurs selon l'efficacité
        colors = []
        for rate in success_rates:
            if rate > 80:
                colors.append('#00FF00')  # Vert - Très efficace
            elif rate > 60:
                colors.append('#FFD700')  # Or - Efficace
            elif rate > 40:
                colors.append('#FF8C00')  # Orange - Moyen
            else:
                colors.append('#FF4500')  # Rouge - Inefficace
    
        bars = ax_creativity.bar(categories, counts, color=colors, alpha=0.9, 
                                 edgecolor='white', linewidth=3)
    
        # Étendre la hauteur de l'axe Y pour éviter que le texte touche le haut
        ax_creativity.set_ylim(top=max(counts) * 1.25)
        ax_creativity.set_title("Créativité du joueur", fontsize=22, color='white', fontweight='bold', pad=20)
    
        # Ajouter les pourcentages de réussite
        for i, (bar, rate) in enumerate(zip(bars, success_rates)):
            ax_creativity.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.05,
                        f'{counts[i]} actions\n{rate:.0f}% réussis', ha='center', va='bottom', 
                        color='white', fontweight='bold', fontsize=12,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.8))
    
        ax_creativity.set_ylabel('Nombre d\'Actions', fontsize=14, color='white', fontweight='bold')
        ax_creativity.tick_params(colors='white', labelsize=12)
        ax_creativity.grid(True, alpha=0.3, color='white')
    
        # ===== MÉTRIQUES TEXTUELLES AVEC ANALYSES SIMPLIFIÉES =====
        # Première ligne de boîtes
        ax_metrics1 = fig.add_subplot(gs[1, :])
        ax_metrics1.axis('off')
        
        # Deuxième ligne de boîtes
        ax_metrics2 = fig.add_subplot(gs[2, :])
        ax_metrics2.axis('off')
    
        # Calculs des métriques de base
        total_events = len(events)
        total_successful = len([e for e in events if e.get('outcomeType', {}).get('displayName') == 'Successful'])
        general_efficiency = (total_successful / total_events * 100) if total_events > 0 else 0
        creativity_ratio = creativity_data['creativity_ratio']
    
        # ANALYSES SIMPLIFIÉES
        # 1. Profil de joueur selon le poste
        style_profile, style_color, style_analysis = self._evaluate_player_style_by_position(self.player_data)
    
        # 2. Analyse de créativité adaptée au poste  
        creativity_level, creativity_color, creativity_interpretation = self._get_position_adapted_creativity_analysis(
            self.player_data, creativity_ratio)
    
        # 3. Analyse d'efficacité simplifiée
        original_position = self.player_data.get('position', 'Unknown')
        position = self._get_dominant_position(original_position)
        normalized_position = self._normalize_position(position)
        
        if position in ['GK', 'CB', 'LCB', 'RCB']:
            excellent_threshold = 85
        elif position in ['MC', 'CM', 'DMC', 'DM']:
            excellent_threshold = 80
        else:
            excellent_threshold = 75
        
        if general_efficiency > excellent_threshold:
            efficiency_level = "EXCEPTIONNELLE"
            efficiency_color = "#00FF00"
            efficiency_interpretation = f"Performance remarquable avec {general_efficiency:.0f}% d'efficacité sur {total_events} actions."
        elif general_efficiency > excellent_threshold - 15:
            efficiency_level = "SATISFAISANTE"
            efficiency_color = "#FFD700"
            efficiency_interpretation = f"Niveau correct avec {general_efficiency:.0f}% d'efficacité technique sur {total_events} actions."
        else:
            efficiency_level = "INSUFFISANTE"
            efficiency_color = "#FF6B35"
            efficiency_interpretation = f"Performance en-deçà des attentes avec {general_efficiency:.0f}% sur {total_events} actions."
    
        # === PREMIÈRE LIGNE DE BOÎTES ===
        box_width = 0.32
        box_height = 0.9
        positions = [0.01, 0.34, 0.67]
    
        # Boîte 1: Profil selon le poste
        self.create_explanation_box(ax_metrics1, positions[0], 0.05, box_width, box_height,
                              style_profile,
                              f"Position: {normalized_position}",
                              style_analysis,
                              style_color)
    
        # Boîte 2: Créativité adaptée au poste
        self.create_explanation_box(ax_metrics1, positions[1], 0.05, box_width, box_height,
                              creativity_level,
                              f"{creativity_ratio:.0f}% Actions Créatives",
                              creativity_interpretation,
                              creativity_color)
    
        # Boîte 3: Efficacité globale
        self.create_explanation_box(ax_metrics1, positions[2], 0.05, box_width, box_height,
                              f"EFFICACITÉ {efficiency_level}",
                              f"{general_efficiency:.0f}% Global",
                              efficiency_interpretation,
                              efficiency_color)
        
        # === DEUXIÈME LIGNE DE BOÎTES ===
        
        # Boîte 4: Mobilité
        if mobility_score > 15:
            mobility_level = "ÉLEVÉE"
            mobility_color = "#00FF00"
            mobility_analysis = f"Joueur très mobile couvrant {x_range:.0f}m en largeur et {y_range:.0f}m en longueur."
        elif mobility_score > 10:
            mobility_level = "MODÉRÉE"
            mobility_color = "#FFD700"
            mobility_analysis = f"Mobilité correcte avec couverture de {x_range:.0f}m x {y_range:.0f}m sur le terrain."
        else:
            mobility_level = "FAIBLE"
            mobility_color = "#FFA500"
            mobility_analysis = f"Joueur positionnel stable dans sa zone avec {mobility_score:.1f} de mobilité."
        
        self.create_explanation_box(ax_metrics2, positions[0], 0.05, box_width, box_height,
                              f"MOBILITÉ {mobility_level}",
                              f"Score: {mobility_score:.1f}",
                              mobility_analysis,
                              mobility_color)
        
        # Boîte 5: Ratio Attaque/Défense
        att_def_ratio = len(possession_events) / len(defensive_events) if defensive_events else float('inf')
        if att_def_ratio > 3:
            ratio_level = "TRÈS OFFENSIF"
            ratio_color = "#FF1493"
            ratio_analysis = f"Joueur très orienté attaque avec {len(possession_events)} actions offensives vs {len(defensive_events)} défensives."
        elif att_def_ratio > 1.5:
            ratio_level = "OFFENSIF"
            ratio_color = "#FF69B4"
            ratio_analysis = f"Profil offensif équilibré avec ratio {att_def_ratio:.1f} entre attaque et défense."
        elif att_def_ratio > 0.7:
            ratio_level = "ÉQUILIBRÉ"
            ratio_color = "#FFD700"
            ratio_analysis = f"Parfait équilibre avec {len(possession_events)} actions offensives et {len(defensive_events)} défensives."
        else:
            ratio_level = "DÉFENSIF"
            ratio_color = "#00BFFF"
            ratio_analysis = f"Profil défensif avec priorité aux actions défensives ({len(defensive_events)} vs {len(possession_events)})."
            
        self.create_explanation_box(ax_metrics2, positions[1], 0.05, box_width, box_height,
                              f"PROFIL {ratio_level}",
                              f"Ratio: {att_def_ratio:.1f}",
                              ratio_analysis,
                              ratio_color)
        
        # Boîte 6: Performance globale
        if general_efficiency > 75 and creativity_ratio > 20:
            performance_level = "EXCELLENT"
            performance_color = "#00FF00"
            performance_analysis = f"Performance globale excellente combinant {general_efficiency:.0f}% d'efficacité et {creativity_ratio:.0f}% de créativité."
        elif general_efficiency > 60 and creativity_ratio > 15:
            performance_level = "TRÈS BON"
            performance_color = "#7FFF00"
            performance_analysis = f"Très bon niveau avec {general_efficiency:.0f}% d'efficacité et créativité modérée."
        elif general_efficiency > 50:
            performance_level = "CORRECT"
            performance_color = "#FFD700"
            performance_analysis = f"Performance correcte avec {general_efficiency:.0f}% d'efficacité sur {total_events} actions."
        else:
            performance_level = "À AMÉLIORER"
            performance_color = "#FFA500"
            performance_analysis = f"Marge de progression avec {general_efficiency:.0f}% d'efficacité à optimiser."
            
        self.create_explanation_box(ax_metrics2, positions[2], 0.05, box_width, box_height,
                              f"PERFORMANCE {performance_level}",
                              f"{total_events} Actions",
                              performance_analysis,
                              performance_color)
    
        # Tag et source stylisé
        ax.text(0.4, 0.48, f"@TarbouchData", fontsize=30, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)
    
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()



    def plot_pressure_analysis(self, save_path):
        """Analyse de la gestion de la pression adverse - Version simplifiée"""
        events = self.player_data.get('events', [])

        if not events:
            print(f"Aucun événement trouvé pour {self.player_data['player_name']}.")
            return

        # Analyser la pression temporelle (actions rapprochées dans le temps)
        pressure_events = []
        normal_events = []

        for i, event in enumerate(events):
            # Vérifier s'il y a une action dans les 3 secondes précédentes
            under_pressure = False
            current_time = event['minute'] * 60 + event.get('second', 0)

            # Chercher dans les événements précédents
            for j in range(max(0, i-5), i):
                prev_time = events[j]['minute'] * 60 + events[j].get('second', 0)
                if current_time - prev_time <= 3:
                    under_pressure = True
                    break
                
            if under_pressure:
                pressure_events.append(event)
            else:
                normal_events.append(event)

        # Analyser l'efficacité sous pression
        def analyze_efficiency(event_list):
            if not event_list:
                return 0, 0, 0

            total = len(event_list)
            successful = len([e for e in event_list if e.get('outcomeType', {}).get('displayName') == 'Successful'])
            failed = total - successful
            efficiency = (successful / total * 100) if total > 0 else 0

            return total, successful, efficiency

        pressure_total, pressure_success, pressure_efficiency = analyze_efficiency(pressure_events)
        normal_total, normal_success, normal_efficiency = analyze_efficiency(normal_events)

        # Analyser les types d'actions sous pression
        pressure_types = {}
        for event in pressure_events:
            event_type = event['type']['displayName']
            pressure_types[event_type] = pressure_types.get(event_type, 0) + 1

        # Analyse spatiale de la pression
        pressure_positions = [(e['x'], e['y']) for e in pressure_events if 'x' in e and 'y' in e]
        normal_positions = [(e['x'], e['y']) for e in normal_events if 'x' in e and 'y' in e]

        # Création de la visualisation
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        fig = plt.figure(figsize=(18, 16))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        # GridSpec modifié pour 3 lignes
        gs = GridSpec(3, 3, height_ratios=[2.5, 1.2, 1.2], width_ratios=[1, 1, 1])

        # ===== TERRAIN 1: ACTIONS SOUS PRESSION =====
        pitch1 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=3)
        ax_pitch1 = fig.add_subplot(gs[0, 0])
        pitch1.draw(ax=ax_pitch1)

        # Actions sous pression avec couleurs très distinctes
        for event in pressure_events:
            if 'x' not in event or 'y' not in event:
                continue
            x, y = event['x'], event['y']
            is_successful = event.get('outcomeType', {}).get('displayName') == 'Successful'

            color = '#00FF00' if is_successful else '#FF0000'  # Vert vif vs Rouge vif
            size = 180 if is_successful else 120
            alpha = 0.9 if is_successful else 0.7

            pitch1.scatter(x, y, s=size, alpha=alpha, color=color, 
                        edgecolor='white', linewidth=3, ax=ax_pitch1)

        # Légende terrain 1
        legend_elements1 = [
            plt.Line2D([0], [0], marker='o', color='w', label='Réussi sous Pression', 
                    markerfacecolor='#00FF00', markersize=20, markeredgecolor='white', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', label='Échoué sous Pression', 
                    markerfacecolor='#FF0000', markersize=18, markeredgecolor='white', markeredgewidth=2)
        ]
        legend1 = ax_pitch1.legend(handles=legend_elements1, loc='upper right', bbox_to_anchor=(1, 1), 
                        fontsize=12, frameon=True, facecolor='black', edgecolor='white')
        for text in legend1.get_texts():
            text.set_color('white')

        ax_pitch1.set_title(f"Sous Pression ({len(pressure_events)} actions)", 
                        fontsize=22, color="#FFFFFF", fontweight='bold', pad=20)

        # ===== TERRAIN 2: ACTIONS NORMALES =====
        pitch2 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=3)
        ax_pitch2 = fig.add_subplot(gs[0, 1])
        pitch2.draw(ax=ax_pitch2)

        # Actions normales avec couleurs très distinctes
        for event in normal_events:
            if 'x' not in event or 'y' not in event:
                continue
            x, y = event['x'], event['y']
            is_successful = event.get('outcomeType', {}).get('displayName') == 'Successful'

            color = '#00BFFF' if is_successful else '#FF8C00'  # Bleu ciel vs Orange
            size = 130 if is_successful else 90
            alpha = 0.8 if is_successful else 0.6

            pitch2.scatter(x, y, s=size, alpha=alpha, color=color, 
                        edgecolor='white', linewidth=2.2, ax=ax_pitch2)

        # Légende terrain 2
        legend_elements2 = [
            plt.Line2D([0], [0], marker='o', color='w', label='Réussi Normal', 
                    markerfacecolor='#00BFFF', markersize=18, markeredgecolor='white', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', label='Échoué Normal', 
                    markerfacecolor='#FF8C00', markersize=16, markeredgecolor='white', markeredgewidth=2)
        ]
        legend2 = ax_pitch2.legend(handles=legend_elements2, loc='upper right', bbox_to_anchor=(1, 1), 
                        fontsize=12, frameon=True, facecolor='black', edgecolor='white')
        for text in legend2.get_texts():
            text.set_color('white')

        ax_pitch2.set_title(f"Conditions Normales ({len(normal_events)} actions)", 
                        fontsize=22, color="#FFFFFF", fontweight='bold', pad=20)

        # ===== TERRAIN 3: HEATMAP COMPARATIVE =====
        pitch3 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=3)
        ax_pitch3 = fig.add_subplot(gs[0, 2])
        pitch3.draw(ax=ax_pitch3)

        # Heatmap des zones de haute pression
        if pressure_positions:
            x_pressure = [pos[0] for pos in pressure_positions]
            y_pressure = [pos[1] for pos in pressure_positions]

            bin_stat_pressure = pitch3.bin_statistic(x_pressure, y_pressure, 
                                                    statistic='count', bins=(12, 16))
            bin_stat_pressure['statistic'] = gaussian_filter(bin_stat_pressure['statistic'], 1.2)

            # Heatmap stylisée pour la pression
            pressure_cmap = mcolors.LinearSegmentedColormap.from_list(
                "pressure_heat", [(0, 0, 0, 0), (1, 1, 0, 0.6), (1, 0.3, 0, 0.8), (1, 0, 0, 1)], N=100)
            pitch3.heatmap(bin_stat_pressure, ax=ax_pitch3, cmap=pressure_cmap)

        # Légende terrain 3
        legend_elements3 = [
            plt.Rectangle((0, 0), 1, 1, facecolor='#FF0000', alpha=0.9, label='Pression Maximale'),
            plt.Rectangle((0, 0), 1, 1, facecolor='#FF6B00', alpha=0.8, label='Pression Élevée'),
            plt.Rectangle((0, 0), 1, 1, facecolor='#FFFF00', alpha=0.6, label='Pression Modérée')
        ]
        legend3 = ax_pitch3.legend(handles=legend_elements3, loc='upper right', bbox_to_anchor=(1, 1), 
                        fontsize=12, frameon=True, facecolor='black', edgecolor='white')
        for text in legend3.get_texts():
            text.set_color('white')

        ax_pitch3.set_title("Zones de Pression", fontsize=22, color="#FFFFFF", fontweight='bold', pad=20)

        # ===== ANALYSES SIMPLIFIÉES DE LA PRESSION =====
        # Première ligne de boîtes
        ax_metrics1 = fig.add_subplot(gs[1, :])
        ax_metrics1.axis('off')

        # Deuxième ligne de boîtes
        ax_metrics2 = fig.add_subplot(gs[2, :])
        ax_metrics2.axis('off')

        # Calculs des métriques simplifiées
        pressure_ratio = (len(pressure_events) / len(events) * 100) if events else 0
        pressure_differential = pressure_efficiency - normal_efficiency
        global_success_rate = ((pressure_success + normal_success) / max(pressure_total + normal_total, 1)) * 100 if (pressure_total + normal_total) > 0 else 0

        # === PREMIÈRE LIGNE DE BOÎTES ===
        box_width = 0.32
        box_height = 0.9
        positions = [0.01, 0.34, 0.67]

        # Boîte 1: Niveau de pression
        if pressure_ratio > 15:
            pressure_level = "ENVIRONNEMENT HAUTE PRESSION"
            pressure_color = "#FF0000"
            pressure_interpretation = f"Joueur très exposé avec {pressure_ratio:.0f}% d'actions sous contrainte temporelle de 3 secondes."
        elif pressure_ratio > 8:
            pressure_level = "PRESSION MODÉRÉE"
            pressure_color = "#FFD700"
            pressure_interpretation = f"Exposition normale avec {pressure_ratio:.0f}% d'actions sous pression selon les standards du poste."
        else:
            pressure_level = "ENVIRONNEMENT PRÉSERVÉ"
            pressure_color = "#00FF80"
            pressure_interpretation = f"Environnement protégé avec seulement {pressure_ratio:.0f}% d'actions sous pression."

        self.create_explanation_box(ax_metrics1, positions[0], 0.05, box_width, box_height,
                              pressure_level,
                              f"{pressure_ratio:.0f}% Actions Pressées",
                              pressure_interpretation,
                              pressure_color)

        # Boîte 2: Résistance mentale
        if pressure_differential > 5:
            resistance_level = "RÉSISTANCE EXCEPTIONNELLE"
            resistance_color = "#00FF00"
            resistance_analysis = f"Performance supérieure sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%), mental d'exception."
        elif pressure_differential > -5:
            resistance_level = "RÉSISTANCE STABLE"
            resistance_color = "#FFD700"
            resistance_analysis = f"Maintien du niveau sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%), profil stable."
        else:
            resistance_level = "FRAGILITÉ SOUS CONTRAINTE"
            resistance_color = "#FF6B35"
            resistance_analysis = f"Baisse notable sous pression ({pressure_efficiency:.0f}% vs {normal_efficiency:.0f}%), à améliorer."

        self.create_explanation_box(ax_metrics1, positions[1], 0.05, box_width, box_height,
                              resistance_level,
                              f"Δ Performance: {pressure_differential:+.1f}%",
                              resistance_analysis,
                              resistance_color)

        # Boîte 3: Performance globale
        if global_success_rate > 85:
            performance_level = "EXCELLENTE"
            performance_color = "#00FF00"
            global_interpretation = f"Performance technique de très haut niveau avec {global_success_rate:.0f}% de réussite globale."
        elif global_success_rate > 70:
            performance_level = "SATISFAISANTE"
            performance_color = "#FFD700"
            global_interpretation = f"Performance technique correcte avec {global_success_rate:.0f}% de réussite sur l'ensemble du match."
        else:
            performance_level = "INSUFFISANTE"
            performance_color = "#FF6B35"
            global_interpretation = f"Performance technique perfectible avec {global_success_rate:.0f}% de réussite globale."

        self.create_explanation_box(ax_metrics1, positions[2], 0.05, box_width, box_height,
                              f"PERFORMANCE {performance_level}",
                              f"{global_success_rate:.0f}% Réussite Globale",
                              global_interpretation,
                              performance_color)

        # === DEUXIÈME LIGNE DE BOÎTES ===

        # Boîte 4: Actions dominantes sous pression
        dominant_pressure_action = max(pressure_types.items(), key=lambda x: x[1]) if pressure_types else ("Aucune", 0)
        pressure_action_analysis = f"Action principale sous contrainte: {dominant_pressure_action[0]} répétée {dominant_pressure_action[1]} fois."

        self.create_explanation_box(ax_metrics2, positions[0], 0.05, box_width, box_height,
                              "RÉFLEXES SOUS CONTRAINTE",
                              f"{dominant_pressure_action[0]}",
                              pressure_action_analysis,
                              "#FF1493")

        # Boîte 5: Répartition temporelle
        pressure_minutes = [e['minute'] for e in pressure_events if 'minute' in e]
        if pressure_minutes:
            avg_pressure_minute = sum(pressure_minutes) / len(pressure_minutes)
            if avg_pressure_minute > 60:
                temporal_level = "PRESSION TARDIVE"
                temporal_color = "#FF0000"
                temporal_analysis = f"Pression concentrée en fin de match (minute {avg_pressure_minute:.0f}), gestion de la fatigue cruciale."
            elif avg_pressure_minute > 30:
                temporal_level = "PRESSION MÉDIANE"
                temporal_color = "#FFD700"
                temporal_analysis = f"Pression équilibrée sur le match (minute {avg_pressure_minute:.0f}), adaptation constante nécessaire."
            else:
                temporal_level = "PRESSION PRÉCOCE"
                temporal_color = "#00BFFF"
                temporal_analysis = f"Pression dès l'entame (minute {avg_pressure_minute:.0f}), adaptation rapide réussie."
        else:
            temporal_level = "DONNÉES INSUFFISANTES"
            temporal_color = "#808080"
            temporal_analysis = "Données temporelles insuffisantes pour une analyse précise."
            avg_pressure_minute = 0

        self.create_explanation_box(ax_metrics2, positions[1], 0.05, box_width, box_height,
                              temporal_level,
                              f"Minute moy: {avg_pressure_minute:.0f}" if pressure_minutes else "N/A",
                              temporal_analysis,
                              temporal_color)

        # Boîte 6: Comparaison standards
        # CORRECTION: Récupérer la position dominante
        original_position = self.player_data.get('position', 'Unknown')
        position = self._get_dominant_position(original_position)
        normalized_position = self._normalize_position(position)

        position_pressure_standards = {
            'GK': 12, 'CB': 18, 'LCB': 18, 'RCB': 18, 'LB': 22, 'RB': 22,
            'DMC': 25, 'DM': 25, 'MC': 20, 'CM': 20, 'AMC': 15, 'CAM': 15,
            'LW': 18, 'RW': 18, 'CF': 20, 'ST': 20
        }

        expected_pressure = position_pressure_standards.get(normalized_position, 20)
        pressure_vs_standard = pressure_ratio - expected_pressure

        if pressure_vs_standard > 5:
            standard_level = "AU-DESSUS DES STANDARDS"
            standard_color = "#FF6B35"
            standard_analysis = f"Exposition {pressure_vs_standard:+.1f}% supérieure au standard {normalized_position}, environnement exigeant."
        elif pressure_vs_standard > -3:
            standard_level = "CONFORME AUX STANDARDS"
            standard_color = "#FFD700"
            standard_analysis = f"Niveau de pression conforme aux standards du poste {normalized_position} ({expected_pressure}%)."
        else:
            standard_level = "SOUS LES STANDARDS"
            standard_color = "#00FF80"
            standard_analysis = f"Environnement {abs(pressure_vs_standard):.1f}% moins contraignant que la moyenne {normalized_position}."

        self.create_explanation_box(ax_metrics2, positions[2], 0.05, box_width, box_height,
                              standard_level,
                              f"Standard: {expected_pressure}%",
                              standard_analysis,
                              standard_color)

        # Tag et source stylisé
        ax.text(0.4, 0.23, f"@TarbouchData", fontsize=30, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()

    def plot_next_action_prediction(self, save_path):
        """Analyse des patterns et prévisibilité du joueur - Version simplifiée"""
        events = self.player_data.get('events', [])

        if len(events) < 10:
            print(f"Pas assez d'événements pour l'analyse prédictive de {self.player_data['player_name']}.")
            return

        # Analyser les préférences directionnelles
        directional_preferences = {'forward': 0, 'lateral': 0, 'backward': 0}
        pass_events = [e for e in events if e['type']['displayName'] == 'Pass']

        for pass_event in pass_events:
            if 'endX' in pass_event and 'endY' in pass_event:
                start_y = pass_event['y']
                end_y = pass_event['endY']

                if end_y > start_y + 5:
                    directional_preferences['forward'] += 1
                elif end_y < start_y - 5:
                    directional_preferences['backward'] += 1
                else:
                    directional_preferences['lateral'] += 1

        # Analyser les zones de confort
        zone_actions = defaultdict(list)
        for event in events:
            if 'x' in event and 'y' in event:
                x, y = event['x'], event['y']

                # Définir la zone
                if y < 33:
                    zone = 'Défensive'
                elif y < 66:
                    zone = 'Milieu'
                else:
                    zone = 'Offensive'

                zone_actions[zone].append(event)

        # Calculer l'efficacité par zone
        zone_efficiency = {}
        for zone, zone_events in zone_actions.items():
            if zone_events:
                successful = len([e for e in zone_events if e.get('outcomeType', {}).get('displayName') == 'Successful'])
                zone_efficiency[zone] = (successful / len(zone_events)) * 100

        # Analyser les séquences d'actions pour la prévisibilité
        action_sequences = []
        for i in range(len(events) - 1):
            current_action = events[i]['type']['displayName']
            next_action = events[i + 1]['type']['displayName']
            action_sequences.append((current_action, next_action))

        # Calculer la prévisibilité
        transition_matrix = defaultdict(Counter)

        for current, next_action in action_sequences:
            transition_matrix[current][next_action] += 1

        predictability_score = 0
        for current_action, next_actions in transition_matrix.items():
            if next_actions:
                max_prob = max(next_actions.values()) / sum(next_actions.values())
                predictability_score += max_prob

        predictability_score = (predictability_score / len(transition_matrix)) * 100 if transition_matrix else 0

        # Analyse des mouvements préférentiels
        movement_patterns = {
            'centre_vers_aile': 0,
            'aile_vers_centre': 0,
            'changement_aile': 0,
            'percee_axiale': 0
        }

        for pass_event in pass_events:
            if 'endX' in pass_event and 'endY' in pass_event:
                start_x, start_y = pass_event['x'], pass_event['y']
                end_x, end_y = pass_event['endX'], pass_event['endY']

                # Du centre vers l'aile
                if 33 <= start_x <= 67 and (end_x < 25 or end_x > 75):
                    movement_patterns['centre_vers_aile'] += 1

                # De l'aile vers le centre
                elif (start_x < 25 or start_x > 75) and 33 <= end_x <= 67:
                    movement_patterns['aile_vers_centre'] += 1

                # Changement d'aile
                elif (start_x < 33 and end_x > 67) or (start_x > 67 and end_x < 33):
                    movement_patterns['changement_aile'] += 1

                # Percée dans l'axe
                elif abs(start_x - end_x) < 15 and end_y > start_y + 15:
                    movement_patterns['percee_axiale'] += 1

        # Création de la visualisation
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        fig = plt.figure(figsize=(18, 16))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        # Layout : diagramme circulaire à gauche, patterns de mouvement à droite, 2 lignes de boîtes
        gs = GridSpec(3, 2, height_ratios=[2.5, 1.2, 1.2], width_ratios=[1, 1])

        # ===== DIAGRAMME CIRCULAIRE =====
        ax_directions = fig.add_subplot(gs[0, 0])
        ax_directions.set_facecolor('none')

        # Graphique en secteurs pour les préférences directionnelles
        total_passes = sum(directional_preferences.values())
        if total_passes > 0:
            sizes = [directional_preferences['forward'], 
                    directional_preferences['lateral'], 
                    directional_preferences['backward']]
            colors = ['#00FF80', '#FFD700', '#FF6B35']
            explode = (0.1, 0.05, 0.05)

            wedges, texts, autotexts = ax_directions.pie(sizes, colors=colors, 
                                                        autopct='%1.1f%%', startangle=90, explode=explode,
                                                        textprops={'color': 'white', 'fontsize': 18, 'fontweight': 'bold'},
                                                        wedgeprops=dict(edgecolor='white', linewidth=5))

            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(18)
                autotext.set_bbox(dict(boxstyle='round,pad=0.4', facecolor='black', alpha=0.8, edgecolor='white'))

            # Légende stylisée
            legend_elements_pie = [
                plt.Rectangle((0, 0), 1, 1, facecolor='#00FF80', alpha=0.9, 
                            label=f'Progression ({directional_preferences["forward"]} passes)'),
                plt.Rectangle((0, 0), 1, 1, facecolor='#FFD700', alpha=0.9, 
                            label=f'Latérales ({directional_preferences["lateral"]} passes)'),
                plt.Rectangle((0, 0), 1, 1, facecolor='#FF6B35', alpha=0.9, 
                            label=f'Sécurité ({directional_preferences["backward"]} passes)')
            ]

            legend_pie = ax_directions.legend(handles=legend_elements_pie, loc='upper right', bbox_to_anchor=(1, 1), 
                            fontsize=12, frameon=True, facecolor='black', edgecolor='white')

            for text in legend_pie.get_texts():
                text.set_color('white')
                text.set_fontweight('bold')

            ax_directions.set_title('Distribution Directionnelle', 
                                fontsize=20, color="#FFFFFF", fontweight='bold', pad=20)

        # ===== GRAPHIQUE PATTERNS DE MOUVEMENT =====
        ax_patterns = fig.add_subplot(gs[0, 1])
        ax_patterns.set_facecolor('none')

        pattern_labels = ['Centre→Aile', 'Aile→Centre', 'Chang. Aile', 'Percée Axiale']
        pattern_values = list(movement_patterns.values())
        pattern_colors = ['#FF6B35', '#00FF80', '#FFD700', '#FF0080']

        bars = ax_patterns.bar(pattern_labels, pattern_values, color=pattern_colors, 
                            alpha=0.9, edgecolor='white', linewidth=3)

        ax_patterns.set_ylim(top=max(pattern_values) * 1.25 if max(pattern_values) > 0 else 1)

        total_patterns = sum(pattern_values) if sum(pattern_values) > 0 else 1
        for bar, value in zip(bars, pattern_values):
            percentage = (value / total_patterns) * 100
            ax_patterns.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (max(pattern_values) or 1) * 0.05,
                        f'{value}\n({percentage:.1f}%)', ha='center', va='bottom', 
                        color='white', fontweight='bold', fontsize=12,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.8))

        ax_patterns.set_ylabel('Occurrences', fontsize=14, color='white', fontweight='bold')
        ax_patterns.set_title('Patterns Tactiques', fontsize=17, color="#FFFFFF", fontweight='bold')
        ax_patterns.tick_params(colors='white', labelsize=11)
        ax_patterns.set_xticklabels(pattern_labels, rotation=15, fontweight='bold')
        ax_patterns.grid(True, alpha=0.3, color='white')

        # ===== ANALYSES SIMPLIFIÉES =====
        ax_text1 = fig.add_subplot(gs[1, :])
        ax_text1.axis('off')

        ax_text2 = fig.add_subplot(gs[2, :])
        ax_text2.axis('off')

        # Calculs simplifiés
        action_diversity = len(set([e['type']['displayName'] for e in events]))
        comfort_zone = max(zone_efficiency.items(), key=lambda x: x[1]) if zone_efficiency else ("Aucune", 0)
        forward_pct = (directional_preferences['forward'] / total_passes * 100) if total_passes > 0 else 0
        backward_pct = (directional_preferences['backward'] / total_passes * 100) if total_passes > 0 else 0

        # CORRECTION: Récupérer la position dominante
        original_position = self.player_data.get('position', 'Unknown')
        position = self._get_dominant_position(original_position)

        # Analyses comportementales simplifiées
        risk_tolerance_analysis = self._analyze_risk_tolerance_by_position(original_position, forward_pct, backward_pct, 0)
        predictability_analysis = self._analyze_predictability_by_age_position(position, predictability_score, action_diversity)
        tactical_pattern_analysis = self._analyze_tactical_patterns_by_position(position, movement_patterns, comfort_zone)

        # === PREMIÈRE LIGNE DE BOÎTES ===
        box_width = 0.32
        box_height = 0.9
        positions_box = [0.01, 0.34, 0.67]

        # Boîte 1: Tolérance au risque
        self.create_explanation_box(ax_text1, positions_box[0], 0.05, box_width, box_height,
                            risk_tolerance_analysis['title'],
                            f"{forward_pct:.0f}% Progression",
                            risk_tolerance_analysis['analysis'],
                            risk_tolerance_analysis['color'])

        # Boîte 2: Prévisibilité
        self.create_explanation_box(ax_text1, positions_box[1], 0.05, box_width, box_height,
                            predictability_analysis['title'],
                            f"Score: {predictability_score:.0f}%",
                            predictability_analysis['analysis'],
                            predictability_analysis['color'])

        # Boîte 3: Patterns tactiques
        self.create_explanation_box(ax_text1, positions_box[2], 0.05, box_width, box_height,
                            tactical_pattern_analysis['title'],
                            f"Zone optimale: {comfort_zone[0]}",
                            tactical_pattern_analysis['analysis'],
                            tactical_pattern_analysis['color'])

        # === DEUXIÈME LIGNE DE BOÎTES ===

        # Boîte 4: Diversité d'actions
        if action_diversity > 8:
            diversity_level = "RÉPERTOIRE TRÈS RICHE"
            diversity_color = "#00FF00"
            diversity_analysis = f"Polyvalence technique remarquable avec {action_diversity} types d'actions différentes."
        elif action_diversity > 6:
            diversity_level = "RÉPERTOIRE ÉQUILIBRÉ"
            diversity_color = "#FFD700"
            diversity_analysis = f"Répertoire adapté aux standards du poste avec {action_diversity} types d'actions."
        else:
            diversity_level = "RÉPERTOIRE LIMITÉ"
            diversity_color = "#FF6B35"
            diversity_analysis = f"Spécialisation marquée avec seulement {action_diversity} types d'actions."

        self.create_explanation_box(ax_text2, positions_box[0], 0.05, box_width, box_height,
                              diversity_level,
                              f"{action_diversity} Types d'Actions",
                              diversity_analysis,
                              diversity_color)

        # Boîte 5: Adaptabilité zonale
        zone_adaptability = len([z for z, eff in zone_efficiency.items() if eff > 70]) if zone_efficiency else 0
        total_zones = len(zone_efficiency) if zone_efficiency else 0

        if zone_adaptability == total_zones and total_zones > 2:
            adaptability_level = "POLYVALENCE ZONALE TOTALE"
            adaptability_color = "#00FF00"
            adaptability_analysis = f"Efficace sur toutes les zones ({zone_adaptability}/{total_zones}), polyvalence spatiale précieuse."
        elif zone_adaptability > 1:
            adaptability_level = "ADAPTABILITÉ CORRECTE"
            adaptability_color = "#FFD700"
            adaptability_analysis = f"Efficace sur {zone_adaptability}/{total_zones} zones, spécialisation en {comfort_zone[0]}."
        else:
            adaptability_level = "SPÉCIALISATION MARQUÉE"
            adaptability_color = "#FF6B35"
            adaptability_analysis = f"Efficace principalement en zone {comfort_zone[0]}, profil spécialisé."

        self.create_explanation_box(ax_text2, positions_box[1], 0.05, box_width, box_height,
                              adaptability_level,
                              f"{zone_adaptability}/{total_zones} Zones",
                              adaptability_analysis,
                              adaptability_color)

        # Boîte 6: Séquences d'actions
        max_pattern = max(movement_patterns.items(), key=lambda x: x[1]) if movement_patterns else ("Aucun", 0)
        pattern_dominance = (max_pattern[1] / sum(movement_patterns.values()) * 100) if sum(movement_patterns.values()) > 0 else 0

        if pattern_dominance > 50:
            sequence_level = "SÉQUENCES TRÈS PRÉVISIBLES"
            sequence_color = "#FF0000"
            sequence_analysis = f"Pattern {max_pattern[0]} domine à {pattern_dominance:.0f}%, nécessite plus de diversification."
        elif pattern_dominance > 35:
            sequence_level = "SÉQUENCES LISIBLES"
            sequence_color = "#FFD700"
            sequence_analysis = f"Pattern principal {max_pattern[0]} à {pattern_dominance:.0f}%, diversité présente."
        else:
            sequence_level = "SÉQUENCES IMPRÉVISIBLES"
            sequence_color = "#00FF80"
            sequence_analysis = f"Jeu varié avec pattern dominant à seulement {pattern_dominance:.0f}%."

        self.create_explanation_box(ax_text2, positions_box[2], 0.05, box_width, box_height,
                              sequence_level,
                              f"Dominance: {pattern_dominance:.0f}%",
                              sequence_analysis,
                              sequence_color)

        # Tag et source
        ax.text(0.25, 0.5, f"@TarbouchData", fontsize=30, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()