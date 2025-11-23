# visualizer.py - Version avec visualisations de l'ancien projet
import json
import os
from mplsoccer import Pitch, VerticalPitch
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.gridspec import GridSpec
import matplotlib.colors as mcolors
import matplotlib.image as mpimg
from scipy.ndimage import gaussian_filter
from player_image_downloader import PlayerProfileScraper
from collections import defaultdict, Counter


class MatchVisualizer:
    def __init__(self, player_data_path, competition, color1, color2, match_name, match_teams):
        self.player_data_path = player_data_path
        self.player_data = self._load_player_data()
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
        """Classification complète des passes"""
        forward_passes, lateral_passes, backward_passes = [], [], []
        successful_passes, failed_passes = [], []

        for pas in passes:
            x_start, y_start = pas['x'], pas['y']
            x_end, y_end = pas['endX'], pas['endY']
            
            # Calcul de l'angle
            angle = np.degrees(np.arctan2(y_end - y_start, x_end - x_start))
            
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

    def _plot_semi_circular_gauge(self, ax, label, successful_passes, total_passes):
        """Jauge semi-circulaire"""
        ax.set_facecolor('none')
        if total_passes == 0:
            total_passes = 0.001
        percentage = successful_passes / total_passes

        theta = np.linspace(np.pi, 0, 100)
        cmap = mcolors.LinearSegmentedColormap.from_list('orange', ['orange', '#6DF176'])
        color = cmap(percentage)

        ax.plot(theta, np.ones_like(theta) * 10, lw=80, color='#505050', solid_capstyle='butt')
        
        end_theta_index = int(percentage * len(theta))
        ax.plot(theta[:end_theta_index], np.ones_like(theta)[:end_theta_index] * 10, 
                lw=80, color=color, solid_capstyle='butt')

        ax.text(0, 0, f'{int(percentage * 100)}%', ha='center', va='center', fontsize=35, 
                color=color, fontweight='bold')

        ax.set_ylim(0, 10)
        ax.set_yticks([])
        ax.set_xticks([])
        ax.spines['polar'].set_visible(False)
        ax.set_title(label, fontsize=20, color="white", fontweight='bold', pad=20)

    def _add_horizontal_bar(self, ax, label, value, max_value):
        """Barre horizontale"""
        bar_height = 0.2
        filled_length = 0

        if max_value != 0:
            filled_length = value / max_value

        if 'Fautes commises' in label:
            cmap = mcolors.LinearSegmentedColormap.from_list('red', ['#FF0000', '#FF0000'])
        else:
            cmap = mcolors.LinearSegmentedColormap.from_list('orange', ['orange', '#6DF176'])

        bar_color = cmap(filled_length)

        ax.barh(0, 1, height=bar_height, color='#505050', edgecolor='none')
        ax.barh(0, filled_length, height=bar_height, color=bar_color, edgecolor='none')

        ax.text(-0.005, 0.6, label, va='center', ha='left', fontsize=20, color='white', fontweight='bold', transform=ax.transAxes)
        ax.text(1.005, 0.6, f'{value}/{max_value}', va='center', ha='right', fontsize=20, color='white', fontweight='bold', transform=ax.transAxes)

        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, 1.0)
        ax.axis('off')

    # ==================== VISUALISATION 1: PASSES + HEATMAP ====================
    def plot_passes_heatmap_and_bar_charts(self, save_path, type_data, nb_passe_d):
        """Passes avec heatmap et statistiques"""
        events = self.player_data.get('events', [])
        passes = [event for event in events if event['type']['displayName'] == 'Pass']

        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        total_passes = len(passes)

        # Événements offensifs
        offensive_events = [
            event for event in events if event['type']['displayName'] in ['TakeOn', 'MissedShots', 'SavedShot', 'Goal', 'Foul', 'Pass']
        ]

        takeons = [event for event in offensive_events if event['type']['displayName'] == 'TakeOn']
        successful_takeons = [event for event in takeons if event.get('outcomeType', {}).get('displayName') == 'Successful']
        missed_shots = [event for event in offensive_events if event['type']['displayName'] == 'MissedShots']
        saved_shots = [event for event in offensive_events if event['type']['displayName'] == 'SavedShot']
        goals = [event for event in offensive_events if event['type']['displayName'] == 'Goal']

        # Événements défensifs
        defensive_events = [
            event for event in events if event['type']['displayName'] in ['BallRecovery', 'Interception', 'Tackle', 'Foul']
        ]

        ball_recoveries = [event for event in defensive_events if event['type']['displayName'] == 'BallRecovery']
        successful_ball_recoveries = [event for event in ball_recoveries if event.get('outcomeType', {}).get('displayName') == 'Successful']
        interceptions = [event for event in defensive_events if event['type']['displayName'] == 'Interception']
        successful_interceptions = [event for event in interceptions if event.get('outcomeType', {}).get('displayName') == 'Successful']
        tackles = [event for event in defensive_events if event['type']['displayName'] == 'Tackle']
        successful_tackles = [event for event in tackles if event.get('outcomeType', {}).get('displayName') == 'Successful']
        fouls = [event for event in defensive_events if event['type']['displayName'] == 'Foul']
        committed_fouls = [event for event in fouls if event.get('outcomeType', {}).get('displayName') == 'Unsuccessful']
        submitted_fouls = [event for event in fouls if event.get('outcomeType', {}).get('displayName') == 'Successful']

        key_passes = [
            event for event in offensive_events if event['type']['displayName'] == 'Pass' and
            any(q['type']['displayName'] == 'KeyPass' for q in event.get('qualifiers', []))
        ]
        key_passes_successful = [
            event for event in key_passes if event.get('outcomeType', {}).get('displayName') == 'Successful'
        ]
    
        # Setup visuel
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        fig = plt.figure(figsize=(16, 16))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
        gs = GridSpec(7, 2, height_ratios=[1, 1, 1, 1, 4, 4, 4])

        # Photo joueur
        PlayerProfileScraper(self.player_data['player_name']).save_player_profile()
        image_path = f"data/photo/{self.player_data['player_name'].replace(' ', '_')}_profile_image.jpg"
        try:
            player_photo = mpimg.imread(image_path)
            ax_image = fig.add_subplot(gs[:4, 0])
            ax_image.imshow(player_photo, aspect='equal')
            ax_image.set_anchor('W')
            ax_image.axis('off')
        except:
            pass

        # Infos joueur
        if self.player_data["isFirstEleven"]:
            status_text = "Titulaire"
            start_minute = 0
        else:
            first_minute = min(self.player_data["stats"]["ratings"].keys())
            status_text = f'Rentré {first_minute}"'
            start_minute = first_minute

        last_minute = list(self.player_data["stats"]["ratings"].keys())[-1]
        playing_time = int(last_minute) - int(start_minute)
        
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
        ]

        for text in text_items:
            if text:
                fontsize = 16 if text == self.match_teams else 19
                ax.text(0.23, y_position, text, fontsize=fontsize, color='white', fontweight='bold', ha='left', transform=ax.transAxes)
                y_position -= y_step

        ax.text(0.425, 0.72, f"@TarbouchData", fontsize=20, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        # Barres stats
        ax_bar1 = fig.add_subplot(gs[0, 1])
        ax_bar2 = fig.add_subplot(gs[1, 1])
        ax_bar3 = fig.add_subplot(gs[2, 1])
        ax_bar4 = fig.add_subplot(gs[3, 1])

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

        priorities = {
            'DEF': ['Récuperations', 'Tacles réussis', 'Interceptions réussies', 'Passes réussies'],
            'MIL': ['Dribbles réussis', 'Passes réussies', 'Passes clés', 'Récuperations'],
            'ATT': ['Dribbles réussis', 'Tirs cadrés', 'Passes clés', 'Récuperations']
        }

        priority_stats = priorities.get(type_data, [])
        selected_stats = []

        for priority in priority_stats:
            for stat in all_stats:
                label, value, total = stat
                if label == priority and value > 0:
                    selected_stats.append(stat)
                    break
                
        if len(selected_stats) < 4:
            remaining_stats = [stat for stat in all_stats if stat not in selected_stats]
            remaining_stats = sorted(remaining_stats, key=lambda x: x[2], reverse=True)
            for stat in remaining_stats:
                if len(selected_stats) >= 4:
                    break
                selected_stats.append(stat)

        while len(selected_stats) < 4:
            selected_stats.append(("N/A", 0, 0))

        ax_bars = [ax_bar1, ax_bar2, ax_bar3, ax_bar4]
        for i in range(4):
            label, value, total = selected_stats[i]
            self._add_horizontal_bar(ax_bars[i], label, value, total)

        # Terrain gauche - Passes
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
            
        # Terrain droit - Heatmap
        ax_pitch_right = fig.add_subplot(gs[4:, 1], aspect=1)
        pitch.draw(ax=ax_pitch_right)
    
        touchs = [event for event in events]
        x_coords = [t['x'] for t in touchs]
        y_coords = [t['y'] for t in touchs]
    
        bin_statistic = pitch.bin_statistic(x_coords, y_coords, statistic='count', bins=(20, 20))
        bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)

        el_greco_cmap = mcolors.LinearSegmentedColormap.from_list(
            "Transparent-Orange-Red",
            [(1, 1, 1, 0), (1, 0.65, 0, 1), (1, 0, 0, 1)],
            N=10
        )
        pitch.heatmap(bin_statistic, ax=ax_pitch_right, cmap=el_greco_cmap)
    
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)

    # ==================== VISUALISATION 2: PASSES COLORÉES ====================
    def plot_passes_and_bar_charts(self, save_path):
        """Passes colorées par direction"""
        events = self.player_data.get('events', [])
        passes = [event for event in events if event['type']['displayName'] == 'Pass']
        
        if not passes:
            print(f"Pas de passes trouvées pour {self.player_data['player_name']}. Aucun visuel généré.")
            return
    
        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        total_passes = len(passes)

        # Setup visuel
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
    
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
        gs = GridSpec(6, 2, width_ratios=[2, 2])
    
        # Terrain
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[:, 0])
        pitch.draw(ax=ax_pitch)
    
        ax_pitch.annotate('', xy=(-0.05, 0.75), xytext=(-0.05, 0.25), xycoords='axes fraction',
                          arrowprops=dict(edgecolor='white', facecolor='none', width=10, headwidth=25, headlength=25))

        forward_count = 0 
        lateral_count = 0 
        backward_count = 0

        for pas in successful_passes:
            y_start = pas['x']
            x_start = pas['y']
            y_end = pas['endX']
            x_end = pas['endY']
            alpha_pass = 1
            
            angle = np.degrees(np.arctan2(y_end - y_start, x_end - x_start))
    
            if 30 <= angle <= 150:
                color = '#78ff00'
                forward_count += 1
            elif -150 <= angle <= -30:
                alpha_pass = 0.5
                color = '#ff3600'
                backward_count += 1
            else:
                color = '#ffb200'
                alpha_pass = 0.8
                lateral_count += 1

            pitch.arrows(y_start, x_start, y_end, x_end, width=2, headwidth=3, headlength=3, color=color, ax=ax_pitch, alpha=alpha_pass)

        p_1 = mpatches.Patch(color='#78ff00', label='Passes vers l\'avant')
        p_2 = mpatches.Patch(color='#ffb200', label='Passes latérales')
        p_3 = mpatches.Patch(color='#ff3600', label='Passes vers l\'arrière')
        ax_pitch.legend(handles=[p_1, p_2, p_3], loc='upper right', bbox_to_anchor=(1.5, 1), fontsize=12)

        ax.text(0.5, 0.96, f"Passes de {self.player_data['player_name']}", fontsize=20, color='white', fontweight='bold', ha='center', transform=ax.transAxes)
        ax.text(0.42, 0.7, f"@TarbouchData", fontsize=18, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        # Jauge et barres
        ax_gauge = fig.add_subplot(gs[1:5, 1], polar=True)
        self._plot_semi_circular_gauge(ax_gauge, "Taux de passes réussies", len(successful_passes), total_passes)
    
        ax_bar1 = fig.add_subplot(gs[3, 1])
        ax_bar2 = fig.add_subplot(gs[4, 1])
        ax_bar3 = fig.add_subplot(gs[5, 1])

        self._add_horizontal_bar(ax_bar1, 'Passes vers l\'avant', forward_count, total_passes)
        self._add_horizontal_bar(ax_bar2, 'Passes latérales', lateral_count, total_passes)
        self._add_horizontal_bar(ax_bar3, 'Passes vers l\'arrière', backward_count, total_passes)
    
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)

    # ==================== VISUALISATION 3: ACTIVITÉ DÉFENSIVE ====================
    def plot_defensive_activity(self, save_path):
        """Activité défensive"""
        events = self.player_data.get('events', [])

        defensive_events = [
            event for event in events if event['type']['displayName'] in ['BallRecovery', 'Interception', 'Tackle', 'Foul']
        ]

        if not defensive_events:
            print(f"Aucune activité défensive trouvée pour {self.player_data['player_name']}. Aucun visuel généré.")
            return

        ball_recoveries = [event for event in defensive_events if event['type']['displayName'] == 'BallRecovery']
        successful_ball_recoveries = [event for event in ball_recoveries if event.get('outcomeType', {}).get('displayName') == 'Successful']
        interceptions = [event for event in defensive_events if event['type']['displayName'] == 'Interception']
        successful_interceptions = [event for event in interceptions if event.get('outcomeType', {}).get('displayName') == 'Successful']
        tackles = [event for event in defensive_events if event['type']['displayName'] == 'Tackle']
        successful_tackles = [event for event in tackles if event.get('outcomeType', {}).get('displayName') == 'Successful']

        passes = [event for event in events if event['type']['displayName'] == 'Pass']
        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        total_passes = len(passes)

        symbol_map = {
            'BallRecovery': 'o',
            'Interception': 's',
            'Tackle': '^',
            'Foul': '*'
        }
        color_map = {
            'Successful': '#6DF176',
            'Unsuccessful': 'red'
        }

        # Setup visuel
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])

        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
        gs = GridSpec(6, 2, width_ratios=[2, 2])

        # Terrain
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[:, 0])
        pitch.draw(ax=ax_pitch)

        ax_pitch.annotate('', xy=(-0.05, 0.75), xytext=(-0.05, 0.25), xycoords='axes fraction',
                          arrowprops=dict(edgecolor='white', facecolor='none', width=10, headwidth=25, headlength=25))
        
        for event in defensive_events:
            x, y = event['x'], event['y']
            event_type = event['type']['displayName']
            outcome = event['outcomeType']['displayName'] if 'outcomeType' in event else 'Successful'
            marker = symbol_map[event_type]

            if event_type == 'Foul':
                if outcome == 'Successful':
                    continue
                color = 'red'
            else:
                color = color_map.get(outcome, '#6DF176')
            
            pitch.scatter(x, y, s=200, marker=marker, color=color, edgecolor='white', linewidth=1.5, ax=ax_pitch)

        legend_handles = [
            plt.Line2D([0], [0], marker='o', color='w', label='Récupération', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='s', color='w', label='Interception', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='^', color='w', label='Tacle', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='*', color='w', label='Faute', markerfacecolor='black', markersize=15),
        ]
        ax_pitch.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1.35, 1), fontsize=12)

        ax.text(0.5, 0.96, f"Activité défensive de {self.player_data['player_name']}", fontsize=20, color='white', fontweight='bold', ha='center', transform=ax.transAxes)
        ax.text(0.44, 0.75, f"@TarbouchData", fontsize=18, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        # Jauge et barres
        ax_gauge = fig.add_subplot(gs[1:5, 1], polar=True)
        self._plot_semi_circular_gauge(ax_gauge, "Taux de passes réussies", len(successful_passes), total_passes)

        ax_bar1 = fig.add_subplot(gs[3, 1])
        ax_bar2 = fig.add_subplot(gs[4, 1])
        ax_bar3 = fig.add_subplot(gs[5, 1])

        self._add_horizontal_bar(ax_bar1, 'Interceptions réussies', len(successful_interceptions), len(interceptions))
        self._add_horizontal_bar(ax_bar2, 'Tacles réussis', len(successful_tackles), len(tackles))
        self._add_horizontal_bar(ax_bar3, 'Récupérations réussies', len(successful_ball_recoveries), len(ball_recoveries))

        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)

    # ==================== VISUALISATION 4: ACTIVITÉ OFFENSIVE ====================
    def plot_offensive_activity(self, save_path_pitch):
        """Activité offensive"""
        events = self.player_data.get('events', [])
    
        offensive_events = [
            event for event in events if event['type']['displayName'] in ['TakeOn', 'MissedShots', 'SavedShot', 'Goal', 'Foul', 'Pass']
        ]
    
        if not offensive_events:
            print(f"Aucune activité offensive trouvée pour {self.player_data['player_name']}. Aucun visuel généré.")
            return
    
        key_passes = [
            event for event in offensive_events if event['type']['displayName'] == 'Pass' and
            any(q['type']['displayName'] == 'KeyPass' for q in event.get('qualifiers', []))
        ]
        key_passes_successful = [
            event for event in key_passes if event.get('outcomeType', {}).get('displayName') == 'Successful'
        ]
    
        takeons = [event for event in offensive_events if event['type']['displayName'] == 'TakeOn']
        successful_takeons = [event for event in takeons if event.get('outcomeType', {}).get('displayName') == 'Successful']
    
        missed_shots = [event for event in offensive_events if event['type']['displayName'] == 'MissedShots']
        saved_shots = [event for event in offensive_events if event['type']['displayName'] == 'SavedShot']
        goals = [event for event in offensive_events if event['type']['displayName'] == 'Goal']
    
        passes = [event for event in events if event['type']['displayName'] == 'Pass']
        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        total_passes = len(passes)
    
        # Setup visuel
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
    
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
        gs = GridSpec(6, 2, width_ratios=[2, 2])
    
        # Terrain
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[:, 0])
        pitch.draw(ax=ax_pitch)
    
        ax_pitch.annotate('', xy=(-0.05, 0.75), xytext=(-0.05, 0.25), xycoords='axes fraction',
                          arrowprops=dict(edgecolor='white', facecolor='none', width=10, headwidth=25, headlength=25))
    
        for event in offensive_events:
            x, y = event['x'], event['y']
            event_type = event['type']['displayName']
            outcome = event['outcomeType']['displayName']
    
            if event_type == 'TakeOn':
                marker = 's'
                color = '#6DF176' if outcome == 'Successful' else 'red'
                pitch.scatter(x, y, s=200, marker=marker, color=color, edgecolor='white', linewidth=1.5, ax=ax_pitch)
    
            elif event_type in ['MissedShots', 'SavedShot', 'Goal']:
                marker = 'o'
                color = '#6DF176' if event_type == 'Goal' else 'red'
                pitch.scatter(x, y, s=200, marker=marker, color=color, edgecolor='white', linewidth=1.5, ax=ax_pitch)
    
                goalmouth_y = next((float(q['value']) for q in event['qualifiers'] if q['type']['displayName'] == 'GoalMouthY'), None)
                if goalmouth_y is not None:
                    end_x = 100
                    end_y = (goalmouth_y / 100) * pitch.dim.pitch_length
                    pitch.arrows(x, y, end_x, end_y, width=2, headwidth=3, headlength=3, color=color, ax=ax_pitch)
    
            elif event_type == 'Foul':
                marker = '*'
                color = '#6DF176'
                if outcome == 'Successful':
                    pitch.scatter(x, y, s=200, marker=marker, color=color, edgecolor='white', linewidth=1.5, ax=ax_pitch)
    
        for pass_event in key_passes_successful:
            x_start, y_start = pass_event['x'], pass_event['y']
            x_end = next((float(q['value']) for q in pass_event['qualifiers'] if q['type']['displayName'] == 'PassEndX'), None)
            y_end = next((float(q['value']) for q in pass_event['qualifiers'] if q['type']['displayName'] == 'PassEndY'), None)
    
            if x_end is not None and y_end is not None:
                pitch.arrows(x_start, y_start, x_end, y_end, width=2, headwidth=3, headlength=3, color='#6DF176', ax=ax_pitch)
    
        legend_handles = [
            plt.Line2D([0], [0], marker='s', color='w', label='Dribble', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='o', color='w', label='Tir', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='*', color='w', label='Faute subie', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], color='#6DF176', lw=2, label='Passe clé')
        ]
        ax_pitch.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1.3, 1), fontsize=12)
    
        ax.text(0.5, 0.96, f"Activité offensive de {self.player_data['player_name']}", fontsize=20, color='white', fontweight='bold', ha='center', transform=ax.transAxes)
        ax.text(0.45, 0.75, f"@TarbouchData", fontsize=18, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        # Jauge et barres
        ax_gauge = fig.add_subplot(gs[1:5, 1], polar=True)
        self._plot_semi_circular_gauge(ax_gauge, "Taux de passes réussies", len(successful_passes), total_passes)
    
        ax_bar1 = fig.add_subplot(gs[3, 1])
        ax_bar2 = fig.add_subplot(gs[4, 1])
        ax_bar3 = fig.add_subplot(gs[5, 1])
    
        self._add_horizontal_bar(ax_bar1, 'Dribbles réussis', len(successful_takeons), len(takeons))
        self._add_horizontal_bar(ax_bar2, 'Passes clés', len(key_passes_successful), len(key_passes))      
        self._add_horizontal_bar(ax_bar3, 'Tirs cadrés', len(saved_shots) + len(goals), len(missed_shots) + len(goals) + len(saved_shots))

        plt.tight_layout()
        plt.savefig(save_path_pitch, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)

    # ==================== VISUALISATION 5: ACTIONS PROGRESSIVES ====================
    def plot_progressive_actions(self, save_path):
        """Passes progressives et courses progressives"""
        events = self.player_data.get('events', [])
        
        progressive_passes = []
        progressive_carries = []
        
        # Détection passes progressives (progression >= 10m vers l'avant)
        for e in events:
            if e.get('type', {}).get('displayName') == 'Pass' and 'x' in e:
                x_start = e.get('x', 0)
                x_end = e.get('endX', x_start)
                
                if x_end - x_start >= 10 and e.get('outcomeType', {}).get('displayName') == 'Successful':
                    progressive_passes.append(e)
        
        # Détection courses progressives (dribbles réussis)
        for e in events:
            if e.get('type', {}).get('displayName') == 'TakeOn' and 'x' in e:
                if e.get('outcomeType', {}).get('displayName') == 'Successful':
                    progressive_carries.append(e)
        
        passes = [event for event in events if event['type']['displayName'] == 'Pass']
        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        
        # Setup visuel
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
        
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
        gs = GridSpec(6, 2, width_ratios=[2, 2])
        
        # Terrain
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[:, 0])
        pitch.draw(ax=ax_pitch)
        
        ax_pitch.annotate('', xy=(-0.05, 0.75), xytext=(-0.05, 0.25), xycoords='axes fraction',
                          arrowprops=dict(edgecolor='white', facecolor='none', width=10, headwidth=25, headlength=25))
        
        # Passes progressives (flèches dorées - même taille que les autres plots)
        for pas in progressive_passes:
            if 'x' in pas and 'endX' in pas:
                y_start = pas['x']
                x_start = pas['y']
                y_end = pas['endX']
                x_end = pas['endY']
                pitch.arrows(y_start, x_start, y_end, x_end, width=3, headwidth=5, headlength=5, 
                           color='#FFD700', alpha=0.8, ax=ax_pitch, zorder=3)
        
        # Courses progressives (triangles cyan plus gros)
        for carry in progressive_carries:
            y = carry['x']
            x = carry['y']
            pitch.scatter(y, x, s=600, marker='>', color='#00FFFF', edgecolor='white', 
                        linewidth=2, ax=ax_pitch, zorder=3)
        
        legend_handles = [
            plt.Line2D([0], [0], color='#FFD700', lw=4, label='Passe progressive'),
            plt.Line2D([0], [0], marker='>', color='w', label='Course progressive', 
                      markerfacecolor='#00FFFF', markersize=15, linestyle='None'),
        ]
        ax_pitch.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1.5, 1), fontsize=12)
        
        ax.text(0.5, 0.96, f"Actions progressives de {self.player_data['player_name']}", 
               fontsize=20, color='white', fontweight='bold', ha='center', transform=ax.transAxes)
        ax.text(0.42, 0.7, f"@TarbouchData", fontsize=18, color='white', fontweight='bold', 
               ha='left', transform=ax.transAxes, alpha=0.8)
        
        # Jauge et barres
        ax_gauge = fig.add_subplot(gs[1:5, 1], polar=True)
        self._plot_semi_circular_gauge(ax_gauge, "Taux de passes réussies", 
                                      len(successful_passes), len(passes))
        
        ax_bar1 = fig.add_subplot(gs[3, 1])
        ax_bar2 = fig.add_subplot(gs[4, 1])
        ax_bar3 = fig.add_subplot(gs[5, 1])
        
        total_progressive = len(progressive_passes) + len(progressive_carries)
        
        self._add_horizontal_bar(ax_bar1, 'Passes progressives', len(progressive_passes), len(successful_passes))
        self._add_horizontal_bar(ax_bar2, 'Courses progressives', len(progressive_carries), len(progressive_carries))
        self._add_horizontal_bar(ax_bar3, 'Total progressions', total_progressive, total_progressive)
        
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)

    # ==================== VISUALISATION 6: DOMINANCE TERRAIN ====================
    def plot_zone_dominance(self, save_path):
        """Dominance par zone du terrain"""
        events = self.player_data.get('events', [])
        
        # Calcul des touches par zone
        zones = {'defensive': [], 'middle': [], 'offensive': []}
        
        for e in events:
            if 'x' in e:
                if e['x'] < 33:
                    zones['defensive'].append(e)
                elif e['x'] < 66:
                    zones['middle'].append(e)
                else:
                    zones['offensive'].append(e)
        
        total_touches = len(events)
        defensive_pct = (len(zones['defensive']) / total_touches * 100) if total_touches > 0 else 0
        middle_pct = (len(zones['middle']) / total_touches * 100) if total_touches > 0 else 0
        offensive_pct = (len(zones['offensive']) / total_touches * 100) if total_touches > 0 else 0
        
        passes = [event for event in events if event['type']['displayName'] == 'Pass']
        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)
        
        # Setup visuel
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
        
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
        gs = GridSpec(6, 2, width_ratios=[2, 2])
        
        # Terrain avec zones colorées
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[:, 0])
        pitch.draw(ax=ax_pitch)
        
        # Lignes de séparation des zones
        pitch.lines(33, 0, 33, 100, lw=3, color='white', alpha=0.5, linestyle='--', ax=ax_pitch)
        pitch.lines(66, 0, 66, 100, lw=3, color='white', alpha=0.5, linestyle='--', ax=ax_pitch)
        
        # Afficher les touches avec un code couleur par zone
        for e in zones['defensive']:
            if 'x' in e:
                pitch.scatter(e['x'], e['y'], s=100, marker='o', color='#FF6B6B', 
                            alpha=0.3, edgecolor='white', linewidth=0.5, ax=ax_pitch)
        
        for e in zones['middle']:
            if 'x' in e:
                pitch.scatter(e['x'], e['y'], s=100, marker='o', color='#FFD93D', 
                            alpha=0.3, edgecolor='white', linewidth=0.5, ax=ax_pitch)
        
        for e in zones['offensive']:
            if 'x' in e:
                pitch.scatter(e['x'], e['y'], s=100, marker='o', color='#6DF176', 
                            alpha=0.3, edgecolor='white', linewidth=0.5, ax=ax_pitch)
        
        # Annotations des zones (utiliser pitch.text() pour VerticalPitch)
        pitch.text(16.5, 50, f'ZONE\nDÉFENSIVE\n{defensive_pct:.1f}%', 
                  ha='center', va='center', fontsize=12, color='white', 
                  fontweight='bold', bbox=dict(boxstyle='round', facecolor='#FF6B6B', alpha=0.7), ax=ax_pitch)
        
        pitch.text(49.5, 50, f'ZONE\nMÉDIANE\n{middle_pct:.1f}%', 
                  ha='center', va='center', fontsize=12, color='white', 
                  fontweight='bold', bbox=dict(boxstyle='round', facecolor='#FFD93D', alpha=0.7), ax=ax_pitch)
        
        pitch.text(83, 50, f'ZONE\nOFFENSIVE\n{offensive_pct:.1f}%', 
                  ha='center', va='center', fontsize=12, color='white', 
                  fontweight='bold', bbox=dict(boxstyle='round', facecolor='#6DF176', alpha=0.7), ax=ax_pitch)
        
        legend_handles = [
            plt.Line2D([0], [0], marker='o', color='w', label='Zone défensive', 
                      markerfacecolor='#FF6B6B', markersize=15, linestyle='None'),
            plt.Line2D([0], [0], marker='o', color='w', label='Zone médiane', 
                      markerfacecolor='#FFD93D', markersize=15, linestyle='None'),
            plt.Line2D([0], [0], marker='o', color='w', label='Zone offensive', 
                      markerfacecolor='#6DF176', markersize=15, linestyle='None'),
        ]
        ax_pitch.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1.5, 1), fontsize=12)
        
        ax.text(0.5, 0.96, f"Dominance terrain de {self.player_data['player_name']}", 
               fontsize=20, color='white', fontweight='bold', ha='center', transform=ax.transAxes)
        ax.text(0.42, 0.7, f"@TarbouchData", fontsize=18, color='white', fontweight='bold', 
               ha='left', transform=ax.transAxes, alpha=0.8)
        
        # Jauge et barres
        ax_gauge = fig.add_subplot(gs[1:5, 1], polar=True)
        self._plot_semi_circular_gauge(ax_gauge, "Taux de passes réussies", 
                                      len(successful_passes), len(passes))
        
        ax_bar1 = fig.add_subplot(gs[3, 1])
        ax_bar2 = fig.add_subplot(gs[4, 1])
        ax_bar3 = fig.add_subplot(gs[5, 1])
        
        self._add_horizontal_bar(ax_bar1, 'Zone défensive', len(zones['defensive']), total_touches)
        self._add_horizontal_bar(ax_bar2, 'Zone médiane', len(zones['middle']), total_touches)
        self._add_horizontal_bar(ax_bar3, 'Zone offensive', len(zones['offensive']), total_touches)
        
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)

    def plot_player_pass_connections(self, save_path):
        """Connexions de passes du joueur vers ses partenaires principaux"""
        events = self.player_data.get('events', [])
        
        # Extraire toutes les passes
        passes = [e for e in events if e.get('type', {}).get('displayName') == 'Pass']
        
        if not passes:
            print("Aucune passe trouvée")
            return
        
        # Position moyenne du joueur
        player_x = np.mean([p['x'] for p in passes if 'x' in p])
        player_y = np.mean([p['y'] for p in passes if 'y' in p])
        
        # Analyser les récepteurs (via événement suivant)
        receivers = {}  # {playerId: {'count': int, 'successful': int, 'positions': [(x,y)]}}
        
        for i, pas in enumerate(passes):
            if pas.get('outcomeType', {}).get('displayName') != 'Successful':
                continue
                
            # Chercher l'événement suivant (même équipe)
            for next_event in events[i+1:i+5]:  # Regarder les 5 prochains événements
                if (next_event.get('teamId') == pas.get('teamId') and 
                    next_event.get('playerId') != pas.get('playerId') and
                    'x' in next_event):
                    
                    receiver_id = next_event['playerId']
                    
                    if receiver_id not in receivers:
                        receivers[receiver_id] = {'count': 0, 'successful': 0, 'positions': []}
                    
                    receivers[receiver_id]['count'] += 1
                    receivers[receiver_id]['successful'] += 1
                    receivers[receiver_id]['positions'].append((next_event['x'], next_event['y']))
                    break
        
        # Top 5 récepteurs
        top_receivers = sorted(receivers.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
        
        if not top_receivers:
            print("Aucune connexion trouvée")
            return
        
        # Setup visuel
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap_bg = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
        
        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap_bg, extent=[0, 1, 0, 1])
        gs = GridSpec(6, 2, width_ratios=[2, 2])
        
        # Terrain
        pitch = VerticalPitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[:, 0])
        pitch.draw(ax=ax_pitch)
        
        ax_pitch.annotate('', xy=(-0.05, 0.75), xytext=(-0.05, 0.25), xycoords='axes fraction',
                          arrowprops=dict(edgecolor='white', facecolor='none', width=10, headwidth=25, headlength=25))
        
        # Position moyenne du joueur (centre doré)
        pitch.scatter(player_x, player_y, s=1200, marker='o', color='#FFD700', 
                     edgecolor='white', linewidth=4, ax=ax_pitch, zorder=10)
        pitch.text(player_x, player_y, self.player_data['player_name'].split()[-1][:3].upper(), 
                  ha='center', va='center', fontsize=12, color='black', 
                  fontweight='bold', ax=ax_pitch, zorder=11)
        
        # Palette de couleurs dégradée
        cmap_arrows = mcolors.LinearSegmentedColormap.from_list('', ['#FF6B6B', '#FFD93D', '#6DF176'])
        
        # Flèches vers les récepteurs
        for idx, (receiver_id, data) in enumerate(top_receivers):
            count = data['count']
            positions = data['positions']
            
            # Position moyenne du récepteur
            rec_x = np.mean([p[0] for p in positions])
            rec_y = np.mean([p[1] for p in positions])
            
            # Couleur selon le rang (1er = vert, 5e = rouge)
            color = cmap_arrows(1 - idx / 5)
            
            # Épaisseur proportionnelle au nombre de passes
            width = 2 + (count / max([r[1]['count'] for r in top_receivers]) * 4)
            
            # Flèche
            pitch.arrows(player_x, player_y, rec_x, rec_y, 
                       width=width, headwidth=8, headlength=8,
                       color=color, alpha=0.8, ax=ax_pitch, zorder=5)
            
            # Position du récepteur
            pitch.scatter(rec_x, rec_y, s=600, marker='o', color=color,
                        edgecolor='white', linewidth=3, ax=ax_pitch, zorder=8)
            
            # Label avec nombre de passes
            pitch.text(rec_x, rec_y, f"{count}", ha='center', va='center', 
                     fontsize=14, color='white', fontweight='bold', ax=ax_pitch, zorder=9)
        
        # Titre et signature
        ax.text(0.5, 0.96, f"Connexions de passes de {self.player_data['player_name']}", 
               fontsize=20, color='white', fontweight='bold', ha='center', transform=ax.transAxes)
        ax.text(0.42, 0.7, f"@TarbouchData", fontsize=18, color='white', fontweight='bold', 
               ha='left', transform=ax.transAxes, alpha=0.8)
        
        # Stats à droite
        total_passes = len(passes)
        successful_passes = len([p for p in passes if p.get('outcomeType', {}).get('displayName') == 'Successful'])
        success_rate = (successful_passes / total_passes * 100) if total_passes > 0 else 0
        
        # Jauge semi-circulaire
        ax_gauge = fig.add_subplot(gs[1:4, 1], polar=True)
        self._plot_semi_circular_gauge(ax_gauge, "Taux de réussite", successful_passes, total_passes)
        
        # Barres avec top 3 récepteurs
        ax_bar1 = fig.add_subplot(gs[3, 1])
        ax_bar2 = fig.add_subplot(gs[4, 1])
        ax_bar3 = fig.add_subplot(gs[5, 1])
        
        bars = [ax_bar1, ax_bar2, ax_bar3]
        for i in range(min(3, len(top_receivers))):
            receiver_id, data = top_receivers[i]
            count = data['count']
            max_count = top_receivers[0][1]['count']
            self._add_horizontal_bar(bars[i], f"Partenaire #{i+1}", count, max_count)
        
        # Remplir les barres vides si < 3 récepteurs
        for i in range(len(top_receivers), 3):
            bars[i].axis('off')
        
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)


# ==================== SEASON VISUALIZER ====================
class SeasonVisualizer:
    def __init__(self, player_data_path, competition, color1, color2, match_name, match_teams):
        self.player_data_path = player_data_path
        self.player_data = self._load_player_data()
        self.competition = competition
        self.color1 = color1
        self.color2 = color2
        self.match_name = match_name
        self.match_teams = match_teams

    def _load_player_data(self):
        with open(self.player_data_path, 'r') as file:
            data = json.load(file)
        return data

    def _add_horizontal_bar(self, ax, label, value, max_value):
        bar_height = 0.2
        filled_length = (value / max_value) if max_value != 0 else 0
        cmap = mcolors.LinearSegmentedColormap.from_list('orange', ['orange', '#6DF176'])
        bar_color = cmap(filled_length)
        ax.barh(0, 1, height=bar_height, color='#505050', edgecolor='none')
        ax.barh(0, filled_length, height=bar_height, color=bar_color, edgecolor='none')
        ax.text(-0.005, 0.6, label, va='center', ha='left', fontsize=20, color='white', fontweight='bold', transform=ax.transAxes)
        ax.text(1.005, 0.6, f'{value}/{max_value}', va='center', ha='right', fontsize=20, color='white', fontweight='bold', transform=ax.transAxes)
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, 1.0)
        ax.axis('off')

    def plot_passes_heatmap_and_bar_charts(self, save_path, type_data, nb_passe_d):
        """Visualisation saison - Tous événements réussis"""
        if not self.player_data:
            print("Erreur: Données non chargées")
            return

        total_matches = 1
        events = self.player_data.get('events', [])
        
        offensive_events = [e for e in events if e.get('type', {}).get('displayName') in ['TakeOn', 'Goal', 'Pass']]
        takeons = [e for e in offensive_events if e['type']['displayName'] == 'TakeOn']
        successful_takeons = [e for e in takeons if e.get('outcomeType', {}).get('displayName') == 'Successful']
        goals = [e for e in offensive_events if e['type']['displayName'] == 'Goal']

        defensive_events = [e for e in events if e.get('type', {}).get('displayName') in ['BallRecovery', 'Interception']]
        ball_recoveries = [e for e in defensive_events if e['type']['displayName'] == 'BallRecovery']
        successful_ball_recoveries = [e for e in ball_recoveries if e.get('outcomeType', {}).get('displayName') == 'Successful']
        interceptions = [e for e in defensive_events if e['type']['displayName'] == 'Interception']
        successful_interceptions = [e for e in interceptions if e.get('outcomeType', {}).get('displayName') == 'Successful']

        key_passes = [e for e in offensive_events if e['type']['displayName'] == 'Pass' and any(q['type']['displayName'] == 'KeyPass' for q in e.get('qualifiers', []))]
        key_passes_successful = [e for e in key_passes if e.get('outcomeType', {}).get('displayName') == 'Successful']

        fig = plt.figure(figsize=(16, 16))
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
        gs = GridSpec(7, 2, height_ratios=[1, 1, 1, 1, 4, 4, 4])

        image_path = PlayerProfileScraper(self.player_data['player_name']).save_player_profile()
        try:
            player_photo = mpimg.imread(image_path)
            ax_image = fig.add_subplot(gs[:4, 0])
            ax_image.imshow(player_photo, aspect='equal')
            ax_image.set_anchor('W')
            ax_image.axis('off')
        except:
            pass

        y_position = 0.96
        y_step = 0.03
        text_items = [
            f"{self.player_data['player_name']}",
            f"Saison {self.match_name}",
            f"{len(goals)} but(s)" if len(goals) >= 1 else None,
            f"{total_matches} match(s)",
        ]

        for text in text_items:
            if text:
                ax.text(0.23, y_position, text, fontsize=19, color='white', fontweight='bold', ha='left', transform=ax.transAxes)
                y_position -= y_step

        ax.text(0.425, 0.72, f"@TarbouchData", fontsize=20, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        ax_bar1 = fig.add_subplot(gs[0, 1])
        ax_bar2 = fig.add_subplot(gs[1, 1])
        ax_bar3 = fig.add_subplot(gs[2, 1])
        ax_bar4 = fig.add_subplot(gs[3, 1])

        selected_stats = [
            ("Buts", len(goals), len(goals)),
            ('Dribbles', len(successful_takeons), len(successful_takeons)),
            ('Passes clés', len(key_passes_successful), len(key_passes_successful)),
            ('Récuperations', len(successful_ball_recoveries), len(successful_ball_recoveries)),
        ]

        ax_bars = [ax_bar1, ax_bar2, ax_bar3, ax_bar4]
        for i in range(4):
            label, value, total = selected_stats[i]
            self._add_horizontal_bar(ax_bars[i], label, value, max(total, 1))

        pitch = Pitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[4:, :])
        pitch.draw(ax=ax_pitch)
        
        color_success = "#78ff00"
        marker_size = 600

        for e in successful_takeons:
            if 'x' in e:
                pitch.scatter(e['x'], e['y'], s=marker_size, marker='s', color=color_success, edgecolor='white', linewidth=2, ax=ax_pitch)

        for e in goals:
            if 'x' in e:
                pitch.scatter(e['x'], e['y'], s=marker_size, marker='o', color=color_success, edgecolor='white', linewidth=2, ax=ax_pitch)

        for e in successful_interceptions:
            if 'x' in e:
                pitch.scatter(e['x'], e['y'], s=marker_size, marker='*', color=color_success, edgecolor='white', linewidth=2, ax=ax_pitch)

        for e in successful_ball_recoveries:
            if 'x' in e:
                pitch.scatter(e['x'], e['y'], s=marker_size, marker='P', color=color_success, edgecolor='white', linewidth=2, ax=ax_pitch)

        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)

    def plot_progressive_actions(self, save_path):
        """Passes progressives et courses progressives - Saison"""
        events = self.player_data.get('events', [])
        
        progressive_passes = []
        progressive_carries = []
        
        # Détection passes progressives (progression >= 10m vers l'avant)
        for e in events:
            if e.get('type', {}).get('displayName') == 'Pass' and 'x' in e:
                x_start = e.get('x', 0)
                x_end = e.get('endX', x_start)
                
                if x_end - x_start >= 10 and e.get('outcomeType', {}).get('displayName') == 'Successful':
                    progressive_passes.append(e)
        
        # Détection courses progressives (dribbles réussis)
        for e in events:
            if e.get('type', {}).get('displayName') == 'TakeOn' and 'x' in e:
                if e.get('outcomeType', {}).get('displayName') == 'Successful':
                    progressive_carries.append(e)
        
        # Setup visuel
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
        
        fig = plt.figure(figsize=(16, 16))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
        gs = GridSpec(7, 2, height_ratios=[1, 1, 1, 1, 4, 4, 4])
        
        # Photo joueur
        image_path = PlayerProfileScraper(self.player_data['player_name']).save_player_profile()
        try:
            player_photo = mpimg.imread(image_path)
            ax_image = fig.add_subplot(gs[:4, 0])
            ax_image.imshow(player_photo, aspect='equal')
            ax_image.set_anchor('W')
            ax_image.axis('off')
        except:
            pass

        # Infos
        y_position = 0.96
        y_step = 0.03
        text_items = [
            f"{self.player_data['player_name']}",
            f"Saison {self.match_name}",
            f"{len(progressive_passes)} passes progressives",
            f"{len(progressive_carries)} courses progressives",
        ]

        for text in text_items:
            if text:
                ax.text(0.23, y_position, text, fontsize=19, color='white', fontweight='bold', ha='left', transform=ax.transAxes)
                y_position -= y_step

        ax.text(0.425, 0.72, f"@TarbouchData", fontsize=20, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        # Barres stats
        ax_bar1 = fig.add_subplot(gs[0, 1])
        ax_bar2 = fig.add_subplot(gs[1, 1])
        ax_bar3 = fig.add_subplot(gs[2, 1])
        ax_bar4 = fig.add_subplot(gs[3, 1])

        total_progressive = len(progressive_passes) + len(progressive_carries)
        
        selected_stats = [
            ("Passes progressives", len(progressive_passes), len(progressive_passes)),
            ('Courses progressives', len(progressive_carries), len(progressive_carries)),
            ('Total progressions', total_progressive, total_progressive),
            ('N/A', 0, 0),
        ]

        ax_bars = [ax_bar1, ax_bar2, ax_bar3, ax_bar4]
        for i in range(4):
            label, value, total = selected_stats[i]
            if total > 0:
                self._add_horizontal_bar(ax_bars[i], label, value, max(total, 1))
        
        # Terrain
        pitch = Pitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[4:, :])
        pitch.draw(ax=ax_pitch)
        
        ax_pitch.annotate('', xy=(0.75, 0.01), xytext=(0.25, 0.01), xycoords='axes fraction',
                          arrowprops=dict(edgecolor='white', facecolor='none', width=10, headwidth=25, headlength=25))
        
        # Passes progressives (flèches dorées)
        for pas in progressive_passes:
            if 'x' in pas and 'endX' in pas:
                x_start = pas['x']
                y_start = pas['y']
                x_end = pas['endX']
                y_end = pas['endY']
                pitch.arrows(x_start, y_start, x_end, y_end, width=4, headwidth=6, headlength=6, 
                           color='#FFD700', alpha=0.6, ax=ax_pitch, zorder=3)
        
        # Courses progressives (triangles cyan)
        for carry in progressive_carries:
            x = carry['x']
            y = carry['y']
            pitch.scatter(x, y, s=600, marker='>', color='#00FFFF', edgecolor='white', 
                        linewidth=2, ax=ax_pitch, zorder=3)
        
        legend_handles = [
            plt.Line2D([0], [0], color='#FFD700', lw=4, label='Passe progressive'),
            plt.Line2D([0], [0], marker='>', color='w', label='Course progressive', 
                      markerfacecolor='#00FFFF', markersize=25, linestyle='None'),
        ]
        ax_pitch.legend(handles=legend_handles, loc='upper center', bbox_to_anchor=(0.5, 0.96), ncol=2, fontsize=12)
        
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)

    def plot_zone_dominance(self, save_path):
        """Dominance par zone du terrain - Saison"""
        events = self.player_data.get('events', [])
        
        # Calcul des touches par zone
        zones = {'defensive': [], 'middle': [], 'offensive': []}
        
        for e in events:
            if 'x' in e:
                if e['x'] < 33:
                    zones['defensive'].append(e)
                elif e['x'] < 66:
                    zones['middle'].append(e)
                else:
                    zones['offensive'].append(e)
        
        total_touches = len(events)
        defensive_pct = (len(zones['defensive']) / total_touches * 100) if total_touches > 0 else 0
        middle_pct = (len(zones['middle']) / total_touches * 100) if total_touches > 0 else 0
        offensive_pct = (len(zones['offensive']) / total_touches * 100) if total_touches > 0 else 0
        
        # Setup visuel
        gradient = np.linspace(0, 1, 256).reshape(-1, 1)
        gradient = np.hstack((gradient, gradient))
        cmap = mcolors.LinearSegmentedColormap.from_list("", [self.color1, self.color2])
        
        fig = plt.figure(figsize=(16, 16))
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')
        ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0, 1, 0, 1])
        gs = GridSpec(7, 2, height_ratios=[1, 1, 1, 1, 4, 4, 4])
        
        # Photo joueur
        image_path = PlayerProfileScraper(self.player_data['player_name']).save_player_profile()
        try:
            player_photo = mpimg.imread(image_path)
            ax_image = fig.add_subplot(gs[:4, 0])
            ax_image.imshow(player_photo, aspect='equal')
            ax_image.set_anchor('W')
            ax_image.axis('off')
        except:
            pass

        # Infos
        y_position = 0.96
        y_step = 0.03
        text_items = [
            f"{self.player_data['player_name']}",
            f"Saison {self.match_name}",
            f"Zone défensive: {defensive_pct:.1f}%",
            f"Zone médiane: {middle_pct:.1f}%",
            f"Zone offensive: {offensive_pct:.1f}%",
        ]

        for text in text_items:
            if text:
                ax.text(0.23, y_position, text, fontsize=19, color='white', fontweight='bold', ha='left', transform=ax.transAxes)
                y_position -= y_step

        ax.text(0.425, 0.72, f"@TarbouchData", fontsize=20, color='white', fontweight='bold', ha='left', transform=ax.transAxes, alpha=0.8)

        # Barres stats
        ax_bar1 = fig.add_subplot(gs[0, 1])
        ax_bar2 = fig.add_subplot(gs[1, 1])
        ax_bar3 = fig.add_subplot(gs[2, 1])
        ax_bar4 = fig.add_subplot(gs[3, 1])

        selected_stats = [
            ("Zone défensive", len(zones['defensive']), total_touches),
            ('Zone médiane', len(zones['middle']), total_touches),
            ('Zone offensive', len(zones['offensive']), total_touches),
            ('Total touches', total_touches, total_touches),
        ]

        ax_bars = [ax_bar1, ax_bar2, ax_bar3, ax_bar4]
        for i in range(4):
            label, value, total = selected_stats[i]
            self._add_horizontal_bar(ax_bars[i], label, value, max(total, 1))
        
        # Terrain avec zones colorées
        pitch = Pitch(pitch_type='opta', pitch_color='none', line_color='white', linewidth=2)
        ax_pitch = fig.add_subplot(gs[4:, :])
        pitch.draw(ax=ax_pitch)
        
        # Lignes de séparation des zones
        pitch.lines(33, 0, 33, 100, lw=3, color='white', alpha=0.5, linestyle='--', ax=ax_pitch)
        pitch.lines(66, 0, 66, 100, lw=3, color='white', alpha=0.5, linestyle='--', ax=ax_pitch)
        
        # Afficher les touches avec un code couleur par zone
        for e in zones['defensive']:
            if 'x' in e:
                pitch.scatter(e['x'], e['y'], s=150, marker='o', color='#FF6B6B', 
                            alpha=0.3, edgecolor='white', linewidth=0.5, ax=ax_pitch)
        
        for e in zones['middle']:
            if 'x' in e:
                pitch.scatter(e['x'], e['y'], s=150, marker='o', color='#FFD93D', 
                            alpha=0.3, edgecolor='white', linewidth=0.5, ax=ax_pitch)
        
        for e in zones['offensive']:
            if 'x' in e:
                pitch.scatter(e['x'], e['y'], s=150, marker='o', color='#6DF176', 
                            alpha=0.3, edgecolor='white', linewidth=0.5, ax=ax_pitch)
        
        # Annotations des zones (utiliser pitch.text() pour VerticalPitch)
        pitch.text(16.5, 50, f'ZONE\nDÉFENSIVE\n{defensive_pct:.1f}%', 
                  ha='center', va='center', fontsize=12, color='white', 
                  fontweight='bold', bbox=dict(boxstyle='round', facecolor='#FF6B6B', alpha=0.7), ax=ax_pitch)
        
        pitch.text(49.5, 50, f'ZONE\nMÉDIANE\n{middle_pct:.1f}%', 
                  ha='center', va='center', fontsize=12, color='white', 
                  fontweight='bold', bbox=dict(boxstyle='round', facecolor='#FFD93D', alpha=0.7), ax=ax_pitch)
        
        pitch.text(83, 50, f'ZONE\nOFFENSIVE\n{offensive_pct:.1f}%', 
                  ha='center', va='center', fontsize=12, color='white', 
                  fontweight='bold', bbox=dict(boxstyle='round', facecolor='#6DF176', alpha=0.7), ax=ax_pitch)
        
        legend_handles = [
            plt.Line2D([0], [0], marker='o', color='w', label='Zone défensive', 
                      markerfacecolor='#FF6B6B', markersize=25, linestyle='None'),
            plt.Line2D([0], [0], marker='o', color='w', label='Zone médiane', 
                      markerfacecolor='#FFD93D', markersize=25, linestyle='None'),
            plt.Line2D([0], [0], marker='o', color='w', label='Zone offensive', 
                      markerfacecolor='#6DF176', markersize=25, linestyle='None'),
        ]
        ax_pitch.legend(handles=legend_handles, loc='upper center', bbox_to_anchor=(0.5, 0.96), ncol=3, fontsize=12)
        
        plt.tight_layout()
        plt.savefig(save_path, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close(fig)


# ==================== AUTRES VISUALIZERS (STUBS) ====================
class PlayerDuelVisualizer:
    def __init__(self, player_data_path, competition, color1, color2, match_name, match_teams):
        pass
    def plot_passes_heatmap_and_bar_charts(self, save_path, type_data, nb_passe_d):
        print("PlayerDuelVisualizer: Non implémenté")

class PlayerDuoVisualizer:
    def __init__(self, player_data_path, competition, color1, color2, match_name, match_teams):
        pass
    def plot_passes_heatmap_and_bar_charts(self, save_path, type_data, nb_passe_d):
        print("PlayerDuoVisualizer: Non implémenté")

class TeamPassNetworkVisualizer:
    def __init__(self, match_data, team_name, competition, color1, color2):
        pass
    def plot_pass_network(self, save_path):
        print("TeamPassNetworkVisualizer: Non implémenté")