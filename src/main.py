import sys
import os
from match_data_extractor import MatchDataExtractor
from player_visualizer import PlayerVisualizer

def main(url, player_name):
    extractor = MatchDataExtractor(url)
    player_data_file = extractor.extract_player_stats_and_events(player_name)

    visualizer = PlayerVisualizer(player_data_file)
    
    save_dir = os.path.join('./viz_data/', player_name.replace(" ", "_"))
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    save_path_passes = os.path.join(save_dir, f'{player_name.replace(" ", "_")}_passes_and_pie_charts.png')
    save_path_stats = os.path.join(save_dir, f'{player_name.replace(" ", "_")}_stats_visualization.png')
    save_path_defensive = os.path.join(save_dir, f'{player_name.replace(" ", "_")}_defensive_activity.png')
    save_path_offensive_pitch = os.path.join(save_dir, f'{player_name.replace(" ", "_")}_offensive_activity_pitch.png')
    save_path_offensive_goal = os.path.join(save_dir, f'{player_name.replace(" ", "_")}_offensive_activity_goal.png')
    save_path_activity = os.path.join(save_dir, f'{player_name.replace(" ", "_")}_activity_goal.png')

    visualizer.plot_passes_and_bar_charts(save_path_passes)
    #visualizer.plot_stats_visualizations(save_path_stats)
    visualizer.plot_defensive_activity(save_path_defensive)
    visualizer.plot_offensive_activity(save_path_offensive_pitch, save_path_offensive_goal)
    visualizer.plot_passes_heatmap_and_bar_charts(save_path_activity)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py <url> <player_name>")
        sys.exit(1)
    
    url = sys.argv[1]
    player_name = sys.argv[2]
    main(url, player_name)




### pour lancer le code : python src/main.py "data/Toulouse 1-3 Marseille - Ligue 1 2024_2025 Direct.html" "Amine Harit"
### python src/main.py "data/Morocco 3-0 Tanzania - Africa Cup of Nations 2023 Direct.html" "Sofyan Amrabat"
### python src/main.py "data/Morocco 3-0 Tanzania - Africa Cup of Nations 2023 Direct.html" "Abde Ezzalzouli"
### python src/main.py "data/Bayern Munich 9-2 Dinamo Zagreb - Champions League 2024_2025 Live.html" "Harry Kane"
