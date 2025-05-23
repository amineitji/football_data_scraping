import sys
import os
from whoscored_data_extractor import WhoScoredDataExtractor  # Classe pour WhoScored
from sofascore_data_extractor import SofaScoreDataExtractor  # Classe pour SofaScore
from player_visualizer import PlayerVisualizer
from season_visualizer import SeasonVisualizer
from match_visualizer import MatchVisualizer

def main(url, player_name, poste, nb_passe_d):
    is_aggregate = "/players/" in url
    
    if is_aggregate:
        player_folder = os.path.join('./viz_data/aggregated/', player_name.replace(" ", "_"))
        match_name = "season_summary"
    else:
        match_name = os.path.basename(url).replace("data/", "").replace(".json", "")
        player_folder = os.path.join('./viz_data/', player_name.replace(" ", "_"))

    # Création des dossiers
    if not os.path.exists(player_folder):
        os.makedirs(player_folder)
    match_folder = os.path.join(player_folder, match_name)
    if not os.path.exists(match_folder):
        os.makedirs(match_folder)

    # Choix du bon extracteur en fonction de l'URL
    if "whoscored.com" in url:
        print(f"Extraction des données depuis WhoScored pour {player_name}")
        extractor = WhoScoredDataExtractor(url)
    elif "sofascore.com" in url:
        print(f"Extraction des données depuis SofaScore pour {player_name}")
        extractor = SofaScoreDataExtractor(url)
    else:
        print("URL non prise en charge. Utilisez une URL de WhoScored ou SofaScore.")
        sys.exit(1)

    # Extraction des données selon le type d’analyse
    if is_aggregate:
        player_data_file = extractor.extract_player_aggregate_stats(player_name)

        # Initialize the visualizer with the extracted data
        visualizer = SeasonVisualizer(player_data_file, None, "#000000", "#5a5403", "2024/2025","(WhoScored)")

        # Save paths for the various visualizations
        save_path_passes = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_passes_and_pie_charts.png')
        save_path_crosses = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_crosses_and_pie_charts.png')
        save_path_defensive = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_defensive_activity.png')
        save_path_offensive_pitch = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_offensive_activity_pitch.png')
        save_path_offensive_goal = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_offensive_activity_goal.png')
        save_path_activity = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_activity_{poste}.png')
        save_path_activity_hate = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_activity_HATE_{poste}.png')

        if poste == "GK":
            visualizer.plot_goalkeeper_activity(save_path_activity, poste)
        else:
            visualizer.plot_passes_and_bar_charts(save_path_passes)
            visualizer.plot_crosses_and_bar_charts(save_path_crosses)
            visualizer.plot_defensive_activity(save_path_defensive)
            visualizer.plot_offensive_activity(save_path_offensive_pitch, save_path_offensive_goal)
            visualizer.plot_passes_heatmap_and_bar_charts(save_path_activity, poste, nb_passe_d)
            visualizer.hate_plot_passes_heatmap_and_bar_charts(save_path_activity_hate, poste, nb_passe_d)
    else:
        player_data_file = extractor.extract_player_stats_and_events(player_name)

        # Obtenir la compétition et les couleurs
        competition, color1, color2 = extractor.get_competition_and_colors()
        match_teams = extractor.extract_match_teams()
        match_name = extractor.get_competition_from_filename()

        # Initialize the visualizer with the extracted data
        visualizer = MatchVisualizer(player_data_file, competition, color1, color2, match_name,match_teams)

        # Save paths for the various visualizations
        save_path_passes = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_passes_and_pie_charts.png')
        save_path_defensive = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_defensive_activity.png')
        save_path_offensive_pitch = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_offensive_activity_pitch.png')
        save_path_offensive_goal = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_offensive_activity_goal.png')
        save_path_activity = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_activity_{poste}.png')
        save_path_activity_sofascore = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_activity_sofascore_{poste}.png')

        # Call visualization functions only if the data source is WhoScored
        if isinstance(extractor, WhoScoredDataExtractor):
            if poste == "GK":
                visualizer.plot_goalkeeper_activity(save_path_activity, poste)
            else:
                visualizer.plot_passes_and_bar_charts(save_path_passes)
                visualizer.plot_defensive_activity(save_path_defensive)
                visualizer.plot_offensive_activity(save_path_offensive_pitch, save_path_offensive_goal)
                visualizer.plot_passes_heatmap_and_bar_charts(save_path_activity, poste, nb_passe_d)
        else:
            visualizer.plot_shots_heatmap_and_bar_charts(save_path_activity_sofascore, poste, nb_passe_d)
            print(f"Aucune visualisation disponible pour SofaScore pour {player_name}.")

if __name__ == "__main__":
    # Check if enough arguments are passed
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("Usage: python main.py <url> <player_name> <poste> [nb_passe_d]")
        sys.exit(1)

    url = sys.argv[1]
    player_name = sys.argv[2]
    poste = sys.argv[3]  # ATT, MIL, DEF
    
    # Check if the optional nb_passe_d argument is provided
    if len(sys.argv) == 5:
        nb_passe_d = int(sys.argv[4])  # Convert the optional argument to an integer
    else:
        nb_passe_d = 0  # Default value if not provided
    
    main(url, player_name, poste, nb_passe_d)
