import sys
import os
import traceback
import json
from whoscored_data_extractor import WhoScoredDataExtractor  # Classe pour WhoScored
from sofascore_data_extractor import SofaScoreDataExtractor  # Classe pour SofaScore
from player_visualizer import PlayerVisualizer
from season_visualizer import SeasonVisualizer
from match_visualizer import MatchVisualizer

def main(url, player_name, poste, nb_passe_d, advanced_analysis=False):
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

    # Extraction des données selon le type d'analyse
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
            
                        # ➕ Ajouter ici les analyses avancées si demandées
            if advanced_analysis:
                try:
                    print("\n🚀 Génération des analyses avancées pour les données agrégées...")
                    advanced_folder = os.path.join(match_folder, "advanced_analysis")
                    os.makedirs(advanced_folder, exist_ok=True)

                    player_name_clean = player_name.replace(" ", "_")

                    print("🧠 Génération de l'analyse spatiale intelligente...")
                    save_path_spatial = os.path.join(advanced_folder, f'{player_name_clean}_spatial_intelligence.png')
                    visualizer.plot_positional_intelligence(save_path_spatial)
                    print("✅ Analyse spatiale générée")

                    print("⚡ Génération de l'analyse de pression...")
                    save_path_pressure = os.path.join(advanced_folder, f'{player_name_clean}_pressure_analysis.png')
                    visualizer.plot_pressure_analysis(save_path_pressure)
                    print("✅ Analyse de pression générée")

                    print("🔮 Génération de l'analyse prédictive...")
                    save_path_prediction = os.path.join(advanced_folder, f'{player_name_clean}_predictive_analysis.png')
                    visualizer.plot_next_action_prediction(save_path_prediction)
                    print("✅ Analyse prédictive générée")

                    print(f"\n🎉 Toutes les analyses avancées ont été générées dans: {advanced_folder}")
                    print("\n📊 RÉSUMÉ DES ANALYSES GÉNÉRÉES:")
                    print(f"   🧠 Intelligence Spatiale: {save_path_spatial}")
                    print(f"   ⚡ Analyse de Pression: {save_path_pressure}")
                    print(f"   🔮 Analyse Prédictive: {save_path_prediction}")

                except Exception as e:
                    print(f"\n❌ ERREUR lors des analyses avancées (agrégées): {type(e).__name__} - {str(e)}")
                    traceback.print_exc()
            
            
    else:
        # NOUVEAU: Génération d'un seul JSON unifié avec toutes les données
        if isinstance(extractor, WhoScoredDataExtractor):
            try:
                print(f"🔍 Génération du JSON unifié pour {player_name}...")
                player_data_file = extractor.generate_unified_player_analysis(player_name, "player_data")
                print(f"✅ JSON unifié généré avec succès: {player_data_file}")
            except Exception as e:
                print(f"\n❌ ERREUR lors de la génération du JSON unifié:")
                print(f"   Type d'erreur: {type(e).__name__}")
                print(f"   Message: {str(e)}")
                print(f"\n📋 STACK TRACE:")
                traceback.print_exc()
                
                # Fallback vers l'ancienne méthode en cas d'erreur
                print("🔄 Tentative avec l'ancienne méthode...")
                try:
                    player_data_file = extractor.extract_player_stats_and_events(player_name, "player_data")
                except Exception as fallback_e:
                    print(f"❌ Erreur même avec l'ancienne méthode: {fallback_e}")
                    sys.exit(1)
        else:
            # Pour SofaScore, garder l'ancienne méthode
            player_data_file = extractor.extract_player_stats_and_events(player_name)

        # Obtenir les informations de compétition pour WhoScored
        if isinstance(extractor, WhoScoredDataExtractor):
            try:
                # Utiliser les méthodes existantes de MatchDataExtractor
                competition, color1, color2 = extractor.get_competition_and_colors()
                match_teams = extractor.extract_match_teams()
                match_name = extractor.get_competition_from_filename()
                
                print(f"✅ Infos extraites via MatchDataExtractor:")
                print(f"   🏆 Compétition: {competition}")
                print(f"   ⚽ Équipes: {match_teams}")
                print(f"   🎨 Couleurs: {color1}, {color2}")
                
            except Exception as comp_e:
                print(f"⚠️ Erreur lors de l'extraction des infos de compétition: {comp_e}")
                # En cas d'erreur, essayer d'extraire depuis le JSON unifié
                try:
                    with open(player_data_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    match_info = json_data.get("match_info", {})
                    competition = match_info.get("competition", "Unknown Competition")
                    match_teams = f"{match_info.get('home_team', 'Team')} vs {match_info.get('away_team', 'Team')}"
                    match_name = competition
                    
                    # Utiliser les méthodes de l'extracteur pour les couleurs si possible
                    try:
                        _, color1, color2 = extractor.load_colors_for_competition(competition)
                    except:
                        color1, color2 = "#000000", "#333333"
                        
                    print(f"✅ Infos extraites depuis JSON unifié:")
                    print(f"   🏆 Compétition: {competition}")
                    print(f"   ⚽ Équipes: {match_teams}")
                    print(f"   🎨 Couleurs: {color1}, {color2}")
                    
                except Exception as json_e:
                    print(f"❌ Erreur extraction JSON: {json_e}")
                    # Valeurs de fallback minimal
                    competition = "Unknown Competition"
                    color1, color2 = "#000000", "#333333"
                    match_teams = "Team vs Team"
                    match_name = "Unknown Match"

            # Initialize the visualizer with the extracted data
            try:
                visualizer = MatchVisualizer(player_data_file, competition, color1, color2, match_name, match_teams)

                # Save paths for the various visualizations
                save_path_passes = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_passes_and_pie_charts.png')
                save_path_defensive = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_defensive_activity.png')
                save_path_offensive_pitch = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_offensive_activity_pitch.png')
                save_path_offensive_goal = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_offensive_activity_goal.png')
                save_path_activity = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_activity_{poste}.png')

                print("📊 Génération des visualisations standard...")
                if poste == "GK":
                    visualizer.plot_goalkeeper_activity(save_path_activity, poste)
                    print("✅ Visualisation gardien générée")
                else:
                    visualizer.plot_passes_and_bar_charts(save_path_passes)
                    print("✅ Visualisation passes générée")
                    visualizer.plot_defensive_activity(save_path_defensive)
                    print("✅ Visualisation défensive générée")
                    visualizer.plot_offensive_activity(save_path_offensive_pitch, save_path_offensive_goal)
                    print("✅ Visualisation offensive générée")
                    visualizer.plot_passes_heatmap_and_bar_charts(save_path_activity, poste, nb_passe_d)
                    print("✅ Heatmap d'activité générée")
                
                print("🎉 Toutes les visualisations standard ont été générées avec succès!")

                # ===== NOUVELLES ANALYSES AVANCÉES =====
                if advanced_analysis:
                    print("\n🚀 Génération des analyses avancées...")
                    
                    try:
                        # Créer le dossier pour les analyses avancées
                        advanced_folder = os.path.join(match_folder, "advanced_analysis")
                        os.makedirs(advanced_folder, exist_ok=True)
                        
                        player_name_clean = player_name.replace(' ', '_')
                        
                        # 1. Analyse spatiale intelligente
                        print("🧠 Génération de l'analyse spatiale intelligente...")
                        save_path_spatial = os.path.join(advanced_folder, f'{player_name_clean}_spatial_intelligence.png')
                        visualizer.plot_positional_intelligence(save_path_spatial)
                        print("✅ Analyse spatiale générée")
                        
                        # 2. Analyse de pression et intensité
                        print("⚡ Génération de l'analyse de pression...")
                        save_path_pressure = os.path.join(advanced_folder, f'{player_name_clean}_pressure_analysis.png')
                        visualizer.plot_pressure_analysis(save_path_pressure)
                        print("✅ Analyse de pression générée")
                        
                        # 3. Analyse prédictive
                        print("🔮 Génération de l'analyse prédictive...")
                        save_path_prediction = os.path.join(advanced_folder, f'{player_name_clean}_predictive_analysis.png')
                        visualizer.plot_next_action_prediction(save_path_prediction)
                        print("✅ Analyse prédictive générée")
                        
                        print(f"\n🎉 Toutes les analyses avancées ont été générées dans: {advanced_folder}")
                        print("\n📊 RÉSUMÉ DES ANALYSES GÉNÉRÉES:")
                        print(f"   🧠 Intelligence Spatiale: {save_path_spatial}")
                        print(f"   ⚡ Analyse de Pression: {save_path_pressure}")
                        print(f"   🔮 Analyse Prédictive: {save_path_prediction}")
                        
                    except Exception as advanced_e:
                        print(f"\n❌ ERREUR lors de la génération des analyses avancées:")
                        print(f"   Type d'erreur: {type(advanced_e).__name__}")
                        print(f"   Message: {str(advanced_e)}")
                        print(f"\n📋 STACK TRACE:")
                        traceback.print_exc()
                        print("\n⚠️ Les visualisations standard ont été générées avec succès.")
                        print("   Les analyses avancées ont échoué mais le programme continue.")
                        
                else:
                    print("\n💡 Pour générer les analyses avancées, ajoutez --advanced au script")
                    print("   Exemple: python main.py <url> <player> <poste> <nb_passes> --advanced")
                
            except Exception as viz_e:
                print(f"\n❌ ERREUR lors de la génération des visualisations:")
                print(f"   Type d'erreur: {type(viz_e).__name__}")
                print(f"   Message: {str(viz_e)}")
                print(f"\n📋 STACK TRACE:")
                traceback.print_exc()
        else:
            # SofaScore handling
            try:
                save_path_activity_sofascore = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_activity_sofascore_{poste}.png')
                visualizer = PlayerVisualizer(player_data_file)  # Assuming PlayerVisualizer for SofaScore
                visualizer.plot_shots_heatmap_and_bar_charts(save_path_activity_sofascore, poste, nb_passe_d)
                print(f"✅ Visualisation SofaScore générée pour {player_name}")
            except Exception as sofa_e:
                print(f"❌ Erreur SofaScore: {sofa_e}")
                traceback.print_exc()

def generate_advanced_analysis_only(url, player_name):
    """Fonction pour générer uniquement les analyses avancées"""
    print(f"\n🚀 GÉNÉRATION ANALYSES AVANCÉES UNIQUEMENT pour {player_name}")
    print("=" * 60)
    
    # Choix du bon extracteur
    if "whoscored.com" in url:
        extractor = WhoScoredDataExtractor(url)
    else:
        print("❌ Analyses avancées disponibles uniquement pour WhoScored")
        return
    
    try:
        # Génération du JSON unifié
        player_data_file = extractor.generate_unified_player_analysis(player_name, "player_data")
        
        # Extraction des infos de compétition
        competition, color1, color2 = extractor.get_competition_and_colors()
        match_teams = extractor.extract_match_teams()
        match_name = extractor.get_competition_from_filename()
        
        # Initialisation du visualizer
        visualizer = MatchVisualizer(player_data_file, competition, color1, color2, match_name, match_teams)
        
        # Génération des analyses avancées avec la fonction intégrée
        analysis_paths = visualizer.generate_advanced_analysis_suite("advanced_analysis")
        
        if analysis_paths:
            print("\n🎉 ANALYSES AVANCÉES GÉNÉRÉES AVEC SUCCÈS!")
            print(f"📁 Dossier: advanced_analysis/")
            for analysis_type, path in analysis_paths.items():
                print(f"   📊 {analysis_type.title()}: {path}")
        else:
            print("❌ Échec de la génération des analyses avancées")
            
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Vérification des arguments
    if len(sys.argv) < 4:
        print("Usage: python main.py <url> <player_name> <poste> [nb_passe_d] [--advanced|--advanced-only]")
        print("")
        print("Options:")
        print("  --advanced      : Génère les visualisations standard + analyses avancées")
        print("  --advanced-only : Génère uniquement les analyses avancées (rapide)")
        print("")
        print("Exemples:")
        print('  python main.py "https://..." "Vitinha" "MIL" 0')
        print('  python main.py "https://..." "Vitinha" "MIL" 0 --advanced')
        print('  python main.py "https://..." "Vitinha" "ATT" --advanced-only')
        sys.exit(1)

    url = sys.argv[1]
    player_name = sys.argv[2]
    
    # Gestion des modes spéciaux
    if "--advanced-only" in sys.argv:
        generate_advanced_analysis_only(url, player_name)
        sys.exit(0)
    
    # Paramètres standards
    poste = sys.argv[3] if len(sys.argv) > 3 else "MIL"
    
    # Paramètres optionnels
    nb_passe_d = 0
    advanced_analysis = False
    
    # Parser les arguments restants
    for i, arg in enumerate(sys.argv[4:], 4):
        if arg == "--advanced":
            advanced_analysis = True
        elif arg.isdigit():
            nb_passe_d = int(arg)
    
    try:
        print(f"🚀 DÉMARRAGE DE L'ANALYSE POUR {player_name}")
        print(f"📊 Mode: {'Standard + Avancé' if advanced_analysis else 'Standard uniquement'}")
        print("=" * 60)
        
        main(url, player_name, poste, nb_passe_d, advanced_analysis)
        
        print("\n" + "=" * 60)
        print("🎉 ANALYSE TERMINÉE AVEC SUCCÈS!")
        
        if not advanced_analysis:
            print("\n💡 CONSEIL: Ajoutez --advanced pour des analyses plus poussées:")
            print(f'   python main.py "{url}" "{player_name}" "{poste}" {nb_passe_d} --advanced')
            
    except Exception as main_e:
        print(f"\n💥 ERREUR CRITIQUE dans main():")
        print(f"   Type: {type(main_e).__name__}")
        print(f"   Message: {str(main_e)}")
        print(f"\n📋 STACK TRACE COMPLÈTE:")
        print("=" * 60)
        traceback.print_exc()
        print("=" * 60)
        sys.exit(1)