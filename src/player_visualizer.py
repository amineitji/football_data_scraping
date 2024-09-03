import json
import os
from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.gridspec import GridSpec

class PlayerVisualizer:
    def __init__(self, player_data_path):
        self.player_data_path = player_data_path
        self.player_data = self._load_player_data()

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
            angle = np.degrees(np.arctan2(y_end - y_start, x_end - x_start))

            if -30 <= angle <= 30:
                forward_passes.append(pas)
            elif 30 < angle < 150 or -150 < angle < -30:
                lateral_passes.append(pas)
            else:
                backward_passes.append(pas)

            if pas['outcomeType']['displayName'] == 'Successful':
                successful_passes.append(pas)
            else:
                failed_passes.append(pas)

        return forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes

    def plot_passes_and_pie_charts(self, save_path):
        events = self.player_data.get('events', [])
        passes = [event for event in events if event['type']['displayName'] == 'Pass']

        if not passes:
            print(f"Pas de passes trouvées pour {self.player_data['player_name']}. Aucun visuel généré.")
            return

        forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = self._classify_passes(passes)

        fig = plt.figure(figsize=(16, 10))
        gs = GridSpec(2, 2, width_ratios=[3, 1])

        pitch = VerticalPitch(pitch_type='opta', pitch_color='#4b0082', line_color='white')
        ax_pitch = fig.add_subplot(gs[:, 0])
        pitch.draw(ax=ax_pitch)

        for pas in passes:
            y_start = pas['x']
            x_start = pas['y']
            y_end = pas['endX']
            x_end = pas['endY']

            color = 'deepskyblue' if pas['outcomeType']['displayName'] == 'Successful' else 'red'
            pitch.arrows(y_start, x_start, y_end, x_end, width=2, headwidth=3, headlength=3, color=color, ax=ax_pitch)

        success_patch = mpatches.Patch(color='deepskyblue', label='Passe réussie')
        failed_patch = mpatches.Patch(color='red', label='Passe ratée')
        ax_pitch.legend(handles=[success_patch, failed_patch], loc='upper right', fontsize=12)

        ax_pitch.set_title(f"Passes de {self.player_data['player_name']}", fontsize=18, fontweight='bold')

        ax1 = fig.add_subplot(gs[0, 1])
        total_passes = len(passes)
        success_failure_data = [
            len(successful_passes) / total_passes,
            len(failed_passes) / total_passes,
        ]
        success_failure_labels = ['Réussies', 'Ratées']
        success_failure_colors = ['#87CEFA', '#FF4500']

        ax1.pie(success_failure_data, labels=success_failure_labels, colors=success_failure_colors, autopct='%1.1f%%', startangle=140,
                textprops={'fontsize': 14, 'fontweight': 'bold', 'color': 'black'})
        ax1.set_title("Répartition des passes réussies/ratées", fontsize=16, fontweight='bold')

        ax2 = fig.add_subplot(gs[1, 1])
        orientation_data = [
            len(forward_passes) / total_passes,
            len(lateral_passes) / total_passes,
            len(backward_passes) / total_passes,
        ]
        orientation_labels = ['Vers l\'avant', 'Latérales', 'Vers l\'arrière']
        orientation_colors = ['#98FB98', '#FFD700', '#9370DB']

        ax2.pie(orientation_data, labels=orientation_labels, colors=orientation_colors, autopct='%1.1f%%', startangle=140,
                textprops={'fontsize': 14, 'fontweight': 'bold', 'color': 'black'})
        ax2.set_title("Orientation des passes", fontsize=16, fontweight='bold')

        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()

    def plot_stats_visualizations(self, save_path):
        stats = self._process_stats_data()
    
        fig = plt.figure(figsize=(14, 12))
        gs = GridSpec(2, 1, height_ratios=[1, 1], figure=fig)
    
        # Diagramme à barres verticales pour les statistiques globales
        ax1 = fig.add_subplot(gs[0, 0])
        categories = [
            'Possession', 'Touches', 'Interceptions', 'Passes', 
            'Passes précises', 'Passes clés', 'Tacles réussis', 
            'Tacles ratés', 'Possession perdue'
        ]
        values = [
            stats['total_possession'], stats['total_touches'], stats['total_interceptions'], 
            stats['total_passes'], stats['total_accurate_passes'], stats['total_key_passes'], 
            stats['total_successful_tackles'], stats['total_unsuccessful_tackles'], stats['total_dispossessed']
        ]
        
        bars = ax1.bar(categories, values, color='mediumseagreen')
    
        # Ajouter les valeurs au-dessus de chaque barre
        for bar in bars:
            yval = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2, yval + 1, int(yval), ha='center', fontsize=12)
    
        ax1.set_ylabel('Total', fontsize=12, fontweight='bold')
        ax1.set_title(f"Les stats globales de {self.player_data['player_name']}", fontsize=16, fontweight='bold')
        ax1.set_xticklabels(categories, rotation=45, ha='right', fontsize=12)
    
        # Diagramme de l'évolution des notes (rating)
        ax2 = fig.add_subplot(gs[1, 0])
        
        # Données pour le graphique
        minutes = stats['minutes']
        ratings_over_time = stats['ratings_over_time']
        threshold = 6
    
        # Convertir les données en tableaux numpy
        ratings_over_time = np.array(ratings_over_time)
    
        # Tracer la ligne horizontale à 6
        ax2.axhline(y=threshold, color='black', linewidth=2, linestyle='--')
    
        # Remplissage des zones
        ax2.fill_between(minutes, ratings_over_time, threshold, where=(ratings_over_time >= threshold), 
                         interpolate=True, color='green', alpha=0.3)
        ax2.fill_between(minutes, ratings_over_time, threshold, where=(ratings_over_time < threshold), 
                         interpolate=True, color='red', alpha=0.3)
    
        # Tracer la courbe fluide sans marqueurs
        ax2.plot(minutes, ratings_over_time, color='dodgerblue', linewidth=2)
    
        ax2.set_xlabel('Minute', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Note', fontsize=12, fontweight='bold')
        ax2.set_title('Évolution des notes au fil du temps', fontsize=16, fontweight='bold')
        ax2.set_ylim(0, 10)
        ax2.grid(True)
    
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()

    def plot_defensive_activity(self, save_path):
        events = self.player_data.get('events', [])
        
        # Filtrage des événements défensifs
        defensive_events = [
            event for event in events if event['type']['displayName'] in ['BallRecovery', 'Challenge', 'Tackle', 'Foul']
        ]

        if not defensive_events:
            print(f"Aucune activité défensive trouvée pour {self.player_data['player_name']}. Aucun visuel généré.")
            return

        # Définir les symboles et couleurs
        symbol_map = {
            'BallRecovery': 'o',  # Rond
            'Challenge': 's',     # Carré
            'Tackle': '^',        # Triangle
            'Foul': '*',          # Étoile
        }
        color_map = {
            'Successful': 'green',
            'Unsuccessful': 'red'
        }

        fig, ax = plt.subplots(figsize=(16, 10))

        pitch = VerticalPitch(pitch_type='opta', pitch_color='#4b0082', line_color='white')
        pitch.draw(ax=ax)

        # Parcours des événements défensifs
        for event in defensive_events:
            x, y = event['x'], event['y']
            event_type = event['type']['displayName']
            outcome = event['outcomeType']['displayName'] if 'outcomeType' in event else 'Successful'  # Assume success if not stated

            marker = symbol_map[event_type]
            color = color_map.get(outcome, 'green')  # Default to green if outcome not recognized

            pitch.scatter(x, y, s=200, marker=marker, color=color, edgecolor='black', linewidth=1.5, ax=ax)

        # Création de la légende
        legend_handles = [
            mpatches.Patch(color='green', label='Succès'),
            mpatches.Patch(color='red', label='Échec'),
            plt.Line2D([0], [0], marker='o', color='w', label='Récupération de balle', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='s', color='w', label='Duel', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='^', color='w', label='Tacle', markerfacecolor='black', markersize=15),
            plt.Line2D([0], [0], marker='*', color='w', label='Faute', markerfacecolor='black', markersize=15),
        ]
        ax.legend(handles=legend_handles, loc='upper right', fontsize=12)

        ax.set_title(f"Activité défensive de {self.player_data['player_name']}", fontsize=18, fontweight='bold')

        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()

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


    def plot_offensive_activity(self, save_path_pitch, save_path_goal):
        events = self.player_data.get('events', [])

        # Filtrage des événements offensifs
        offensive_events = [
            event for event in events if event['type']['displayName'] in ['TakeOn', 'MissedShots', 'Goal']
        ]

        if not offensive_events:
            print(f"Aucune activité offensive trouvée pour {self.player_data['player_name']}. Aucun visuel généré.")
            return

        fig, ax = plt.subplots(figsize=(16, 10))
        pitch = VerticalPitch(pitch_type='opta', pitch_color='#4b0082', line_color='white')
        pitch.draw(ax=ax)

        # Variables pour les tirs
        shots = []

        for event in offensive_events:
            x, y = event['x'], event['y']
            event_type = event['type']['displayName']

            if event_type == 'TakeOn':
                marker = 'o'  # Rond pour les dribbles
                color = 'yellow' if event['outcomeType']['displayName'] == 'Successful' else 'red'
                pitch.scatter(x, y, s=200, marker=marker, color=color, edgecolor='black', linewidth=1.5, ax=ax)

            elif event_type in ['MissedShots', 'Goal']:
                outcome = event['outcomeType']['displayName']
                color = 'green' if event_type == 'Goal' else 'red'

                # Ajouter le point de tir
                pitch.scatter(x, y, s=200, color=color, edgecolor='black', linewidth=1.5, ax=ax)

                # Trouver les coordonnées de la cible (la cage)
                goalmouth_y = next((float(q['value']) for q in event['qualifiers'] if q['type']['displayName'] == 'GoalMouthY'), None)
                goalmouth_z = next((float(q['value']) for q in event['qualifiers'] if q['type']['displayName'] == 'GoalMouthZ'), None)

                if goalmouth_y is not None and goalmouth_z is not None:
                    end_x = 100  # Les tirs se terminent à la ligne de but
                    end_y = (goalmouth_y / 100) * pitch.dim.pitch_length
                    shots.append((goalmouth_y, goalmouth_z, color))  # Ajouter pour le visuel de la cage
                    pitch.arrows(x, y, end_x, end_y, width=2, headwidth=3, headlength=3, color=color, ax=ax)

        # Ajouter la légende pour l'activité offensive sur le terrain
        legend_handles = [
            mpatches.Patch(color='yellow', label='Dribble réussi'),
            mpatches.Patch(color='red', label='Dribble raté'),
            mpatches.Patch(color='green', label='But'),
            mpatches.Patch(color='red', label='Tir manqué')
        ]
        ax.legend(handles=legend_handles, loc='upper right', fontsize=12)

        ax.set_title(f"Activité offensive de {self.player_data['player_name']}", fontsize=18, fontweight='bold')

        plt.tight_layout()
        plt.savefig(save_path_pitch)
        plt.close()

        # Générer le visuel de la cage
        if shots:
            fig, ax = plt.subplots(figsize=(7.32, 2.44))  # Adapter la taille du graphique aux dimensions réelles
            ax.set_xlim(0, 7.32)  # Largeur de la cage en mètres
            ax.set_ylim(0, 2.44)  # Hauteur de la cage en mètres
            ax.set_aspect('equal')
            ax.set_title("Vue frontale des tirs")

            # Normaliser les coordonnées pour correspondre aux dimensions réelles de la cage
            for y, z, color in shots:
                # Le y est sur une échelle de 0 à 100, le z aussi, il faut donc normaliser pour les dimensions réelles
                real_y = (y / 100) * 7.32
                real_z = (z / 100) * 2.44
                ax.scatter(real_y, real_z, s=200, color=color, edgecolor='black', linewidth=1.5)

            # Supprimer les graduations
            ax.set_xticks([])
            ax.set_yticks([])

            # Dessiner les lignes de la cage
            ax.axhline(y=0, color='black')  # Bas de la cage
            ax.axhline(y=2.44, color='black')  # Haut de la cage
            ax.axvline(x=0, color='black')  # Côté gauche
            ax.axvline(x=7.32, color='black')  # Côté droit

            # Ajouter la légende pour la vue frontale des tirs
            legend_handles = [
                plt.Line2D([0], [0], marker='o', color='w', label='But', markerfacecolor='green', markersize=15, markeredgecolor='black'),
                plt.Line2D([0], [0], marker='o', color='w', label='Tir manqué', markerfacecolor='red', markersize=15, markeredgecolor='black')
            ]
            ax.legend(handles=legend_handles, loc='upper right', fontsize=12)

            plt.tight_layout()
            plt.savefig(save_path_goal)
            plt.close()
