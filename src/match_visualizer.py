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


class MatchVisualizer(PlayerVisualizer):
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

        # Check if the player was a starter or a substitute and calculate playing time
        if self.player_data["isFirstEleven"]:
            status_text = "Titulaire"
            start_minute = 0
        else:
            first_minute = min(self.player_data["stats"]["ratings"].keys())
            status_text = f'Rentré {first_minute}"'
            start_minute = first_minute

        # Get the last minute played
        last_minute = list(self.player_data["stats"]["ratings"].keys())[-1]
        playing_time = int(last_minute) - int(start_minute)
        
        # Get the number of assists (key passes leading to a goal)
        assists = sum(1 for event in self.player_data['events'] if any(qualifier['type']['displayName'] == 'IntentionalGoalAssist' for qualifier in event.get('qualifiers', [])))
        
        # Initial Y position for the first text line
        y_position = 0.96
        y_step = 0.03  # Step between text lines

        # List of text items to display
        text_items = [
            f"{self.player_data['player_name']} - N°{self.player_data['shirtNo']}",
            f"{self.player_data['age']} ans - {self.player_data['height']}cm",
            f"{status_text} ",
            f"{self.match_teams}",
            f"Temps de jeu: {playing_time} minutes",
            f"{len(goals)} but(s)" if len(goals) >= 1 else None,
            f"{nb_passe_d} passe(s) décisive(s)" if nb_passe_d >= 1 else None, # TODO
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
            ('Interceptions réussies', len(successful_interceptions), len(interceptions)),
            ('Passes réussies', len(successful_passes), total_passes),
            ('Dribbles réussis', len(successful_takeons), len(takeons)),
            ('Tirs cadrés', len(saved_shots) + len(goals), len(missed_shots) + len(saved_shots) + len(goals)),
            ('Fautes commises', len(committed_fouls), len(committed_fouls)),
            ('Fautes subies', len(submitted_fouls), len(submitted_fouls))
        ]

        # Priorités par type de joueur
        priorities = {
            'DEF': ['Récuperations', 'Tacles réussis', 'Interceptions réussies', 'Passes réussies'],
            'MIL': ['Dribbles réussis', 'Passes réussies', 'Passes clés', 'Récuperations'],
            'ATT': ['Dribbles réussis', 'Tirs cadrés', 'Passes clés', 'Récuperations']
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





        # 2. Plotting the pitches on the second row

        # First pitch (1,0) - left side
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch_left = fig.add_subplot(gs[4:, 0], aspect=1)
        pitch.draw(ax=ax_pitch_left)

        for pas in passes:
            y_start = pas['x']
            x_start = pas['y']
            y_end = pas['endX']
            x_end = pas['endY']

            color = '#6DF176' if pas['outcomeType']['displayName'] == 'Successful' else 'red'
            pitch.arrows(y_start, x_start, y_end, x_end, width=3, headwidth=3, headlength=3, color=color, ax=ax_pitch_left)
            
        # 3. Plotting the second pitch (right) with heatmap on the second row
        ax_pitch_right = fig.add_subplot(gs[4:, 1], aspect=1)
        pitch.draw(ax=ax_pitch_right)
    
        # Collecting all pass starting positions
        touchs  = [event for event in events]
        x_coords = [t['x'] for t in touchs]
        y_coords = [t['y'] for t in touchs]
    
        # Compute bin statistic for heatmap
        bin_statistic = pitch.bin_statistic(x_coords, y_coords, statistic='count', bins=(20, 20))
    
        # Apply Gaussian filter for smoothing
        bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)

        el_greco_transparent_orange_red = mcolors.LinearSegmentedColormap.from_list(
            "Transparent-Orange-Red",
            [(1, 1, 1, 0),    # Transparent (RGBA: alpha = 0)
             (1, 0.65, 0, 1),  # Orange (RGBA: full opacity)
             (1, 0, 0, 1)],    # Red (RGBA: full opacity)
            N=10
        )
        # Plot the heatmap using the custom colormap with transparency for low activity areas
        pitch.heatmap(bin_statistic, ax=ax_pitch_right, cmap=el_greco_transparent_orange_red)
    
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

        forward_passes = 0 
        lateral_passes = 0 
        backward_passes = 0

        for pas in successful_passes:
            y_start = pas['x']
            x_start = pas['y']
            y_end = pas['endX']
            x_end = pas['endY']
            alpha_pass = 1
            
            # Calcul de l'angle
            angle = np.degrees(np.arctan2(y_end - y_start, x_end - x_start))
    
            # Définir les couleurs selon le type de passe
            if 30 <= angle <= 150:
                color = '#78ff00'  # Couleur pour les passes en avant
                forward_passes = forward_passes+1
            elif -150 <= angle <= -30:
                alpha_pass = 0.5
                color = '#ff3600'  # Couleur pour les passes en arrière 
                backward_passes = backward_passes+1
            else:
                color = '#ffb200'  # Couleur pour les passes latérales 
                alpha_pass = 0.8
                lateral_passes = lateral_passes+1

            # Dessiner la flèche avec la couleur appropriée
            pitch.arrows(y_start, x_start, y_end, x_end, width=2, headwidth=3, headlength=3, color=color, ax=ax_pitch, alpha=alpha_pass)

    
        p_1 = mpatches.Patch(color='#78ff00', label='Passes vers l\'avant')
        p_2 = mpatches.Patch(color='#ffb200', label='Passes latérales')
        p_3 = mpatches.Patch(color='#ff3600', label='Passes vers l\'arrière')
        ax_pitch.legend(handles=[p_1, p_2, p_3], loc='upper right', bbox_to_anchor=(1.425, 1), fontsize=12)
        ax_pitch.set_title("@MaData_fr", fontsize=20, color=(1, 1, 1, 0), fontweight='bold', loc='center')

        # Ajoutez cette ligne à la place
        ax.text(0.5, 0.96, f"Passes de {self.player_data['player_name']}", fontsize=20, color='white', fontweight='bold', ha='center', transform=ax.transAxes)

        # Display your tag or source at a fixed position
        ax.text(0.425, 0.77, f"@TarbouchData", fontsize=14, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)


        # 2. Plotting data visualizations on the right side
    
        # Move the semi-circular gauge lower (closer to the first bar plot)
        ax_gauge = fig.add_subplot(gs[1:5, 1], polar=True)  # Now taking up only the third row, right above the bar chart
        self._plot_semi_circular_gauge(ax_gauge, "Taux de passes réussies", len(successful_passes), total_passes)
    
        # Horizontal bars for forward, lateral, and backward passes
        ax_bar1 = fig.add_subplot(gs[3, 1])
        ax_bar2 = fig.add_subplot(gs[4, 1])
        ax_bar3 = fig.add_subplot(gs[5, 1])

        self._add_horizontal_bar(ax_bar1, 'Passes vers l\'avant', forward_passes, total_passes)
        self._add_horizontal_bar(ax_bar2, 'Passes latérales', lateral_passes, total_passes)
        self._add_horizontal_bar(ax_bar3, 'Passes vers l\'arrière', backward_passes, total_passes)
    
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

    def plot_stats_visualizations(self, save_path):
        stats = self._process_stats_data()

        # Récupérer les événements du joueur
        events = self.player_data.get('events', [])

        # Récupérer les minutes des buts à partir des événements
        goal_minutes = [event['minute'] for event in events if event['type']['displayName'] == 'Goal']

        # Récupérer les passes décisives (IntentionalGoalAssist uniquement)
        assist_minutes = [
            event['minute'] for event in events 
            if event['type']['displayName'] == 'Pass' and any(
                qualifier['type']['displayName'] == 'IntentionalGoalAssist' for qualifier in event.get('qualifiers', [])
            )
        ]

        # Définir la minute d'entrée en jeu du joueur (ici, nous prenons la première minute où il a une action)
        first_minute_played = stats['minutes'][0] if stats['minutes'] else None

        # Définir la couleur de fond globale
        background_color = '#8549B7'  # Violet foncé
        orange_background = '#D4CAE1'  # Orange

        # Créer un gradient vertical (de haut en bas)
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))

        # Créer un colormap personnalisé à partir des couleurs hexadécimales
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        # Créer une figure adaptée pour téléphone
        fig = plt.figure(figsize=(9, 16))  # Largeur 9, hauteur 16 pour un meilleur ajustement mobile

        # Ajouter un axe qui occupe toute la figure
        ax = fig.add_axes([0, 0, 1, 1])

        # Désactiver les axes
        ax.axis('off')

        # Appliquer le gradient vertical avec les couleurs choisies
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        # Ajouter présentation du joueur
        gs = GridSpec(3, 1, height_ratios=[0.5, 1, 1], figure=fig)  # Présentation en haut, stats et notes en bas
        ax0 = fig.add_subplot(gs[0, 0])
        ax0.text(0.5, 0.5, f"Présentation du joueur : {self.player_data['player_name']}", fontsize=20, color='white', ha='center', va='center', fontweight='bold')
        ax0.axis('off')  # On désactive les axes pour cette section

        # Diagramme à barres verticales pour les statistiques globales
        ax1 = fig.add_subplot(gs[1, 0])
        ax1.set_facecolor(orange_background)  # Changer la couleur de fond à orange
        categories = [
            'Possession', 'Touches', 'Passes', 
            'Passes précises', 'Passes clés', 'Interceptions', 
            'Tacles réussis'
        ]
        values = [
            stats['total_possession'], stats['total_touches'], stats['total_passes'], 
            stats['total_accurate_passes'], stats['total_key_passes'], 
            stats['total_interceptions'], stats['total_successful_tackles']
        ]

        bars = ax1.bar(categories, values, color='mediumseagreen')

        # Ajouter les valeurs au-dessus de chaque barre
        for bar in bars:
            yval = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width() / 2, yval + 0.1, int(yval), ha='center', fontsize=10)

        ax1.set_ylabel('Total', fontsize=12, fontweight='bold', color='white')
        ax1.set_title(f"Stats globales de {self.player_data['player_name']}", fontsize=16, fontweight='bold', color='white')
        ax1.set_xticklabels(categories, rotation=45, ha='right', fontsize=12, color='white')
        ax1.tick_params(axis='y', colors='white')  # Changer la couleur des graduations sur l'axe Y
        ax1.spines['bottom'].set_color('white')
        ax1.spines['left'].set_color('white')

        # Diagramme de l'évolution des notes (rating)
        ax2 = fig.add_subplot(gs[2, 0])
        ax2.set_facecolor(orange_background)  # Changer la couleur de fond à orange

        # Données pour le graphique
        minutes = stats['minutes']
        ratings_over_time = stats['ratings_over_time']
        threshold = 6

        # Convertir les données en tableaux numpy
        ratings_over_time = np.array(ratings_over_time)

        # Tracer la ligne horizontale à 6
        ax2.axhline(y=threshold, color='white', linewidth=2, linestyle='--')

        # Déterminer les bornes Y pour centrer autour de la note actuelle
        if ratings_over_time.size > 0:
            current_rating = ratings_over_time[-1]
            lower_bound = max(0, current_rating - 2)  # Min value
            upper_bound = min(10, np.ceil(current_rating))  # Max value rounded up
        else:
            lower_bound, upper_bound = 0, 10  # Valeurs par défaut si pas de notes

        # Remplissage des zones
        ax2.fill_between(minutes, ratings_over_time, threshold, where=(ratings_over_time >= threshold), 
                         interpolate=True, color='#6DF176', alpha=0.3)
        ax2.fill_between(minutes, ratings_over_time, threshold, where=(ratings_over_time < threshold), 
                         interpolate=True, color='red', alpha=0.3)

        # Tracer la courbe fluide sans marqueurs
        ax2.plot(minutes, ratings_over_time, color='dodgerblue', linewidth=2)

        # Ajouter une ligne verticale à la fin pour indiquer la fin du match
        final_minute = minutes[-1]
        ax2.axvline(x=final_minute, color='red', linestyle='-', linewidth=2)
        ax2.text(final_minute + 0.5, lower_bound + 0.5, f'{final_minute}"', rotation=0, verticalalignment='center',
                 color='red', fontsize=12, fontweight='bold')

        # Ajouter un trait rouge vertical pour l'entrée en jeu et annoter avec "Entré en jeu"
        if first_minute_played is not None:
            ax2.axvline(x=first_minute_played, color='red', linestyle='-', linewidth=2)
            ax2.text(first_minute_played + 0.5, lower_bound + 0.5, f'Entré en jeu {first_minute_played}"', rotation=0, verticalalignment='center',
                     color='red', fontsize=12, fontweight='bold')

        # Tracer les points rouges pour les buts et les croix rouges pour les passes décisives
        for minute in set(goal_minutes + assist_minutes):
            if minute not in minutes:
                # Ajouter la minute si elle n'existe pas
                closest_minute_idx = np.searchsorted(minutes, minute)
                if closest_minute_idx == 0:
                    minutes.insert(0, minute)
                    ratings_over_time = np.insert(ratings_over_time, 0, ratings_over_time[0])
                elif closest_minute_idx == len(minutes):
                    minutes.append(minute)
                    ratings_over_time = np.append(ratings_over_time, ratings_over_time[-1])
                else:
                    prev_minute = minutes[closest_minute_idx - 1]
                    next_minute = minutes[closest_minute_idx]
                    prev_rating = ratings_over_time[closest_minute_idx - 1]
                    next_rating = ratings_over_time[closest_minute_idx]
                    interpolated_rating = prev_rating + (next_rating - prev_rating) * (minute - prev_minute) / (next_minute - prev_minute)
                    minutes.insert(closest_minute_idx, minute)
                    ratings_over_time = np.insert(ratings_over_time, closest_minute_idx, interpolated_rating)

            # Tracer le point rouge pour les buts
            if minute in goal_minutes:
                goal_rating = ratings_over_time[minutes.index(minute)]
                ax2.scatter(minute, goal_rating, color='red', s=100, zorder=5)

            # Tracer la croix rouge en gras pour les passes décisives
            if minute in assist_minutes:
                assist_rating = ratings_over_time[minutes.index(minute)]
                ax2.scatter(minute, assist_rating, color='red', s=150, zorder=5, marker='x', linewidths=3)

        # Mettre à jour le titre avec le nombre de minutes jouées
        num_minutes_played = final_minute
        ax2.set_title(f"Évolution de la note durant {num_minutes_played - first_minute_played} minutes", fontsize=16, fontweight='bold', color='white')

        ax2.set_xlabel('Minute', fontsize=12, fontweight='bold', color='white')
        ax2.set_ylabel('Note', fontsize=12, fontweight='bold', color='white')
        ax2.set_ylim(lower_bound, upper_bound)  # Ajustement dynamique
        ax2.tick_params(axis='x', colors='white')  # Changer la couleur des graduations sur l'axe X
        ax2.tick_params(axis='y', colors='white')  # Changer la couleur des graduations sur l'axe Y
        ax2.spines['bottom'].set_color('white')
        ax2.spines['left'].set_color('white')

        # Supprimer la grille
        ax2.grid(False)

        # Ajouter la légende avec une croix rouge pour passe décisive
        legend_handles = [
            plt.Line2D([0], [0], marker='o', color='w', label='But', markerfacecolor='red', markersize=10),
            plt.Line2D([0], [0], marker='x', color='red', label='Passe décisive', markersize=10, markeredgewidth=3)
        ]
        ax2.legend(handles=legend_handles, loc='upper left', fontsize=12)

        # Appliquer le fond violet à la figure et aux axes
        fig.patch.set_facecolor(background_color)

        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()

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

            # Si l'événement est une faute, la couleur doit toujours être rouge
            if event_type == 'Foul':
                if outcome == 'Successful':
                    continue
                color = 'red'
            else:
                color = color_map.get(outcome, '#6DF176')  # Default to green if outcome not recognized
            
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
    
            if event_type == 'TakeOn':
                # Carré pour les dribbles
                marker = 's'
                color = '#6DF176' if outcome == 'Successful' else 'red'
                pitch.scatter(x, y, s=200, marker=marker, color=color, edgecolor='white', linewidth=1.5, ax=ax_pitch)
    
            elif event_type in ['MissedShots', 'SavedShot', 'Goal']:
                # Ronds pour les tirs et les buts
                marker = 'o'
                color = '#6DF176' if event_type == 'Goal' else 'red'
    
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



    def _process_stats_data(self):
        stats = self.player_data.get('stats', {})

        total_possession = sum(stats.get('possession', {}).values())
        total_touches = sum(stats.get('touches', {}).values())
        total_interceptions = sum(stats.get('interceptions', {}).values())
        total_passes = sum(stats.get('passesTotal', {}).values())
        total_accurate_passes = sum(stats.get('passesAccurate', {}).values())
        total_key_passes = sum(stats.get('passesKey', {}).values())
        total_successful_tackles = sum(stats.get('tacklesTotal', {}).values())
        total_unsuccessful_tackles = sum(stats.get('tackleUnsuccesful', {}).values())
        total_dispossessed = sum(stats.get('dispossessed', {}).values())

        ratings = stats.get('ratings', {})

        # Convertir les minutes en entiers pour un tri correct
        minutes = sorted(map(int, ratings.keys()))
        ratings_over_time = [ratings[str(minute)] for minute in minutes]

        return {
            'total_possession': total_possession,
            'total_touches': total_touches,
            'total_interceptions': total_interceptions,
            'total_passes': total_passes,
            'total_accurate_passes': total_accurate_passes,
            'total_key_passes': total_key_passes,
            'total_successful_tackles': total_successful_tackles,
            'total_unsuccessful_tackles': total_unsuccessful_tackles,
            'total_dispossessed': total_dispossessed,
            'minutes': minutes,
            'ratings_over_time': ratings_over_time
        }

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
        
        
# ===== NOUVELLES FONCTIONS D'ANALYSE AVANCÉE =====

    def plot_positional_intelligence(self, save_path):
        """Analyse du positionnement tactique et de l'intelligence spatiale"""
        events = self.player_data.get('events', [])
        
        if not events:
            print(f"Aucun événement trouvé pour {self.player_data['player_name']}.")
            return

        # Séparer les phases de jeu
        possession_events = []
        defensive_events = []
        transition_events = []
        
        for event in events:
            event_type = event['type']['displayName']
            if event_type in ['Pass', 'TakeOn', 'Goal', 'MissedShots', 'SavedShot']:
                possession_events.append(event)
            elif event_type in ['Tackle', 'Interception', 'BallRecovery', 'Clearance']:
                defensive_events.append(event)
            else:
                transition_events.append(event)

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

        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        gs = GridSpec(3, 3, height_ratios=[1, 2, 2], width_ratios=[2, 2, 1])

        # Titre principal
        ax.text(0.5, 0.96, f"Intelligence Positionnelle - {self.player_data['player_name']}", 
                fontsize=24, color='white', fontweight='bold', ha='center', transform=ax.transAxes)

        # ===== TERRAIN 1: HEATMAP GLOBALE =====
        pitch1 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch1 = fig.add_subplot(gs[1, 0])
        pitch1.draw(ax=ax_pitch1)

        if all_positions:
            x_coords = [pos[0] for pos in all_positions]
            y_coords = [pos[1] for pos in all_positions]
            
            bin_statistic = pitch1.bin_statistic(x_coords, y_coords, statistic='count', bins=(15, 20))
            bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1.5)
            
            # Heatmap avec transparence
            heatmap_cmap = mcolors.LinearSegmentedColormap.from_list(
                "custom_heat", [(1, 1, 1, 0), (1, 0.6, 0, 0.8), (1, 0, 0, 1)], N=100)
            pitch1.heatmap(bin_statistic, ax=ax_pitch1, cmap=heatmap_cmap)

            # Ajouter le centre de gravité global
            if cog_all[0] is not None:
                pitch1.scatter(cog_all[0], cog_all[1], s=400, marker='X', 
                              color='yellow', edgecolor='black', linewidth=3, ax=ax_pitch1)

        ax_pitch1.set_title("Heatmap Globale + Centre de Gravité", fontsize=16, color='white', fontweight='bold')

        # ===== TERRAIN 2: PHASES DE JEU =====
        pitch2 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch2 = fig.add_subplot(gs[1, 1])
        pitch2.draw(ax=ax_pitch2)

        # Positions en possession (vert)
        if possession_positions:
            x_poss = [pos[0] for pos in possession_positions]
            y_poss = [pos[1] for pos in possession_positions]
            pitch2.scatter(x_poss, y_poss, s=60, alpha=0.7, color='#6DF176', 
                          edgecolor='white', linewidth=0.5, ax=ax_pitch2)
            
            if cog_possession[0] is not None:
                pitch2.scatter(cog_possession[0], cog_possession[1], s=300, marker='o', 
                              color='#6DF176', edgecolor='black', linewidth=2, ax=ax_pitch2)

        # Positions défensives (rouge)
        if defensive_positions:
            x_def = [pos[0] for pos in defensive_positions]
            y_def = [pos[1] for pos in defensive_positions]
            pitch2.scatter(x_def, y_def, s=60, alpha=0.7, color='red', 
                          edgecolor='white', linewidth=0.5, ax=ax_pitch2)
            
            if cog_defensive[0] is not None:
                pitch2.scatter(cog_defensive[0], cog_defensive[1], s=300, marker='s', 
                              color='red', edgecolor='black', linewidth=2, ax=ax_pitch2)

        # Légende
        legend_handles = [
            plt.Line2D([0], [0], marker='o', color='w', label='Possession', 
                      markerfacecolor='#6DF176', markersize=12),
            plt.Line2D([0], [0], marker='s', color='w', label='Défense', 
                      markerfacecolor='red', markersize=12)
        ]
        ax_pitch2.legend(handles=legend_handles, loc='upper right', fontsize=12)
        ax_pitch2.set_title("Phases de Jeu", fontsize=16, color='white', fontweight='bold')

        # ===== TERRAIN 3: ZONES TACTIQUES =====
        pitch3 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch3 = fig.add_subplot(gs[2, :2])
        pitch3.draw(ax=ax_pitch3)

        # Diviser le terrain en zones tactiques
        zones = {
            'Défense centrale': [(30, 50), (0, 33)],
            'Défense latérale': [(0, 30), (0, 33), (70, 100), (0, 33)],
            'Milieu défensif': [(30, 70), (33, 50)],
            'Milieu offensif': [(30, 70), (50, 66)],
            'Couloirs': [(0, 30), (33, 100), (70, 100), (33, 100)],
            'Zone de finition': [(30, 70), (66, 100)]
        }

        # Compter les actions par zone
        zone_counts = {}
        for event in events:
            if 'x' not in event or 'y' not in event:
                continue
            x, y = event['x'], event['y']
            
            if 30 <= x <= 70 and 66 <= y <= 100:
                zone_counts['Zone de finition'] = zone_counts.get('Zone de finition', 0) + 1
            elif 30 <= x <= 70 and 50 <= y < 66:
                zone_counts['Milieu offensif'] = zone_counts.get('Milieu offensif', 0) + 1
            elif 30 <= x <= 70 and 33 <= y < 50:
                zone_counts['Milieu défensif'] = zone_counts.get('Milieu défensif', 0) + 1
            elif 30 <= x <= 70 and 0 <= y < 33:
                zone_counts['Défense centrale'] = zone_counts.get('Défense centrale', 0) + 1
            elif (0 <= x < 30 or 70 < x <= 100) and y >= 33:
                zone_counts['Couloirs'] = zone_counts.get('Couloirs', 0) + 1
            elif (0 <= x < 30 or 70 < x <= 100) and y < 33:
                zone_counts['Défense latérale'] = zone_counts.get('Défense latérale', 0) + 1

        # Affichage des événements avec code couleur selon la densité
        max_count = max(zone_counts.values()) if zone_counts else 1
        
        for event in events:
            if 'x' not in event or 'y' not in event:
                continue
            x, y = event['x'], event['y']
            
            # Déterminer la zone et sa densité
            zone_density = 0.3  # Valeur par défaut
            if 30 <= x <= 70 and 66 <= y <= 100:
                zone_density = zone_counts.get('Zone de finition', 0) / max_count
            elif 30 <= x <= 70 and 50 <= y < 66:
                zone_density = zone_counts.get('Milieu offensif', 0) / max_count
            # ... autres zones
            
            color_intensity = min(1.0, 0.3 + zone_density * 0.7)
            pitch3.scatter(x, y, s=40, alpha=0.6, 
                          color=plt.cm.RdYlGn(color_intensity), ax=ax_pitch3)

        ax_pitch3.set_title("Répartition par Zones Tactiques", fontsize=16, color='white', fontweight='bold')

        # ===== MÉTRIQUES TEXTUELLES =====
        ax_metrics = fig.add_subplot(gs[:, 2])
        ax_metrics.axis('off')

        metrics_text = f"""
MÉTRIQUES SPATIALES

🎯 Centre de Gravité:
   X: {cog_all[0]:.1f}
   Y: {cog_all[1]:.1f}

📏 Couverture Terrain:
   Largeur: {x_range:.1f}m
   Profondeur: {y_range:.1f}m
   
🏃 Mobilité: {mobility_score:.1f}

📊 Actions par Zone:
"""
        
        # Ajouter le comptage des zones
        for zone, count in sorted(zone_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(events)) * 100 if events else 0
            metrics_text += f"   {zone}: {count} ({percentage:.1f}%)\n"

        # Analyse du profil tactique
        if zone_counts:
            total_defensive = zone_counts.get('Défense centrale', 0) + zone_counts.get('Défense latérale', 0)
            total_midfield = zone_counts.get('Milieu défensif', 0) + zone_counts.get('Milieu offensif', 0)
            total_attacking = zone_counts.get('Zone de finition', 0) + zone_counts.get('Couloirs', 0)
            
            dominant_zone = max([
                ('Défensif', total_defensive),
                ('Milieu', total_midfield), 
                ('Offensif', total_attacking)
            ], key=lambda x: x[1])
            
            metrics_text += f"\n🔍 Profil Dominant:\n   {dominant_zone[0]} ({dominant_zone[1]} actions)"

        ax_metrics.text(0.05, 0.95, metrics_text, fontsize=14, color='white', 
                       fontweight='bold', ha='left', va='top', transform=ax_metrics.transAxes)

        # Tag et source
        ax.text(0.5, 0.02, "@TarbouchData - Intelligence Positionnelle", 
                fontsize=16, color='white', fontweight='bold', ha='center', 
                transform=ax.transAxes, alpha=0.8)

        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()

    def plot_pressure_analysis(self, save_path):
        """Analyse de la gestion de la pression adverse et intensité"""
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

        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        gs = GridSpec(3, 3, height_ratios=[1, 2, 2], width_ratios=[2, 2, 1])

        # Titre principal
        ax.text(0.5, 0.96, f"Analyse de Pression - {self.player_data['player_name']}", 
                fontsize=24, color='white', fontweight='bold', ha='center', transform=ax.transAxes)

        # ===== TERRAIN 1: ACTIONS SOUS PRESSION =====
        pitch1 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch1 = fig.add_subplot(gs[1, 0])
        pitch1.draw(ax=ax_pitch1)

        # Actions sous pression (rouge/orange selon succès)
        for event in pressure_events:
            if 'x' not in event or 'y' not in event:
                continue
            x, y = event['x'], event['y']
            is_successful = event.get('outcomeType', {}).get('displayName') == 'Successful'
            
            color = '#FF6B35' if is_successful else '#FF0000'
            size = 80 if is_successful else 60
            
            pitch1.scatter(x, y, s=size, alpha=0.7, color=color, 
                          edgecolor='white', linewidth=1, ax=ax_pitch1)

        ax_pitch1.set_title(f"Actions sous Pression ({len(pressure_events)})", 
                           fontsize=16, color='white', fontweight='bold')

        # ===== TERRAIN 2: ACTIONS NORMALES =====
        pitch2 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch2 = fig.add_subplot(gs[1, 1])
        pitch2.draw(ax=ax_pitch2)

        # Actions normales (vert selon succès)
        for event in normal_events:
            if 'x' not in event or 'y' not in event:
                continue
            x, y = event['x'], event['y']
            is_successful = event.get('outcomeType', {}).get('displayName') == 'Successful'
            
            color = '#6DF176' if is_successful else '#90EE90'
            size = 60 if is_successful else 40
            
            pitch2.scatter(x, y, s=size, alpha=0.6, color=color, 
                          edgecolor='white', linewidth=0.5, ax=ax_pitch2)

        ax_pitch2.set_title(f"Actions Normales ({len(normal_events)})", 
                           fontsize=16, color='white', fontweight='bold')

        # ===== TERRAIN 3: HEATMAP COMPARATIVE =====
        pitch3 = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch3 = fig.add_subplot(gs[2, :2])
        pitch3.draw(ax=ax_pitch3)

        # Heatmap des zones de pression
        if pressure_positions:
            x_pressure = [pos[0] for pos in pressure_positions]
            y_pressure = [pos[1] for pos in pressure_positions]
            
            bin_stat_pressure = pitch3.bin_statistic(x_pressure, y_pressure, 
                                                    statistic='count', bins=(12, 16))
            bin_stat_pressure['statistic'] = gaussian_filter(bin_stat_pressure['statistic'], 1)
            
            # Heatmap rouge pour la pression
            pressure_cmap = mcolors.LinearSegmentedColormap.from_list(
                "pressure_heat", [(1, 1, 1, 0), (1, 0.4, 0, 0.6), (1, 0, 0, 0.9)], N=50)
            pitch3.heatmap(bin_stat_pressure, ax=ax_pitch3, cmap=pressure_cmap)

        ax_pitch3.set_title("Zones de Haute Pression", fontsize=16, color='white', fontweight='bold')

        # ===== GRAPHIQUES D'ANALYSE =====
        ax_analysis = fig.add_subplot(gs[:, 2])
        ax_analysis.axis('off')

        # Graphique en barres pour l'efficacité
        gs_sub = GridSpec(4, 1, figure=fig, 
                         left=0.68, right=0.98, top=0.85, bottom=0.15,
                         height_ratios=[1, 1, 1, 1])

        # 1. Efficacité comparative
        ax_eff = fig.add_subplot(gs_sub[0])
        categories = ['Sous Pression', 'Normal']
        efficiencies = [pressure_efficiency, normal_efficiency]
        colors = ['#FF6B35', '#6DF176']
        
        bars = ax_eff.bar(categories, efficiencies, color=colors, alpha=0.8, edgecolor='white')
        ax_eff.set_ylabel('Efficacité (%)', fontsize=12, color='white')
        ax_eff.set_title('Efficacité Comparative', fontsize=14, color='white', fontweight='bold')
        ax_eff.tick_params(colors='white')
        ax_eff.set_facecolor('none')
        
        # Ajouter les valeurs sur les barres
        for bar, value in zip(bars, efficiencies):
            ax_eff.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                       f'{value:.1f}%', ha='center', va='bottom', color='white', fontweight='bold')

        # 2. Types d'actions sous pression
        ax_types = fig.add_subplot(gs_sub[1])
        if pressure_types:
            top_types = sorted(pressure_types.items(), key=lambda x: x[1], reverse=True)[:5]
            type_names = [t[0][:8] for t in top_types]  # Raccourcir les noms
            type_counts = [t[1] for t in top_types]
            
            ax_types.barh(type_names, type_counts, color='#FF6B35', alpha=0.8, edgecolor='white')
            ax_types.set_xlabel('Occurrences', fontsize=12, color='white')
            ax_types.set_title('Actions sous Pression', fontsize=14, color='white', fontweight='bold')
            ax_types.tick_params(colors='white')
            ax_types.set_facecolor('none')

        # 3. Métriques détaillées
        ax_metrics = fig.add_subplot(gs_sub[2:])
        ax_metrics.axis('off')

        # Calcul du ratio de pression
        pressure_ratio = (len(pressure_events) / len(events) * 100) if events else 0
        
        # Analyse de la réaction à la pression
        if pressure_efficiency < normal_efficiency:
            pressure_reaction = "Sensible à la pression"
            reaction_color = "🔴"
        elif pressure_efficiency > normal_efficiency + 5:
            pressure_reaction = "Excellent sous pression"
            reaction_color = "🟢"
        else:
            pressure_reaction = "Stable sous pression"
            reaction_color = "🟡"

        metrics_text = f"""
📊 MÉTRIQUES DE PRESSION

{reaction_color} Profil: {pressure_reaction}

⚡ Ratio de Pression: {pressure_ratio:.1f}%

🎯 Efficacité:
   • Sous pression: {pressure_efficiency:.1f}%
   • Normal: {normal_efficiency:.1f}%
   • Différence: {pressure_efficiency - normal_efficiency:+.1f}%

📈 Volume d'Actions:
   • Pression: {pressure_total}
   • Normal: {normal_total}

🔥 Zone de Pression Max:
"""
        
        # Trouver la zone de pression maximale
        if pressure_positions:
            # Diviser en zones et compter
            zones_pressure = {'Défense': 0, 'Milieu': 0, 'Attaque': 0}
            for x, y in pressure_positions:
                if y < 33:
                    zones_pressure['Défense'] += 1
                elif y < 66:
                    zones_pressure['Milieu'] += 1
                else:
                    zones_pressure['Attaque'] += 1
            
            max_zone = max(zones_pressure.items(), key=lambda x: x[1])
            metrics_text += f"   {max_zone[0]} ({max_zone[1]} actions)"

        ax_metrics.text(0.05, 0.95, metrics_text, fontsize=12, color='white', 
                       fontweight='bold', ha='left', va='top', transform=ax_metrics.transAxes)

        # Tag et source
        ax.text(0.5, 0.02, "@TarbouchData - Analyse de Pression", 
                fontsize=16, color='white', fontweight='bold', ha='center', 
                transform=ax.transAxes, alpha=0.8)

        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()

    def plot_next_action_prediction(self, save_path):
        """Analyse des patterns et prévisibilité du joueur"""
        events = self.player_data.get('events', [])
        
        if len(events) < 10:
            print(f"Pas assez d'événements pour l'analyse prédictive de {self.player_data['player_name']}.")
            return

        # Analyser les séquences d'actions
        action_sequences = []
        for i in range(len(events) - 1):
            current_action = events[i]['type']['displayName']
            next_action = events[i + 1]['type']['displayName']
            action_sequences.append((current_action, next_action))

        # Construire la matrice de transition
        from collections import defaultdict, Counter
        transition_matrix = defaultdict(Counter)
        
        for current, next_action in action_sequences:
            transition_matrix[current][next_action] += 1

        # Calculer les probabilités
        transition_probs = {}
        for current_action, next_actions in transition_matrix.items():
            total = sum(next_actions.values())
            transition_probs[current_action] = {
                action: count / total for action, count in next_actions.items()
            }

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

        # Créer la visualisation
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        gs = GridSpec(3, 3, height_ratios=[1, 2, 2], width_ratios=[1.5, 1.5, 1])

        # Titre principal
        ax.text(0.5, 0.96, f"Analyse Prédictive - {self.player_data['player_name']}", 
                fontsize=24, color='white', fontweight='bold', ha='center', transform=ax.transAxes)

        # ===== MATRICE DE TRANSITION =====
        ax_matrix = fig.add_subplot(gs[1, 0])
        
        # Préparer les données pour la heatmap
        all_actions = list(set([action for action, _ in action_sequences] + [action for _, action in action_sequences]))
        most_common_actions = [action for action, count in Counter([a for a, _ in action_sequences]).most_common(8)]
        
        # Créer la matrice numérique
        matrix_data = np.zeros((len(most_common_actions), len(most_common_actions)))
        action_to_idx = {action: i for i, action in enumerate(most_common_actions)}
        
        for i, current_action in enumerate(most_common_actions):
            for j, next_action in enumerate(most_common_actions):
                if current_action in transition_probs and next_action in transition_probs[current_action]:
                    matrix_data[i][j] = transition_probs[current_action][next_action] * 100

        # Afficher la heatmap
        im = ax_matrix.imshow(matrix_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=50)
        
        # Configurer les labels
        ax_matrix.set_xticks(range(len(most_common_actions)))
        ax_matrix.set_yticks(range(len(most_common_actions)))
        ax_matrix.set_xticklabels([action[:8] for action in most_common_actions], 
                                 rotation=45, ha='right', fontsize=10, color='white')
        ax_matrix.set_yticklabels([action[:8] for action in most_common_actions], 
                                 fontsize=10, color='white')
        
        # Ajouter les valeurs dans les cellules
        for i in range(len(most_common_actions)):
            for j in range(len(most_common_actions)):
                if matrix_data[i][j] > 5:  # Seulement si significatif
                    ax_matrix.text(j, i, f'{matrix_data[i][j]:.0f}%', 
                                  ha='center', va='center', color='black', fontweight='bold', fontsize=8)

        ax_matrix.set_title('Matrice de Transition\n(Probabilités %)', 
                           fontsize=14, color='white', fontweight='bold')
        ax_matrix.set_xlabel('Action Suivante', fontsize=12, color='white')
        ax_matrix.set_ylabel('Action Actuelle', fontsize=12, color='white')

        # ===== TERRAIN: ZONES DE CONFORT =====
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[1, 1])
        pitch.draw(ax=ax_pitch)

        # Afficher les actions avec code couleur selon l'efficacité de la zone
        for event in events:
            if 'x' not in event or 'y' not in event:
                continue
            
            x, y = event['x'], event['y']
            
            # Déterminer la zone et sa couleur
            if y < 33:
                zone_eff = zone_efficiency.get('Défensive', 50)
                zone_color = 'Défensive'
            elif y < 66:
                zone_eff = zone_efficiency.get('Milieu', 50)
                zone_color = 'Milieu'
            else:
                zone_eff = zone_efficiency.get('Offensive', 50)
                zone_color = 'Offensive'
            
            # Couleur basée sur l'efficacité
            if zone_eff > 80:
                color = '#006400'  # Vert foncé - zone de confort
            elif zone_eff > 60:
                color = '#6DF176'  # Vert clair
            elif zone_eff > 40:
                color = '#FFD700'  # Jaune
            else:
                color = '#FF4500'  # Rouge - zone de défi
            
            pitch.scatter(x, y, s=50, alpha=0.7, color=color, 
                         edgecolor='white', linewidth=0.5, ax=ax_pitch)

        # Ajouter les zones d'efficacité
        for zone, efficiency in zone_efficiency.items():
            if zone == 'Défensive':
                y_pos = 16.5
            elif zone == 'Milieu':
                y_pos = 49.5
            else:
                y_pos = 82.5
            
            color = '#006400' if efficiency > 80 else '#6DF176' if efficiency > 60 else '#FFD700' if efficiency > 40 else '#FF4500'
            ax_pitch.text(50, y_pos, f'{zone}\n{efficiency:.0f}%', 
                         ha='center', va='center', fontsize=12, color='white', 
                         fontweight='bold', bbox=dict(boxstyle='round', facecolor=color, alpha=0.8))

        ax_pitch.set_title('Zones de Confort/Défi', fontsize=14, color='white', fontweight='bold')

        # ===== PRÉFÉRENCES DIRECTIONNELLES =====
        ax_directions = fig.add_subplot(gs[2, :2])
        
        # Graphique en secteurs pour les préférences directionnelles
        total_passes = sum(directional_preferences.values())
        if total_passes > 0:
            labels = ['Vers l\'avant', 'Latérales', 'Vers l\'arrière']
            sizes = [directional_preferences['forward'], 
                    directional_preferences['lateral'], 
                    directional_preferences['backward']]
            colors = ['#6DF176', '#FFD700', '#FF6B35']
            
            # Créer le graphique en secteurs
            wedges, texts, autotexts = ax_directions.pie(sizes, labels=labels, colors=colors, 
                                                        autopct='%1.1f%%', startangle=90,
                                                        textprops={'color': 'white', 'fontsize': 14, 'fontweight': 'bold'})
            
            # Améliorer l'apparence
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_fontweight('bold')
            
            ax_directions.set_title('Préférences Directionnelles des Passes', 
                                   fontsize=16, color='white', fontweight='bold', pad=20)

        # ===== ANALYSE PRÉDICTIVE DÉTAILLÉE =====
        ax_analysis = fig.add_subplot(gs[:, 2])
        ax_analysis.axis('off')

        # Calculer les patterns les plus fréquents
        most_common_sequences = Counter(action_sequences).most_common(5)
        
        # Calculer la prévisibilité
        total_sequences = len(action_sequences)
        predictability_score = 0
        
        for current_action, next_actions in transition_matrix.items():
            if next_actions:
                max_prob = max(next_actions.values()) / sum(next_actions.values())
                predictability_score += max_prob
        
        predictability_score = (predictability_score / len(transition_matrix)) * 100 if transition_matrix else 0

        # Analyser la diversité des actions
        action_diversity = len(set([e['type']['displayName'] for e in events]))
        
        # Évaluer le profil de joueur
        if predictability_score > 70:
            player_profile = "Très prévisible"
            profile_emoji = "🔴"
        elif predictability_score > 50:
            player_profile = "Modérément prévisible"
            profile_emoji = "🟡"
        else:
            player_profile = "Imprévisible"
            profile_emoji = "🟢"

        # Zone de confort principale
        comfort_zone = max(zone_efficiency.items(), key=lambda x: x[1]) if zone_efficiency else ("Aucune", 0)

        analysis_text = f"""
🎯 ANALYSE PRÉDICTIVE

{profile_emoji} Profil: {player_profile}

📊 Score de Prévisibilité: {predictability_score:.1f}%

🎭 Diversité d'Actions: {action_diversity} types

🏠 Zone de Confort:
   {comfort_zone[0]} ({comfort_zone[1]:.1f}% efficacité)

🔄 Séquences Fréquentes:
"""
        
        for i, ((action1, action2), count) in enumerate(most_common_sequences[:3]):
            percentage = (count / total_sequences) * 100
            analysis_text += f"   {i+1}. {action1[:8]} → {action2[:8]}\n      ({percentage:.1f}%)\n"

        # Ajouter des insights
        forward_pct = (directional_preferences['forward'] / total_passes * 100) if total_passes > 0 else 0
        
        analysis_text += f"""
📈 Style de Jeu:
   • Orientation offensive: {forward_pct:.1f}%
   • Actions totales: {len(events)}
   • Séquences analysées: {total_sequences}

🧠 Insights:
"""
        
        if forward_pct > 60:
            analysis_text += "   • Joueur progressiste\n"
        elif forward_pct < 30:
            analysis_text += "   • Joueur sécuritaire\n"
        else:
            analysis_text += "   • Joueur équilibré\n"
            
        if predictability_score > 60:
            analysis_text += "   • Patterns répétitifs\n"
        else:
            analysis_text += "   • Créativité élevée\n"

        if action_diversity > 8:
            analysis_text += "   • Polyvalence technique\n"
        else:
            analysis_text += "   • Spécialisation\n"

        ax_analysis.text(0.05, 0.95, analysis_text, fontsize=11, color='white', 
                        fontweight='bold', ha='left', va='top', transform=ax_analysis.transAxes)

        # ===== GRAPHIQUES ADDITIONNELS =====
        # Créer un sous-graphique pour les probabilités les plus élevées
        gs_sub = GridSpec(2, 1, figure=fig, 
                         left=0.68, right=0.98, top=0.45, bottom=0.15,
                         height_ratios=[1, 1])

        # Top transitions
        ax_top_trans = fig.add_subplot(gs_sub[0])
        ax_top_trans.set_facecolor('none')
        
        # Extraire les transitions les plus probables
        top_transitions = []
        for current_action, next_actions in transition_probs.items():
            for next_action, prob in next_actions.items():
                if prob > 0.2:  # Seulement les transitions > 20%
                    top_transitions.append((f"{current_action[:6]}→{next_action[:6]}", prob * 100))
        
        top_transitions = sorted(top_transitions, key=lambda x: x[1], reverse=True)[:5]
        
        if top_transitions:
            trans_names = [t[0] for t in top_transitions]
            trans_probs = [t[1] for t in top_transitions]
            
            bars = ax_top_trans.barh(trans_names, trans_probs, color='#FFD700', alpha=0.8, edgecolor='white')
            ax_top_trans.set_xlabel('Probabilité (%)', fontsize=10, color='white')
            ax_top_trans.set_title('Top Transitions', fontsize=12, color='white', fontweight='bold')
            ax_top_trans.tick_params(colors='white', labelsize=8)
            
            # Ajouter les valeurs
            for bar, value in zip(bars, trans_probs):
                ax_top_trans.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                                 f'{value:.1f}%', ha='left', va='center', color='white', fontweight='bold', fontsize=8)

        # Évolution de la prévisibilité dans le match
        ax_evolution = fig.add_subplot(gs_sub[1])
        ax_evolution.set_facecolor('none')
        
        # Calculer la prévisibilité par tranches de 15 minutes
        time_windows = [(0, 15), (15, 30), (30, 45), (45, 60), (60, 75), (75, 90)]
        predictability_evolution = []
        
        for start_min, end_min in time_windows:
            window_events = [e for e in events if start_min <= e['minute'] < end_min]
            if len(window_events) >= 3:
                window_sequences = [(window_events[i]['type']['displayName'], 
                                   window_events[i+1]['type']['displayName']) 
                                  for i in range(len(window_events)-1)]
                
                if window_sequences:
                    window_counter = Counter(window_sequences)
                    max_freq = max(window_counter.values())
                    window_predictability = (max_freq / len(window_sequences)) * 100
                    predictability_evolution.append(window_predictability)
                else:
                    predictability_evolution.append(0)
            else:
                predictability_evolution.append(0)

        if predictability_evolution and any(p > 0 for p in predictability_evolution):
            minutes = [f"{start}-{end}" for start, end in time_windows]
            ax_evolution.plot(minutes, predictability_evolution, 
                            color='#FF6B35', linewidth=3, marker='o', markersize=6)
            ax_evolution.set_ylabel('Prévisibilité (%)', fontsize=10, color='white')
            ax_evolution.set_title('Évolution Temporelle', fontsize=12, color='white', fontweight='bold')
            ax_evolution.tick_params(colors='white', labelsize=8)
            ax_evolution.tick_params(axis='x', rotation=45)
            
            # Ligne de référence
            ax_evolution.axhline(y=50, color='white', linestyle='--', alpha=0.6)

        # Tag et source
        ax.text(0.5, 0.02, "@TarbouchData - Analyse Prédictive", 
                fontsize=16, color='white', fontweight='bold', ha='center', 
                transform=ax.transAxes, alpha=0.8)

        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()

    # ===== FONCTION UTILITAIRE POUR APPELER LES NOUVELLES ANALYSES =====
    
    def generate_advanced_analysis_suite(self, save_dir="advanced_analysis"):
        """Génère toutes les analyses avancées d'un coup"""
        import os
        
        os.makedirs(save_dir, exist_ok=True)
        player_name_clean = self.player_data['player_name'].replace(' ', '_')
        
        print(f"🚀 Génération de la suite d'analyses avancées pour {self.player_data['player_name']}...")
        
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

    # ===== FONCTION BONUS: ANALYSE COMPARATIVE ENTRE PLUSIEURS JOUEURS =====
    
    def compare_players_advanced_metrics(self, other_players_data, save_path):
        """Compare les métriques avancées entre plusieurs joueurs"""
        
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
        
        # Créer la visualisation comparative
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        fig = plt.figure(figsize=(16, 10))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])

        gs = GridSpec(3, 2, height_ratios=[1, 2, 2])

        # Titre
        ax.text(0.5, 0.95, "Comparaison Avancée Multi-Joueurs", 
                fontsize=24, color='white', fontweight='bold', ha='center', transform=ax.transAxes)

        # ===== RADAR CHART COMPARATIF =====
        ax_radar = fig.add_subplot(gs[1, 0], projection='polar')
        
        # Préparer les données du radar
        metrics_names = ['Efficacité', 'Sous Pression', 'Diversité', 'Zone Confort', 'Volume']
        angles = np.linspace(0, 2 * np.pi, len(metrics_names), endpoint=False).tolist()
        angles += angles[:1]  # Fermer le cercle
        
        colors = ['#FF6B35', '#6DF176', '#FFD700', '#FF69B4', '#00CED1']
        
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
            
            ax_radar.plot(angles, values, 'o-', linewidth=2, label=player_metrics['name'], color=colors[i])
            ax_radar.fill(angles, values, alpha=0.25, color=colors[i])
        
        ax_radar.set_xticks(angles[:-1])
        ax_radar.set_xticklabels(metrics_names, color='white', fontsize=12)
        ax_radar.set_ylim(0, 100)
        ax_radar.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=10)
        ax_radar.set_title('Profils Comparatifs', color='white', fontsize=16, fontweight='bold', pad=20)

        # ===== GRAPHIQUES EN BARRES =====
        metrics_to_compare = [
            ('Taux de Réussite (%)', 'success_rate'),
            ('Ratio Pression (%)', 'pressure_ratio'),
            ('Diversité Actions', 'action_diversity'),
            ('Meilleure Zone (%)', 'best_zone_efficiency')
        ]
        
        for idx, (metric_title, metric_key) in enumerate(metrics_to_compare):
            ax_bar = fig.add_subplot(gs[1 + idx//2, 1] if idx < 2 else gs[2, idx-2])
            
            names = [p['name'][:8] for p in players_metrics]
            values = [p[metric_key] for p in players_metrics]
            
            bars = ax_bar.bar(names, values, color=colors[:len(players_metrics)], alpha=0.8, edgecolor='white')
            ax_bar.set_title(metric_title, fontsize=14, color='white', fontweight='bold')
            ax_bar.tick_params(colors='white')
            ax_bar.set_facecolor('none')
            
            # Ajouter les valeurs sur les barres
            for bar, value in zip(bars, values):
                ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                           f'{value:.1f}', ha='center', va='bottom', color='white', fontweight='bold')

        # ===== CLASSEMENT GÉNÉRAL =====
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
        
        ranking_text = "🏆 CLASSEMENT GÉNÉRAL (Score Composite)\n\n"
        for i, player in enumerate(players_metrics):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            ranking_text += f"{medal} {player['name']} - {player['composite_score']:.1f}/100\n"
            ranking_text += f"   Efficacité: {player['success_rate']:.1f}% | "
            ranking_text += f"Actions: {player['total_actions']} | "
            ranking_text += f"Diversité: {player['action_diversity']}\n\n"

        ax_ranking.text(0.05, 0.95, ranking_text, fontsize=14, color='white', 
                       fontweight='bold', ha='left', va='top', transform=ax_ranking.transAxes)

        # Tag et source
        ax.text(0.5, 0.02, "@TarbouchData - Comparaison Multi-Joueurs", 
                fontsize=16, color='white', fontweight='bold', ha='center', 
                transform=ax.transAxes, alpha=0.8)

        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none', dpi=300)
        plt.show()

        return players_metrics