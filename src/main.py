import sys
import os
from match_data_extractor import MatchDataExtractor
from player_visualizer import PlayerVisualizer

def main(url, player_name, poste):
    # Extract the match name from the url by removing "data/" and ".json"
    match_name = os.path.basename(url).replace("data/", "").replace(".json", "")
    
    # Create the player's folder if it doesn't exist
    player_folder = os.path.join('./viz_data/', player_name.replace(" ", "_"))
    if not os.path.exists(player_folder):
        os.makedirs(player_folder)
    
    # Create the match folder inside the player's folder
    match_folder = os.path.join(player_folder, match_name)
    if not os.path.exists(match_folder):
        os.makedirs(match_folder)
    
    # Extract player data
    extractor = MatchDataExtractor(url)
    player_data_file = extractor.extract_player_stats_and_events(player_name)

    # Initialize the visualizer with the extracted data
    visualizer = PlayerVisualizer(player_data_file, url)
    
    # Save paths for the various visualizations
    save_path_passes = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_passes_and_pie_charts.png')
    save_path_stats = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_stats_visualization.png')
    save_path_defensive = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_defensive_activity.png')
    save_path_offensive_pitch = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_offensive_activity_pitch.png')
    save_path_offensive_goal = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_offensive_activity_goal.png')
    save_path_activity = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_activity_{poste}.png')

    # Generate and save visualizations
    visualizer.plot_passes_and_bar_charts(save_path_passes)
    visualizer.plot_defensive_activity(save_path_defensive)
    visualizer.plot_offensive_activity(save_path_offensive_pitch, save_path_offensive_goal)
    visualizer.plot_passes_heatmap_and_bar_charts(save_path_activity, poste)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python main.py <url> <player_name> <poste>")
        sys.exit(1)
    
    url = sys.argv[1]
    player_name = sys.argv[2]
    poste = sys.argv[3] # ATT, MIL, DEF
    main(url, player_name, poste)
