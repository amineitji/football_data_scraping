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
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  

    def plot_positional_intelligence(self, save_path):
        """Analyse du positionnement tactique et de l'intelligence spatiale - Version améliorée"""
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
    
        # Création de la visualisation
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
    
        fig = plt.figure(figsize=(18, 12))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
    
        gs = GridSpec(2, 3, height_ratios=[3, 1], width_ratios=[1, 1, 1])
    
        # Titre principal avec style amélioré
        ax.text(0.5, 0.96, f"INTELLIGENCE POSITIONNELLE - {self.player_data['player_name']}", 
                fontsize=30, color='white', fontweight='bold', ha='center', transform=ax.transAxes)
    
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
    
        # Légende terrain 1 avec couleurs en blanc
        legend_elements1 = [
            plt.Line2D([0], [0], marker='*', color='w', label='Centre de Gravité Global', 
                    markerfacecolor='#00FF00', markersize=25, markeredgecolor='white', markeredgewidth=3),
            plt.Rectangle((0, 0), 1, 1, facecolor='red', alpha=0.9, label='Zones d\'Activité Maximale'),
            plt.Rectangle((0, 0), 1, 1, facecolor='yellow', alpha=0.7, label='Zones d\'Activité Élevée'),
            plt.Rectangle((0, 0), 1, 1, facecolor='blue', alpha=0.4, label='Zones d\'Activité Modérée')
        ]
        legend1 = ax_pitch1.legend(handles=legend_elements1, loc='upper right', bbox_to_anchor=(1.3, 1), 
                        fontsize=12, frameon=True, facecolor='black', edgecolor='white')
        # Texte des légendes en blanc
        for text in legend1.get_texts():
            text.set_color('white')
    
        ax_pitch1.set_title("Heatmap Globale", fontsize=22, color='white', fontweight='bold', pad=20)
    
        # ===== TERRAIN 2: PHASES DE JEU =====
        pitch2 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=3)
        ax_pitch2 = fig.add_subplot(gs[0, 1])
        pitch2.draw(ax=ax_pitch2)
    
        # Positions en possession avec couleurs distinctes
        if possession_positions:
            x_poss = [pos[0] for pos in possession_positions]
            y_poss = [pos[1] for pos in possession_positions]
            pitch2.scatter(x_poss, y_poss, s=150, alpha=0.8, color='#00BFFF', 
                        edgecolor='white', linewidth=2.5, ax=ax_pitch2)
            
            if cog_possession[0] is not None:
                pitch2.scatter(cog_possession[0], cog_possession[1], s=800, marker='o', 
                            color='#00BFFF', edgecolor='white', linewidth=5, ax=ax_pitch2)
    
        # Positions défensives avec couleurs distinctes
        if defensive_positions:
            x_def = [pos[0] for pos in defensive_positions]
            y_def = [pos[1] for pos in defensive_positions]
            pitch2.scatter(x_def, y_def, s=150, alpha=0.8, color='#FF1493', 
                        edgecolor='white', linewidth=2.5, ax=ax_pitch2)
            
            if cog_defensive[0] is not None:
                pitch2.scatter(cog_defensive[0], cog_defensive[1], s=800, marker='s', 
                            color='#FF1493', edgecolor='white', linewidth=5, ax=ax_pitch2)
    
        # Légende terrain 2 avec couleurs distinctes
        legend_elements2 = [
            plt.Line2D([0], [0], marker='o', color='w', label='Actions Offensives', 
                    markerfacecolor='#00BFFF', markersize=16, markeredgecolor='white', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', label='Centre Gravité Offensif', 
                    markerfacecolor='#00BFFF', markersize=20, markeredgecolor='white', markeredgewidth=3),
            plt.Line2D([0], [0], marker='o', color='w', label='Actions Défensives', 
                    markerfacecolor='#FF1493', markersize=16, markeredgecolor='white', markeredgewidth=2),
            plt.Line2D([0], [0], marker='s', color='w', label='Centre Gravité Défensif', 
                    markerfacecolor='#FF1493', markersize=18, markeredgecolor='white', markeredgewidth=3)
        ]
        legend2 = ax_pitch2.legend(handles=legend_elements2, loc='upper right', bbox_to_anchor=(1.35, 1), 
                        fontsize=12, frameon=True, facecolor='black', edgecolor='white')
        # Texte des légendes en blanc
        for text in legend2.get_texts():
            text.set_color('white')
    
        ax_pitch2.set_title("Phases de Jeu", fontsize=22, color='white', fontweight='bold', pad=20)
    
        # ===== TERRAIN 3: ZONES TACTIQUES (CORRIGÉ POUR VERTICAL PITCH) =====
        pitch3 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=3)
        ax_pitch3 = fig.add_subplot(gs[0, 2])
        pitch3.draw(ax=ax_pitch3)
    
        # Compter les actions par zone tactique - CORRIGÉ pour vertical pitch avec rotation 90°
        zone_counts = {}
        zone_colors = {
            'Zone de finition': '#FF0080',      # Rose vif
            'Milieu offensif': '#00FF80',       # Vert lime
            'Milieu défensif': '#FFD700',       # Or
            'Défense centrale': '#0080FF',      # Bleu vif
            'Couloirs': '#FF8000',              # Orange
            'Défense latérale': '#8000FF'       # Violet
        }
    
        for event in events:
            if 'x' not in event or 'y' not in event:
                continue
            x, y = event['x'], event['y']
            
            # Classification des zones CORRIGÉE avec rotation 90° - Zone finition à DROITE
            if 80 <= x <= 100 and 30 <= y <= 70:  # Zone de finition à DROITE
                zone = 'Zone de finition'
            elif 60 <= x < 80 and 30 <= y <= 70:  # Milieu offensif
                zone = 'Milieu offensif'
            elif 40 <= x < 60 and 30 <= y <= 70:  # Milieu défensif
                zone = 'Milieu défensif'
            elif 0 <= x < 40 and 30 <= y <= 70:   # Défense centrale à GAUCHE
                zone = 'Défense centrale'
            elif x >= 40 and (0 <= y < 30 or 70 < y <= 100):  # Couloirs haut et bas
                zone = 'Couloirs'
            else:
                zone = 'Défense latérale'
                
            zone_counts[zone] = zone_counts.get(zone, 0) + 1
    
        # Affichage avec code couleur par zone - ROTATION 90°
        for event in events:
            if 'x' not in event or 'y' not in event:
                continue
            x, y = event['x'], event['y']
            
            # Déterminer la zone CORRIGÉE avec rotation 90°
            if 80 <= x <= 100 and 30 <= y <= 70:
                color = zone_colors['Zone de finition']
            elif 60 <= x < 80 and 30 <= y <= 70:
                color = zone_colors['Milieu offensif']
            elif 40 <= x < 60 and 30 <= y <= 70:
                color = zone_colors['Milieu défensif']
            elif 0 <= x < 40 and 30 <= y <= 70:
                color = zone_colors['Défense centrale']
            elif x >= 40 and (0 <= y < 30 or 70 < y <= 100):
                color = zone_colors['Couloirs']
            else:
                color = zone_colors['Défense latérale']
            
            pitch3.scatter(x, y, s=120, alpha=0.8, color=color, 
                        edgecolor='white', linewidth=1.5, ax=ax_pitch3)
    
        # Légende terrain 3 avec couleurs très variées
        legend_elements3 = [
            plt.Line2D([0], [0], marker='o', color='w', label='Zone de Finition', 
                    markerfacecolor='#FF0080', markersize=14),
            plt.Line2D([0], [0], marker='o', color='w', label='Milieu Offensif', 
                    markerfacecolor='#00FF80', markersize=14),
            plt.Line2D([0], [0], marker='o', color='w', label='Milieu Défensif', 
                    markerfacecolor='#FFD700', markersize=14),
            plt.Line2D([0], [0], marker='o', color='w', label='Défense Centrale', 
                    markerfacecolor='#0080FF', markersize=14),
            plt.Line2D([0], [0], marker='o', color='w', label='Couloirs', 
                    markerfacecolor='#FF8000', markersize=14),
            plt.Line2D([0], [0], marker='o', color='w', label='Défense Latérale', 
                    markerfacecolor='#8000FF', markersize=14)
        ]
        legend3 = ax_pitch3.legend(handles=legend_elements3, loc='upper right', bbox_to_anchor=(1.4, 1), 
                        fontsize=11, frameon=True, facecolor='black', edgecolor='white', ncol=1)
        # Texte des légendes en blanc
        for text in legend3.get_texts():
            text.set_color('white')
    
        ax_pitch3.set_title("Répartition Tactique", fontsize=22, color='white', fontweight='bold', pad=20)
    
        # ===== MÉTRIQUES TEXTUELLES STYLISÉES =====
        ax_metrics = fig.add_subplot(gs[1, :])
        ax_metrics.axis('off')
    
        # Calculs des métriques avancées
        total_events = len(events)
        
        # Zone dominante
        if zone_counts:
            dominant_zone = max(zone_counts.items(), key=lambda x: x[1])
            dominant_percentage = (dominant_zone[1] / total_events) * 100
        else:
            dominant_zone = ("Aucune", 0)
            dominant_percentage = 0
    
        # Analyse du profil tactique
        if zone_counts:
            defensive_actions = zone_counts.get('Défense centrale', 0) + zone_counts.get('Défense latérale', 0)
            midfield_actions = zone_counts.get('Milieu défensif', 0) + zone_counts.get('Milieu offensif', 0)
            attacking_actions = zone_counts.get('Zone de finition', 0) + zone_counts.get('Couloirs', 0)
            
            defensive_pct = (defensive_actions / total_events) * 100
            midfield_pct = (midfield_actions / total_events) * 100
            attacking_pct = (attacking_actions / total_events) * 100
        else:
            defensive_pct = midfield_pct = attacking_pct = 0
    
        # Évaluation du profil
        if attacking_pct > 40:
            profil_tactique = "ATTAQUANT PUR"
            profil_color = '#FF0080'
        elif defensive_pct > 40:
            profil_tactique = "DÉFENSEUR SOLIDE"
            profil_color = '#0080FF'
        else:
            profil_tactique = "JOUEUR COMPLET"
            profil_color = '#00FF80'
    
        # Métriques de mobilité
        if mobility_score > 25:
            mobilite_evaluation = "ULTRA MOBILE"
            mobilite_color = '#FF0080'
        elif mobility_score > 15:    
            mobilite_evaluation = "MOBILE"
            mobilite_color = '#FFD700'
        else:
            mobilite_evaluation = "POSITIONNEL"
            mobilite_color = '#0080FF'
    
        # Création des boîtes stylisées pour le texte
        def create_text_box(ax, x, y, width, height, title, content, title_color, bg_color='black'):
            # Rectangle de fond
            rect = plt.Rectangle((x, y), width, height, facecolor=bg_color, alpha=0.8, 
                            edgecolor='white', linewidth=2, transform=ax.transAxes)
            ax.add_patch(rect)
            
            # Titre coloré
            ax.text(x + width/2, y + height - 0.05, title, fontsize=18, color=title_color, 
                fontweight='bold', ha='center', va='top', transform=ax.transAxes)
            
            # Contenu
            ax.text(x + width/2, y + height/2 - 0.02, content, fontsize=16, color='white', 
                fontweight='bold', ha='center', va='center', transform=ax.transAxes)
    
        # Boîte 1: Positionnement
        content1 = f"""Centre de Gravité Global:
    X: {cog_all[0]:.1f}m  |  Y: {cog_all[1]:.1f}m
    
    Couverture Terrain:
    {x_range:.1f}m × {y_range:.1f}m
    
    {mobilite_evaluation}
    Score: {mobility_score:.1f}"""
    
        create_text_box(ax_metrics, 0.02, 0.1, 0.28, 0.8, "POSITIONNEMENT", content1, '#00FF80')
    
        # Boîte 2: Profil tactique
        content2 = f"""{profil_tactique}
    
    Défense: {defensive_pct:.0f}%
    Milieu: {midfield_pct:.0f}%
    Attaque: {attacking_pct:.0f}%
    
    Zone Dominante:
    {dominant_zone[0]} ({dominant_percentage:.0f}%)"""
    
        create_text_box(ax_metrics, 0.36, 0.1, 0.28, 0.8, "PROFIL TACTIQUE", content2, profil_color)
    
        # Boîte 3: Intelligence spatiale
        content3 = f"""Actions Totales Analysées:
    {total_events} événements
    
    Répartition des Actions:
    Possession: {len(possession_events)}
    Défense: {len(defensive_events)}
    
    Intelligence Spatiale:
    Score Global: {mobility_score:.1f}/50"""
    
        create_text_box(ax_metrics, 0.7, 0.1, 0.28, 0.8, "INTELLIGENCE", content3, '#FFD700')
    
        # Tag et source stylisé
        ax.text(0.5, 0.02, "@TarbouchData - Intelligence Positionnelle Avancée", 
                fontsize=22, color='white', fontweight='bold', ha='center', 
                transform=ax.transAxes, alpha=0.9,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.8, edgecolor='white'))
    
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()
    
    def plot_pressure_analysis(self, save_path):
        """Analyse de la gestion de la pression adverse et intensité - Version améliorée"""
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
    
        # Création de la visualisation améliorée
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
    
        fig = plt.figure(figsize=(18, 12))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
    
        gs = GridSpec(2, 3, height_ratios=[3, 1], width_ratios=[1, 1, 1])
    
        # Titre principal stylisé
        ax.text(0.5, 0.96, f"ANALYSE DE PRESSION - {self.player_data['player_name']}", 
                fontsize=30, color='white', fontweight='bold', ha='center', transform=ax.transAxes)
    
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
    
        # Légende terrain 1 avec couleurs distinctes
        legend_elements1 = [
            plt.Line2D([0], [0], marker='o', color='w', label='Action Réussie sous Pression', 
                    markerfacecolor='#00FF00', markersize=20, markeredgecolor='white', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', label='Action Ratée sous Pression', 
                    markerfacecolor='#FF0000', markersize=18, markeredgecolor='white', markeredgewidth=2)
        ]
        legend1 = ax_pitch1.legend(handles=legend_elements1, loc='upper right', bbox_to_anchor=(1.35, 1), 
                        fontsize=12, frameon=True, facecolor='black', edgecolor='white')
        for text in legend1.get_texts():
            text.set_color('white')
    
        ax_pitch1.set_title(f"Sous Pression ({len(pressure_events)} actions)", 
                        fontsize=22, color='#FF6B35', fontweight='bold', pad=20)
    
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
    
        # Légende terrain 2 avec couleurs distinctes
        legend_elements2 = [
            plt.Line2D([0], [0], marker='o', color='w', label='Action Réussie Normale', 
                    markerfacecolor='#00BFFF', markersize=18, markeredgecolor='white', markeredgewidth=2),
            plt.Line2D([0], [0], marker='o', color='w', label='Action Ratée Normale', 
                    markerfacecolor='#FF8C00', markersize=16, markeredgecolor='white', markeredgewidth=2)
        ]
        legend2 = ax_pitch2.legend(handles=legend_elements2, loc='upper right', bbox_to_anchor=(1.32, 1), 
                        fontsize=12, frameon=True, facecolor='black', edgecolor='white')
        for text in legend2.get_texts():
            text.set_color('white')
    
        ax_pitch2.set_title(f"Conditions Normales ({len(normal_events)} actions)", 
                        fontsize=22, color='#32CD32', fontweight='bold', pad=20)
    
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
            
            # Heatmap stylisée pour la pression avec couleurs plus vives
            pressure_cmap = mcolors.LinearSegmentedColormap.from_list(
                "pressure_heat", [(0, 0, 0, 0), (1, 1, 0, 0.6), (1, 0.3, 0, 0.8), (1, 0, 0, 1)], N=100)
            pitch3.heatmap(bin_stat_pressure, ax=ax_pitch3, cmap=pressure_cmap)
    
        # Légende terrain 3 avec couleurs distinctes
        legend_elements3 = [
            plt.Rectangle((0, 0), 1, 1, facecolor='#FF0000', alpha=0.9, label='Pression Maximale'),
            plt.Rectangle((0, 0), 1, 1, facecolor='#FF6B00', alpha=0.8, label='Pression Élevée'),
            plt.Rectangle((0, 0), 1, 1, facecolor='#FFFF00', alpha=0.6, label='Pression Modérée')
        ]
        legend3 = ax_pitch3.legend(handles=legend_elements3, loc='upper right', bbox_to_anchor=(1.3, 1), 
                        fontsize=12, frameon=True, facecolor='black', edgecolor='white')
        for text in legend3.get_texts():
            text.set_color('white')
    
        ax_pitch3.set_title("Zones de Haute Pression", fontsize=22, color='#FFD700', fontweight='bold', pad=20)
    
        # ===== MÉTRIQUES TEXTUELLES STYLISÉES =====
        ax_metrics = fig.add_subplot(gs[1, :])
        ax_metrics.axis('off')
    
        # Calculs des métriques avancées
        pressure_ratio = (len(pressure_events) / len(events) * 100) if events else 0
        efficiency_diff = pressure_efficiency - normal_efficiency
    
        # Évaluation de la réaction à la pression avec emojis
        if efficiency_diff < -10:
            reaction_grade = "CRITIQUE"
            reaction_color = '#FF0000'
        elif efficiency_diff < -5:
            reaction_grade = "DIFFICILE"
            reaction_color = '#FF6B00'
        elif efficiency_diff < 5:
            reaction_grade = "CORRECT"
            reaction_color = '#FFD700'
        else:
            reaction_grade = "EXCEPTIONNEL"
            reaction_color = '#00FF00'
    
        # Zones de pression maximale
        pressure_zones = {'Défense': 0, 'Milieu': 0, 'Attaque': 0}
        for x, y in pressure_positions:
            if y < 33:
                pressure_zones['Défense'] += 1
            elif y < 66:
                pressure_zones['Milieu'] += 1
            else:
                pressure_zones['Attaque'] += 1
    
        max_pressure_zone = max(pressure_zones.items(), key=lambda x: x[1]) if pressure_zones else ("Aucune", 0)
    
        # Évaluation du niveau de pression
        if pressure_ratio > 60:
            pressure_level = "TRÈS SOLLICITÉ"
            pressure_color = '#FF0000'
        elif pressure_ratio > 40:
            pressure_level = "SOLLICITÉ"
            pressure_color = '#FF6B00'
        else:
            pressure_level = "PEU PRESSÉ"
            pressure_color = '#00FF00'
    
        # Création des boîtes stylisées pour le texte
        def create_pressure_box(ax, x, y, width, height, title, content, title_color, bg_color='black'):
            # Rectangle de fond avec bordure colorée
            rect = plt.Rectangle((x, y), width, height, facecolor=bg_color, alpha=0.85, 
                            edgecolor=title_color, linewidth=3, transform=ax.transAxes)
            ax.add_patch(rect)
            
            # Titre coloré avec fond
            title_rect = plt.Rectangle((x, y + height - 0.15), width, 0.15, 
                                    facecolor=title_color, alpha=0.3, transform=ax.transAxes)
            ax.add_patch(title_rect)
            
            ax.text(x + width/2, y + height - 0.075, title, fontsize=18, color=title_color, 
                fontweight='bold', ha='center', va='center', transform=ax.transAxes)
            
            # Contenu
            ax.text(x + width/2, y + height/2 - 0.05, content, fontsize=16, color='white', 
                fontweight='bold', ha='center', va='center', transform=ax.transAxes)
    
        # Boîte 1: Pression globale
        content1 = f"""{pressure_level}
    {pressure_ratio:.0f}% des actions
    
    Efficacité Comparative:
    Sous pression: {pressure_efficiency:.0f}%
    Conditions normales: {normal_efficiency:.0f}%
    
    {reaction_grade}"""
    
        create_pressure_box(ax_metrics, 0.02, 0.1, 0.3, 0.8, "NIVEAU DE PRESSION", content1, pressure_color)
    
        # Boîte 2: Comportement
        content2 = f"""Volume d'Actions Analysées:
    Sous pression: {pressure_total}
    Normales: {normal_total}
    
    Zone de Plus Forte Pression:
    {max_pressure_zone[0]}
    {max_pressure_zone[1]} actions
    
    Ratio Actions: {pressure_total}/{normal_total}"""
    
        create_pressure_box(ax_metrics, 0.35, 0.1, 0.3, 0.8, "COMPORTEMENT", content2, '#00BFFF')
    
        # Boîte 3: Performance
        adaptability_color = '#00FF00' if efficiency_diff > 0 else '#FF6B00' if efficiency_diff > -5 else '#FF0000'
        adaptability_text = 'ÉLEVÉE' if efficiency_diff > 0 else 'MOYENNE' if efficiency_diff > -5 else 'FAIBLE'
    
        content3 = f"""Différence d'Efficacité:
    {efficiency_diff:+.0f} points
    
    Actions Réussies:
    Sous pression: {pressure_success}
    Normales: {normal_success}
    
    Adaptabilité: {adaptability_text}
    Mental: {'Fort' if efficiency_diff > -5 else 'Fragile'}"""
    
        create_pressure_box(ax_metrics, 0.68, 0.1, 0.3, 0.8, "PERFORMANCE", content3, adaptability_color)
    
        # Tag et source stylisé
        ax.text(0.5, 0.02, "@TarbouchData - Analyse de Pression Avancée", 
                fontsize=22, color='white', fontweight='bold', ha='center', 
                transform=ax.transAxes, alpha=0.9,
                bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.8, edgecolor='#FF6B35'))
    
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()
    
    def plot_next_action_prediction(self, save_path):
        """Analyse des patterns et prévisibilité du joueur - Version ultra-améliorée"""
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
        from collections import defaultdict
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
        from collections import defaultdict, Counter
        transition_matrix = defaultdict(Counter)
        
        for current, next_action in action_sequences:
            transition_matrix[current][next_action] += 1
    
        predictability_score = 0
        for current_action, next_actions in transition_matrix.items():
            if next_actions:
                max_prob = max(next_actions.values()) / sum(next_actions.values())
                predictability_score += max_prob
        
        predictability_score = (predictability_score / len(transition_matrix)) * 100 if transition_matrix else 0
    
        # Créer la visualisation ultra-stylisée
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
    
        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
    
        gs = GridSpec(2, 3, height_ratios=[3, 1], width_ratios=[1.5, 1, 1.5])
    
        # Titre principal ultra-stylisé
        ax.text(0.5, 0.96, f"ANALYSE PRÉDICTIVE - {self.player_data['player_name']}", 
                fontsize=28, color='white', fontweight='bold', ha='center', transform=ax.transAxes)
    
        # ===== TERRAIN: ZONES DE CONFORT =====
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=3)
        ax_pitch = fig.add_subplot(gs[0, 0])
        pitch.draw(ax=ax_pitch)
    
        # Afficher les actions avec code couleur selon l'efficacité de la zone
        for event in events:
            if 'x' not in event or 'y' not in event:
                continue
            
            x, y = event['x'], event['y']
            
            # Déterminer la zone et sa couleur
            if y < 33:
                zone_eff = zone_efficiency.get('Défensive', 50)
                zone_name = 'Défensive'
            elif y < 66:
                zone_eff = zone_efficiency.get('Milieu', 50)
                zone_name = 'Milieu'
            else:
                zone_eff = zone_efficiency.get('Offensive', 50)
                zone_name = 'Offensive'
            
            # Couleurs très distinctes basées sur l'efficacité
            if zone_eff > 80:
                color = '#00FF00'  # Vert vif - zone de confort maximale
            elif zone_eff > 60:
                color = '#00BFFF'  # Bleu ciel - bonne zone
            elif zone_eff > 40:
                color = '#FFD700'  # Or - zone moyenne
            else:
                color = '#FF4500'  # Rouge orangé - zone de défi
            
            pitch.scatter(x, y, s=100, alpha=0.8, color=color, 
                        edgecolor='white', linewidth=1.5, ax=ax_pitch)
    
        # Ajouter les labels des zones avec leur efficacité - STYLE AMÉLIORÉ
        zone_positions = {'Défensive': 16.5, 'Milieu': 49.5, 'Offensive': 82.5}
        for zone, efficiency in zone_efficiency.items():
            y_pos = zone_positions[zone]
            
            if efficiency > 80:
                bg_color = '#00FF00'
                emoji = ''
            elif efficiency > 60:
                bg_color = '#00BFFF'
                emoji = ''
            elif efficiency > 40:
                bg_color = '#FFD700'
                emoji = ''
            else:
                bg_color = '#FF4500'
                emoji = ''
            
            ax_pitch.text(50, y_pos, f'{emoji} {zone}\n{efficiency:.0f}%', 
                        ha='center', va='center', fontsize=14, color='white', 
                        fontweight='bold', bbox=dict(boxstyle='round,pad=0.6', 
                        facecolor=bg_color, alpha=0.9, edgecolor='white', linewidth=2))
    
        # Légende terrain zones de confort avec emojis
        legend_elements_zones = [
            plt.Line2D([0], [0], marker='o', color='w', label='Zone Confort Max (>80%)', 
                    markerfacecolor='#00FF00', markersize=18),
            plt.Line2D([0], [0], marker='o', color='w', label='Bonne Zone (60-80%)', 
                    markerfacecolor='#00BFFF', markersize=18),
            plt.Line2D([0], [0], marker='o', color='w', label='Zone Moyenne (40-60%)', 
                    markerfacecolor='#FFD700', markersize=18),
            plt.Line2D([0], [0], marker='o', color='w', label='Zone Défi (<40%)', 
                    markerfacecolor='#FF4500', markersize=18)
        ]
        legend_zones = ax_pitch.legend(handles=legend_elements_zones, loc='upper right', bbox_to_anchor=(1.32, 1), 
                        fontsize=11, frameon=True, facecolor='black', edgecolor='white')
        for text in legend_zones.get_texts():
            text.set_color('white')
    
        ax_pitch.set_title('Zones de Confort', fontsize=22, color='#00FF80', fontweight='bold', pad=20)
    
        # ===== GRAPHIQUE DIRECTIONNEL DES PASSES =====
        ax_directions = fig.add_subplot(gs[0, 1])
        ax_directions.set_facecolor('none')
        
        # Graphique en secteurs ultra-stylisé pour les préférences directionnelles
        total_passes = sum(directional_preferences.values())
        if total_passes > 0:
            labels = ['Progression', 'Latérales', 'Conservation']
            sizes = [directional_preferences['forward'], 
                    directional_preferences['lateral'], 
                    directional_preferences['backward']]
            colors = ['#00FF80', '#FFD700', '#FF6B35']  # Couleurs très distinctes
            explode = (0.08, 0.05, 0.05)  # Mettre en avant la progression
            
            # Créer le graphique en secteurs avec style ultra-amélioré
            wedges, texts, autotexts = ax_directions.pie(sizes, labels=labels, colors=colors, 
                                                        autopct='%1.1f%%', startangle=90, explode=explode,
                                                        textprops={'color': 'white', 'fontsize': 15, 'fontweight': 'bold'},
                                                        wedgeprops=dict(edgecolor='white', linewidth=4))
            
            # Style ultra-amélioré des pourcentages
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(14)
                autotext.set_bbox(dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
            
            # Style des labels
            for text in texts:
                text.set_fontsize(13)
                text.set_fontweight('bold')
            
            ax_directions.set_title('Préférences Directionnelles', 
                                fontsize=22, color='#FFD700', fontweight='bold', pad=20)
    
        # ===== ANALYSE DES PATTERNS DE MOUVEMENT AMÉLIORÉE =====
        ax_patterns = fig.add_subplot(gs[0, 2])
        ax_patterns.set_facecolor('none')
        
        # Analyse ultra-développée des préférences tactiques avec nouveaux termes
        pass_distances = {'courtes': 0, 'moyennes': 0, 'longues': 0}
        pass_sides = {'gauche': 0, 'centre': 0, 'droite': 0}
        pass_directions_detailed = {'progression': 0, 'conservation': 0, 'ouverture': 0}
        
        for pass_event in pass_events:
            if 'endX' in pass_event and 'endY' in pass_event:
                start_x, start_y = pass_event['x'], pass_event['y']
                end_x, end_y = pass_event['endX'], pass_event['endY']
                
                # Distance euclidienne
                distance = np.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
                
                # Classification des distances
                if distance < 15:
                    pass_distances['courtes'] += 1
                elif distance < 35:
                    pass_distances['moyennes'] += 1
                else:
                    pass_distances['longues'] += 1
                
                # Analyse latérale (côtés du terrain)
                if start_x < 33:
                    pass_sides['gauche'] += 1
                elif start_x > 67:
                    pass_sides['droite'] += 1
                else:
                    pass_sides['centre'] += 1
                
                # Analyse tactique avancée
                y_diff = end_y - start_y
                x_diff = abs(end_x - start_x)
                
                if y_diff > 10:
                    pass_directions_detailed['progression'] += 1
                elif y_diff < -5:
                    pass_directions_detailed['conservation'] += 1
                elif x_diff > 20:
                    pass_directions_detailed['ouverture'] += 1
    
        # Analyse des mouvements préférentiels avec nouveaux termes
        movement_patterns = {
            'centre_vers_aile': 0,
            'aile_vers_centre': 0,
            'changement_aile': 0,
            'percee_axiale': 0  # Remplace "penetration"
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
                
                # Percée dans l'axe (nouveau terme)
                elif abs(start_x - end_x) < 15 and end_y > start_y + 15:
                    movement_patterns['percee_axiale'] += 1
    
        # Graphique des patterns avec nouveaux termes et couleurs distinctes
        pattern_labels = ['Centre→Aile', 'Aile→Centre', 'Chang. Aile', 'Percée Axiale']
        pattern_values = list(movement_patterns.values())
        pattern_colors = ['#FF6B35', '#00FF80', '#FFD700', '#FF0080']  # Couleurs très distinctes
        
        bars = ax_patterns.bar(pattern_labels, pattern_values, color=pattern_colors, 
                            alpha=0.9, edgecolor='white', linewidth=3)
        
        # Ajouter les valeurs et pourcentages avec style amélioré
        total_patterns = sum(pattern_values) if sum(pattern_values) > 0 else 1
        for bar, value in zip(bars, pattern_values):
            percentage = (value / total_patterns) * 100
            ax_patterns.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(pattern_values)*0.05,
                        f'{value}\n({percentage:.1f}%)', ha='center', va='bottom', 
                        color='white', fontweight='bold', fontsize=12,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.8))
        
        ax_patterns.set_ylabel('Occurrences', fontsize=14, color='white', fontweight='bold')
        ax_patterns.set_title('Patterns de Mouvement', fontsize=22, color='#FF6B35', fontweight='bold')
        ax_patterns.tick_params(colors='white', labelsize=11)
        ax_patterns.set_xticklabels(pattern_labels, rotation=15, fontweight='bold')
        ax_patterns.grid(True, alpha=0.3, color='white')
    
        # ===== ANALYSE TEXTUELLE ULTRA-STYLISÉE =====
        ax_text = fig.add_subplot(gs[1, :])
        ax_text.axis('off')
    
        # Calculs avancés
        action_diversity = len(set([e['type']['displayName'] for e in events]))
        comfort_zone = max(zone_efficiency.items(), key=lambda x: x[1]) if zone_efficiency else ("Aucune", 0)
        forward_pct = (directional_preferences['forward'] / total_passes * 100) if total_passes > 0 else 0
    
        # Évaluation du profil de joueur avec emojis
        if predictability_score > 70:
            player_profile = "TRÈS PRÉVISIBLE"
            profile_color = "#FF4500"
        elif predictability_score > 50:
            player_profile = "ÉQUILIBRÉ"
            profile_color = "#FFD700"
        else:
            player_profile = "CRÉATIF"
            profile_color = "#00FF80"
    
        # Style de jeu avec emojis
        if forward_pct > 60:
            style_jeu = "PROGRESSISTE"
            style_color = "#00FF80"
        elif forward_pct < 30:
            style_jeu = "SÉCURITAIRE"
            style_color = "#FFD700"
        else:
            style_jeu = "ÉQUILIBRÉ"
            style_color = "#00BFFF"
    
        # Polyvalence avec emojis
        if action_diversity > 8:
            polyvalence = "TRÈS POLYVALENT"
            poly_color = "#FF0080"
        elif action_diversity > 5:
            polyvalence = "POLYVALENT"
            poly_color = "#00FF80"
        else:
            polyvalence = "SPÉCIALISÉ"
            poly_color = "#FFD700"
    
        # Calculs détaillés pour les boîtes
        total_passes_analysis = sum(pass_distances.values()) if sum(pass_distances.values()) > 0 else 1
        total_patterns = sum(movement_patterns.values()) if sum(movement_patterns.values()) > 0 else 1
        
        courtes_pct = (pass_distances['courtes'] / total_passes_analysis) * 100
        moyennes_pct = (pass_distances['moyennes'] / total_passes_analysis) * 100
        longues_pct = (pass_distances['longues'] / total_passes_analysis) * 100
        
        total_sides = sum(pass_sides.values()) if sum(pass_sides.values()) > 0 else 1
        gauche_pct = (pass_sides['gauche'] / total_sides) * 100
        centre_pct = (pass_sides['centre'] / total_sides) * 100
        droite_pct = (pass_sides['droite'] / total_sides) * 100
        
        centre_aile_pct = (movement_patterns['centre_vers_aile'] / total_patterns) * 100
        aile_centre_pct = (movement_patterns['aile_vers_centre'] / total_patterns) * 100
        changement_aile_pct = (movement_patterns['changement_aile'] / total_patterns) * 100
        percee_pct = (movement_patterns['percee_axiale'] / total_patterns) * 100
    
        # Fonction pour créer des boîtes ultra-stylisées
        def create_prediction_box(ax, x, y, width, height, title, content, title_color, bg_color='black'):
            # Rectangle de fond avec dégradé simulé
            rect = plt.Rectangle((x, y), width, height, facecolor=bg_color, alpha=0.9, 
                            edgecolor=title_color, linewidth=4, transform=ax.transAxes)
            ax.add_patch(rect)
            
            # Barre de titre colorée
            title_rect = plt.Rectangle((x, y + height - 0.18), width, 0.18, 
                                    facecolor=title_color, alpha=0.4, transform=ax.transAxes)
            ax.add_patch(title_rect)
            
            ax.text(x + width/2, y + height - 0.09, title, fontsize=18, color=title_color, 
                fontweight='bold', ha='center', va='center', transform=ax.transAxes)
            
            # Contenu avec meilleur espacement
            ax.text(x + width/2, y + (height-0.18)/2, content, fontsize=15, color='white', 
                fontweight='bold', ha='center', va='center', transform=ax.transAxes,
                linespacing=1.5)
    
        # Boîte 1: Style de jeu
        content1 = f"""{style_jeu}
    
    Distance des Passes:
    Courtes: {courtes_pct:.0f}%
    Moyennes: {moyennes_pct:.0f}%
    Longues: {longues_pct:.0f}%
    
    {player_profile}
    Score: {predictability_score:.0f}%"""
    
        create_prediction_box(ax_text, 0.02, 0.1, 0.3, 0.8, "STYLE DE JEU", content1, style_color)
    
        # Boîte 2: Préférences spatiales
        if gauche_pct > 45:
            preference_laterale = "CÔTÉ GAUCHE"
            pref_color = "#00FF80"
        elif droite_pct > 45:
            preference_laterale = "CÔTÉ DROIT"
            pref_color = "#FF6B35"
        else:
            preference_laterale = "POLYVALENT"
            pref_color = "#FFD700"
    
        content2 = f"""{preference_laterale}
    
    Répartition Spatiale:
    Gauche: {gauche_pct:.0f}%
    Centre: {centre_pct:.0f}%
    Droite: {droite_pct:.0f}%
    
    {polyvalence}
    Diversité: {action_diversity} types"""
    
        create_prediction_box(ax_text, 0.35, 0.1, 0.3, 0.8, "PRÉFÉRENCES", content2, pref_color)
    
        # Boîte 3: Patterns tactiques
        max_pattern = max(movement_patterns.items(), key=lambda x: x[1])
        if max_pattern[0] == 'centre_vers_aile':
            pattern_dominant = "OUVREUR"
            pattern_color = "#FF6B35"
        elif max_pattern[0] == 'aile_vers_centre':
            pattern_dominant = "RECENTREUR"  
            pattern_color = "#00FF80"
        elif max_pattern[0] == 'changement_aile':
            pattern_dominant = "RETOURNEUR"
            pattern_color = "#FFD700"
        else:
            pattern_dominant = "PERCUTANT"  # Remplace "PÉNÉTRATEUR"
            pattern_color = "#FF0080"
    
        content3 = f"""{pattern_dominant}
    
    Patterns de Mouvement:
    Centre→Aile: {centre_aile_pct:.0f}%
    Aile→Centre: {aile_centre_pct:.0f}%
    Chang. Aile: {changement_aile_pct:.0f}%
    Percée: {percee_pct:.0f}%
    
    Actions: {len(events)} analysées"""
    
        create_prediction_box(ax_text, 0.68, 0.1, 0.3, 0.8, "PATTERNS", content3, pattern_color)
    
        # Tag et source ultra-stylisé
        ax.text(0.5, 0.02, "@TarbouchData - Analyse Prédictive Avancée", 
                fontsize=22, color='white', fontweight='bold', ha='center', 
                transform=ax.transAxes, alpha=0.9,
                bbox=dict(boxstyle='round,pad=0.6', facecolor='black', alpha=0.8, edgecolor='#FF0080', linewidth=3))
    
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()
    
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
            print("Analyse spatiale générée")
            
            # 2. Analyse de pression
            pressure_path = os.path.join(save_dir, f"{player_name_clean}_pressure_analysis.png")
            self.plot_pressure_analysis(pressure_path)
            print("Analyse de pression générée")
            
            # 3. Analyse prédictive
            prediction_path = os.path.join(save_dir, f"{player_name_clean}_predictive_analysis.png")
            self.plot_next_action_prediction(prediction_path)
            print("Analyse prédictive générée")
            
            print(f"Suite d'analyses complète disponible dans: {save_dir}")
            
            return {
                "spatial": spatial_path,
                "pressure": pressure_path, 
                "predictive": prediction_path
            }
            
        except Exception as e:
            print(f"Erreur lors de la génération: {e}")
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
    
        # ===== RADAR CHART COMPARATIF AMÉLIORÉ =====
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
        legend_radar = ax_radar.legend(loc='upper right', bbox_to_anchor=(1.4, 1.0), fontsize=12,
                                    frameon=True, facecolor='black', edgecolor='white')
        for text in legend_radar.get_texts():
            text.set_color('white')
        
        ax_radar.set_title('Profils Comparatifs', color='white', fontsize=20, fontweight='bold', pad=30)
    
        # ===== GRAPHIQUES EN BARRES STYLISÉS =====
        metrics_to_compare = [
            ('Taux de Réussite (%)', 'success_rate', '#00FF80'),
            ('Ratio Pression (%)', 'pressure_ratio', '#FF6B35'),
            ('Diversité Actions', 'action_diversity', '#FFD700'),
            ('Meilleure Zone (%)', 'best_zone_efficiency', '#FF0080')
        ]
        
        for idx, (metric_title, metric_key, metric_color) in enumerate(metrics_to_compare):
            if idx < 2:
                ax_bar = fig.add_subplot(gs[1, 1])
            else:
                ax_bar = fig.add_subplot(gs[2, idx-2])
            
            ax_bar.set_facecolor('none')
            
            names = [p['name'][:10] for p in players_metrics]
            values = [p[metric_key] for p in players_metrics]
            
            # Créer des barres avec dégradé de couleurs
            bar_colors = [colors[i] for i in range(len(players_metrics))]
            bars = ax_bar.bar(names, values, color=bar_colors, alpha=0.9, 
                            edgecolor='white', linewidth=3)
            
            ax_bar.set_title(metric_title, fontsize=18, color=metric_color, fontweight='bold')
            ax_bar.tick_params(colors='white', labelsize=11)
            ax_bar.grid(True, alpha=0.3, color='white')
            
            # Ajouter les valeurs sur les barres avec style
            for bar, value in zip(bars, values):
                ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                        f'{value:.1f}', ha='center', va='bottom', color='white', 
                        fontweight='bold', fontsize=12,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.8))
    
        # ===== CLASSEMENT GÉNÉRAL STYLISÉ =====
        ax_ranking = fig.add_subplot(gs[2, :])
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
        
        # Créer le classement avec style ultra-amélioré
        ranking_text = "CLASSEMENT GÉNÉRAL (Score Composite)\n" + "="*60 + "\n\n"
        medals = ["1er", "2ème", "3ème", "4ème", "5ème"]
        
        for i, player in enumerate(players_metrics):
            medal = medals[i] if i < 5 else f"{i+1}ème"
            
            # Évaluation du score
            score = player['composite_score']
            if score > 85:
                grade = "EXCEPTIONNEL"
            elif score > 75:
                grade = "EXCELLENT"
            elif score > 65:
                grade = "TRÈS BON"
            elif score > 55:
                grade = "BON"
            else:
                grade = "MOYEN"
            
            ranking_text += f"{medal} {player['name']} - Score: {score:.1f}/100 - {grade}\n"
            ranking_text += f"     Efficacité: {player['success_rate']:.1f}% | "
            ranking_text += f"Actions: {player['total_actions']} | "
            ranking_text += f"Diversité: {player['action_diversity']}\n\n"
    
        # Créer une boîte stylisée pour le classement
        ranking_box = plt.Rectangle((0.05, 0.1), 0.9, 0.8, facecolor='black', alpha=0.9, 
                                edgecolor='white', linewidth=3, transform=ax_ranking.transAxes)
        ax_ranking.add_patch(ranking_box)
    
        ax_ranking.text(0.5, 0.5, ranking_text, fontsize=14, color='white', 
                    fontweight='bold', ha='center', va='center', transform=ax_ranking.transAxes,
                    linespacing=1.3)
    
        # Tag et source ultra-stylisé
        ax.text(0.5, 0.02, "@TarbouchData - Comparaison Multi-Joueurs Avancée", 
                fontsize=22, color='white', fontweight='bold', ha='center', 
                transform=ax.transAxes, alpha=0.9,
                bbox=dict(boxstyle='round,pad=0.6', facecolor='black', alpha=0.8, 
                        edgecolor='#FFD700', linewidth=4))
    
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()
    
        return players_metrics