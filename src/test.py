import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def draw_fifa_style_bar(ax, value, max_value=100, label='', low_threshold=50, high_threshold=75):
    """
    Draws a FIFA style attribute bar with thresholds for coloring the bar.
    
    Parameters:
    - ax: Matplotlib axis to draw the bar on.
    - value: The current value of the attribute.
    - max_value: The maximum possible value (default is 100).
    - label: The label to show next to the bar.
    - low_threshold: The threshold below which the bar is red.
    - high_threshold: The threshold above which the bar is green.
    """
    # Bar dimensions
    bar_height = 0.2
    bar_length = 8.0  # Width of the bar in arbitrary units
    
    # Calculate the filled portion of the bar
    filled_length = bar_length * (value / max_value)

    # Determine the bar color based on the thresholds
    if value < low_threshold:
        bar_color = 'red'
    elif value < high_threshold:
        bar_color = 'yellow'
    else:
        bar_color = 'green'

    # Add a background bar (gray) for context
    bbox_background = patches.FancyBboxPatch((0, -bar_height / 2), bar_length, bar_height, 
                                             boxstyle="round,pad=0.1", color='#505050', ec="none")
    ax.add_patch(bbox_background)

    # Add a filled bar for the actual value
    bbox_filled = patches.FancyBboxPatch((0, -bar_height / 2), filled_length, bar_height, 
                                         boxstyle="round,pad=0.1", color=bar_color, ec="none")
    ax.add_patch(bbox_filled)

    # Add the label and value as text above the bar
    ax.text(0, 0.7, label, va='center', ha='left', fontsize=12, color='#D3D3D3', fontweight='bold')
    ax.text(bar_length, 0.7, f'{int(value)}', va='center', ha='right', fontsize=12, color='#D3D3D3', fontweight='bold')

    # Remove axes for clean look
    ax.set_xlim(0, bar_length)
    ax.set_ylim(-1, 1)
    ax.axis('off')

def draw_fifa_semi_circular_bar(ax, value, max_value=100, label='', low_threshold=50, high_threshold=75):
    """
    Draws a semi-circular FIFA style gauge with the arc starting from 0° to 180°, with reduced thickness.
    
    Parameters:
    - ax: Matplotlib axis to draw the semi-circular bar on.
    - value: The current value of the attribute.
    - max_value: The maximum possible value (default is 100).
    - label: The label to show below the gauge.
    - low_threshold: The threshold below which the bar is red.
    - high_threshold: The threshold above which the bar is green.
    """
    # Calculate the angle corresponding to the value
    theta = np.linspace(0, np.pi, 100)
    radius = 1.0
    
    # Create a background semi-circle (gauge background)
    ax.plot(np.cos(theta), np.sin(theta) - 1.5, color='#505050', lw=15, solid_capstyle='round')  # Lower the position
    
    # Determine the filled portion of the gauge based on value
    end_angle = np.pi * (value / max_value)
    
    # Determine color
    if value < low_threshold:
        gauge_color = 'red'
    elif value < high_threshold:
        gauge_color = 'yellow'
    else:
        gauge_color = 'green'
    
    # Create the filled portion of the gauge
    theta_filled = np.linspace(0, end_angle, 100)
    ax.plot(np.cos(theta_filled), np.sin(theta_filled) - 1.5, color=gauge_color, lw=15, solid_capstyle='round')  # Lower the position
    
    # Add label and value
    ax.text(0, -2.5, label, va='center', ha='center', fontsize=12, color='#D3D3D3', fontweight='bold')
    ax.text(0, -2.9, f'{int(value)}', va='center', ha='center', fontsize=12, color='#D3D3D3', fontweight='bold')
    
    # Adjust the axis limits for more space (move the bar down)
    ax.set_xlim(-2, 2)
    ax.set_ylim(-3, 1)  # Lower the ylim to move everything down
    ax.axis('off')

def create_single_semi_circular_bar(save_path):
    # Create a single semi-circular bar
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={'aspect': 'equal'})
    
    # Define a single value and label
    value = 82  # Sample value
    label = 'Acceleration'

    # Draw a single semi-circular bar
    draw_fifa_semi_circular_bar(ax, value=value, max_value=100, label=label, low_threshold=50, high_threshold=75)

    # Set dark figure background
    fig.patch.set_facecolor('#1E1E1E')  # Darker background for the figure

    # Save the plot to the specified path
    plt.savefig(save_path, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()

def create_multiple_fifa_bars(save_path):
    # Example with multiple linear bars
    fig, axs = plt.subplots(nrows=5, figsize=(10, 6))  # Ajustement de la hauteur pour éviter le chevauchement
    values = [82, 47, 33, 65, 90]  # Sample attribute values
    labels = ['Acceleration', 'Crossing', 'Def. Awareness', 'Short Pass', 'Pace']

    for i, ax in enumerate(axs):
        draw_fifa_style_bar(ax, value=values[i], max_value=100, label=labels[i], low_threshold=50, high_threshold=75)

    # Set dark figure background
    fig.patch.set_facecolor('#1E1E1E')  # Darker background for the figure

    # Save the plot to the specified path
    plt.tight_layout(pad=2)  # Ajout d'espacement entre les sous-graphiques
    plt.savefig(save_path, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()

# Save the image with normal bars
save_path_normal = 'fifa_multiple_bars.png'
create_multiple_fifa_bars(save_path_normal)

# Save the image with a single semi-circular bar
save_path_single_semi_circular = 'fifa_single_semi_circular_bar.png'
create_single_semi_circular_bar(save_path_single_semi_circular)
