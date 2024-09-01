import json
import os
from mplsoccer import VerticalPitch
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.gridspec import GridSpec

def load_player_data(prenom_nom):
    file_path = os.path.join('./player_data/', f'{prenom_nom}.json')
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def classify_passes(passes):
    forward_passes = []
    lateral_passes = []
    backward_passes = []
    successful_passes = []
    failed_passes = []

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

def plot_passes_and_pie_charts(player_data, save_path):
    events = player_data.get('events', [])
    passes = [event for event in events if event['type']['displayName'] == 'Pass']

    forward_passes, lateral_passes, backward_passes, successful_passes, failed_passes = classify_passes(passes)

    # Create a grid for the pitch and pie charts
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(2, 2, width_ratios=[3, 1])

    # Create the football pitch with a dark purple background
    pitch = VerticalPitch(pitch_type='opta', pitch_color='#4b0082', line_color='white')
    ax_pitch = fig.add_subplot(gs[:, 0])
    pitch.draw(ax=ax_pitch)

    # Plot the passes
    for pas in passes:
        y_start = pas['x']
        x_start = pas['y']
        y_end = pas['endX']
        x_end = pas['endY']

        color = 'deepskyblue' if pas['outcomeType']['displayName'] == 'Successful' else 'red'
        pitch.arrows(y_start, x_start, y_end, x_end,  # Invert coordinates to match the vertical pitch
                     width=2, headwidth=3, headlength=3, color=color, ax=ax_pitch)

    # Add the legend
    success_patch = mpatches.Patch(color='deepskyblue', label='Passe réussie')
    failed_patch = mpatches.Patch(color='red', label='Passe ratée')
    ax_pitch.legend(handles=[success_patch, failed_patch], loc='upper right', fontsize=12)

    ax_pitch.set_title(f"Passes de {player_data['player_name']}", fontsize=18, fontweight='bold')
    ax_pitch.set_xticks([])  # Remove x-axis ticks
    ax_pitch.set_yticks([])  # Remove y-axis ticks

    # Pie chart for successful/failed passes
    ax1 = fig.add_subplot(gs[0, 1])
    total_passes = len(passes)
    success_failure_data = [
        len(successful_passes) / total_passes,
        len(failed_passes) / total_passes,
    ]
    success_failure_labels = ['Réussies', 'Ratées']
    success_failure_colors = ['#87CEFA', '#FF4500']  # Light Sky Blue, Orange Red

    ax1.pie(success_failure_data, labels=success_failure_labels, colors=success_failure_colors, autopct='%1.1f%%', startangle=140,
            textprops={'fontsize': 14, 'fontweight': 'bold', 'color': 'black'})
    ax1.set_title("Répartition des passes réussies/ratées", fontsize=16, fontweight='bold')

    # Pie chart for pass orientation
    ax2 = fig.add_subplot(gs[1, 1])
    orientation_data = [
        len(forward_passes) / total_passes,
        len(lateral_passes) / total_passes,
        len(backward_passes) / total_passes,
    ]
    orientation_labels = ['Vers l\'avant', 'Latérales', 'Vers l\'arrière']
    orientation_colors = ['#98FB98', '#FFD700', '#9370DB']  # Pale Green, Gold, Medium Purple

    ax2.pie(orientation_data, labels=orientation_labels, colors=orientation_colors, autopct='%1.1f%%', startangle=140,
            textprops={'fontsize': 14, 'fontweight': 'bold', 'color': 'black'})
    ax2.set_title("Orientation des passes", fontsize=16, fontweight='bold')

    # Adjust layout and save the image
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

# Usage
prenom_nom = "Amine_Harit_stats"  # Replace with the name of the file without the extension
player_data = load_player_data(prenom_nom)

# Define the save path
save_dir = './viz_data/'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
save_path = os.path.join(save_dir, f'{prenom_nom}_passes_and_pie_charts_adjusted.png')

plot_passes_and_pie_charts(player_data, save_path)
