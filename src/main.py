# main.py
import sys
import os
import traceback
import json
import re
from whoscored_data_extractor import WhoScoredDataExtractor
from visualizer import MatchVisualizer, SeasonVisualizer, PlayerDuelVisualizer, PlayerDuoVisualizer, TeamPassNetworkVisualizer

def run_analysis(url, player_name, poste, nb_passe_d, extractor):
    """
    La logique d'analyse et de visualisation.
    """
    is_aggregate = "/players/" in url
    
    if is_aggregate:
        print("Analyse de données agrégées (saison)...")
        player_folder = os.path.join('./viz_data/aggregated/', player_name.replace(" ", "_"))
        match_name = "season_summary"
        if not os.path.exists(player_folder): os.makedirs(player_folder)
        match_folder = os.path.join(player_folder, match_name)
        if not os.path.exists(match_folder): os.makedirs(match_folder)
        
        player_data_file = extractor.extract_player_aggregate_stats(player_name, player_folder)

        if not player_data_file:
            print(f"Impossible de générer le fichier de données pour {player_name}.")
            return

        visualizer = SeasonVisualizer(player_data_file, None, "#000000", "#5a5403", "Saison 2024/2025","(WhoScored)")
        
        # Génération des 3 visualisations de saison
        save_path_events = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_season_events_{poste}.png')
        save_path_progressive = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_season_progressive_{poste}.png')
        save_path_dominance = os.path.join(match_folder, f'{player_name.replace(" ", "_")}_season_dominance_{poste}.png')
        
        print("📊 Génération des 3 visualisations de saison...")
        visualizer.plot_passes_heatmap_and_bar_charts(save_path_events, poste, nb_passe_d)
        print(f"✅ 1/3 Événements réussis")
        
        visualizer.plot_progressive_actions(save_path_progressive)
        print(f"✅ 2/3 Actions progressives")
        
        visualizer.plot_zone_dominance(save_path_dominance)
        print(f"✅ 3/3 Dominance terrain")
        
        print(f"Visualisations de saison générées dans : {match_folder}")
            
    else:
        # Logique pour un match unique
        print("Analyse de match unique...")
        
        player_data_file = extractor.extract_player_stats_and_events(player_name, "player_data")
        
        if not player_data_file:
            print(f"Impossible de générer le fichier de données pour {player_name}.")
            return

        match = re.search(r"/matches/(\d+)/", url, re.IGNORECASE)
        if match:
            match_id = match.group(1)
            match_name = f"match_{match_id}"
        else:
            match_name = "match_unknown"

        player_folder = os.path.join('./viz_data/', player_name.replace(" ", "_"))
        if not os.path.exists(player_folder): os.makedirs(player_folder)
        match_folder = os.path.join(player_folder, match_name)
        if not os.path.exists(match_folder): os.makedirs(match_folder)

        try:
            competition, color1, color2 = extractor.get_competition_and_colors()
            match_teams = extractor.extract_match_teams()
            match_name_comp = extractor.get_competition_from_filename()
            print(f"✅ Infos extraites : {competition}, {match_teams}, {color1}, {color2}")
            
        except Exception as comp_e:
            print(f"⚠️ Erreur lors de l'extraction des infos de compétition : {comp_e}")
            competition = "Unknown Competition"
            color1, color2 = "#000000", "#333333"
            match_teams = "Team vs Team"
            match_name_comp = "Unknown Match"

        # Initialisation du visualizer de match
        try:
            visualizer = MatchVisualizer(player_data_file, competition, color1, color2, match_name_comp, match_teams)

            # Définir les 7 chemins de sauvegarde pour les 7 visualisations
            base_name = f'{player_name.replace(" ", "_")}_match'
            save_path_heatmap = os.path.join(match_folder, f'{base_name}_heatmap_{poste}.png')
            save_path_passes = os.path.join(match_folder, f'{base_name}_passes_{poste}.png')
            save_path_defensive = os.path.join(match_folder, f'{base_name}_defensive_{poste}.png')
            save_path_offensive = os.path.join(match_folder, f'{base_name}_offensive_{poste}.png')
            save_path_progressive = os.path.join(match_folder, f'{base_name}_progressive_{poste}.png')
            save_path_dominance = os.path.join(match_folder, f'{base_name}_dominance_{poste}.png')
            save_path_connections = os.path.join(match_folder, f'{base_name}_connections_{poste}.png')

            print("📊 Génération des 7 visualisations de match...")
            
            # 1. Heatmap + passes
            visualizer.plot_passes_heatmap_and_bar_charts(save_path_heatmap, poste, nb_passe_d)
            print(f"✅ 1/7 Heatmap + passes")
            
            # 2. Classification des passes
            visualizer.plot_passes_and_bar_charts(save_path_passes)
            print(f"✅ 2/7 Classification passes")
            
            # 3. Activité défensive
            visualizer.plot_defensive_activity(save_path_defensive)
            print(f"✅ 3/7 Activité défensive")
            
            # 4. Activité offensive
            visualizer.plot_offensive_activity(save_path_offensive)
            print(f"✅ 4/7 Activité offensive")
            
            # 5. Actions progressives
            visualizer.plot_progressive_actions(save_path_progressive)
            print(f"✅ 5/7 Actions progressives")
            
            # 6. Dominance zones
            visualizer.plot_zone_dominance(save_path_dominance)
            print(f"✅ 6/7 Dominance zones")
            
            # 7. Connexions de passes
            save_path_connections = os.path.join(match_folder, f'{base_name}_connections_{poste}.png')
            visualizer.plot_player_pass_connections(save_path_connections)
            print(f"✅ 7/7 Connexions de passes")
            
        except Exception as viz_e:
            print(f"\n❌ ERREUR lors de la génération des visualisations:")
            print(f"   Type d'erreur: {type(viz_e).__name__}")
            print(f"   Message: {str(viz_e)}")
            print(f"\n📋 STACK TRACE:")
            traceback.print_exc()

def display_player_list(player_list):
    """Affiche la liste des joueurs de manière numérique."""
    print("\n" + "=" * 50)
    print("    LISTE DES JOUEURS DU MATCH")
    print("=" * 50)
    player_indices = []
    for i, (name, team, is_starter) in enumerate(player_list):
        if team is None: # C'est un titre de section
            print(f"\n{name}")
        else:
            status = " (Titulaire)" if is_starter else " (Remplaçant)"
            print(f"  {i+1}: {name}{status}")
            player_indices.append(i+1)
    print("=" * 50)
    return player_indices

def get_player_choice(player_list):
    """Demande à l'utilisateur de choisir un ou plusieurs joueurs."""
    print("\nVous pouvez choisir:")
    print("  - Un seul joueur: entrez son numéro (ex: 5)")
    print("  - Plusieurs joueurs: entrez les numéros séparés par des virgules (ex: 1,3,7)")
    print("  - Tous les joueurs: entrez 'all' ou 'tous'")
    
    while True:
        try:
            choice = input("\nVotre choix: ").strip()
            
            # Option pour sélectionner tous les joueurs
            if choice.lower() in ['all', 'tous']:
                selected_players = []
                for player_name, team, _ in player_list:
                    if team is not None:  # Exclure les titres
                        selected_players.append(player_name)
                return selected_players
            
            # Multi-sélection avec virgules
            if ',' in choice:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                selected_players = []
                for idx in indices:
                    if 0 <= idx < len(player_list):
                        player_name, team, _ = player_list[idx]
                        if team is None:
                            print(f"⚠️ L'indice {idx+1} est un titre, pas un joueur.")
                        else:
                            selected_players.append(player_name)
                    else:
                        print(f"⚠️ Numéro {idx+1} invalide.")
                
                if selected_players:
                    return selected_players
                else:
                    print("Aucun joueur valide sélectionné. Veuillez réessayer.")
                    continue
            
            # Sélection unique
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(player_list):
                player_name, team, _ = player_list[choice_index]
                if team is None:
                    print("Veuillez choisir un numéro de joueur valide.")
                    continue
                return [player_name]  # Retourne une liste avec un seul joueur
            else:
                print("Numéro invalide. Veuillez réessayer.")
        except ValueError:
            print("Format invalide. Veuillez entrer un numéro ou plusieurs numéros séparés par des virgules.")

def interactive_main():
    """La nouvelle fonction main interactive."""
    print("🚀 DÉMARRAGE DE L'ANALYSE INTERACTIVE")
    print("=" * 60)
    
    # 0. Choix du mode
    print("\nChoisissez le mode d'analyse:")
    print("  1. Analyse individuelle (joueur(s))")
    print("  2. Duel 1v1 (2 joueurs adverses) 🥊")
    print("  3. Duo (2 joueurs même équipe) 🤝")
    print("  4. Réseau d'équipe (11 titulaires) 🕸️")
    
    mode = input("\nMode (1-4) : ").strip()
    
    # 1. Demander l'URL
    url = input("\nVeuillez entrer l'URL du match WhoScored : ")
    
    extractor = WhoScoredDataExtractor(url)

    # Récupération des infos de compétition pour les modes 2, 3 et 4
    competition, color1, color2, match_teams = None, "#000000", "#333333", "Team vs Team"
    try:
        competition, color1, color2 = extractor.get_competition_and_colors()
        match_teams = extractor.extract_match_teams()
    except Exception as comp_e:
        print(f"⚠️ Erreur lors de l'extraction des infos de compétition pour le style: {comp_e}")

    # 2. Traitement selon le mode
    if mode == "1":
        # === MODE 1: ANALYSE INDIVIDUELLE (EXISTANT) ===
        if "/players/" in url:
            print("URL de saison détectée. L'analyse agrégée nécessite le nom du joueur.")
            player_names = [input("Nom du joueur pour l'analyse de saison : ")]
        else:
            player_list = extractor.get_player_list()
            if not player_list:
                print("Impossible de récupérer la liste des joueurs. Vérifiez l'URL.")
                return
            display_player_list(player_list)
            player_names = get_player_choice(player_list)
            print(f"✅ Joueur(s) choisi(s) : {', '.join(player_names)}")

        poste = ""
        while poste not in ["DEF", "MIL", "ATT"]:
            poste = input("Poste du joueur (DEF, MIL, ATT) [appliqué à tous si multi-sélection] : ").upper()
        
        nb_passe_d = 0
        try:
            nb_passe_d_input = input("Nombre de passes décisives (laisser vide pour 0) [appliqué à tous si multi-sélection] : ")
            nb_passe_d = int(nb_passe_d_input) if nb_passe_d_input.isdigit() else 0
        except ValueError:
            nb_passe_d = 0
        
        total_players = len(player_names)
        for idx, player_name in enumerate(player_names, 1):
            print(f"\n{'='*60}")
            print(f"📊 Analyse {idx}/{total_players}: {player_name} ({poste}), {nb_passe_d} passe(s) D.")
            print(f"{'='*60}")
            
            try:
                run_analysis(url, player_name, poste, nb_passe_d, extractor)
                print(f"✅ Analyse terminée pour {player_name}")
            except Exception as e:
                print(f"❌ Erreur lors de l'analyse de {player_name}: {str(e)}")
                traceback.print_exc()
        
        print(f"\n{'='*60}")
        print(f"🎉 TOUTES LES ANALYSES TERMINÉES ({total_players} joueur(s))")
        print(f"{'='*60}")
    
    elif mode in ["2", "3", "4"]:
        # === MODES 2, 3, 4: NON IMPLÉMENTÉS ===
        print(f"\n⚠️ MODE {mode} NON IMPLÉMENTÉ")
        print("Les visualiseurs suivants sont actuellement en stub:")
        print("  - Mode 2: PlayerDuelVisualizer (Duel 1v1)")
        print("  - Mode 3: PlayerDuoVisualizer (Duo)")
        print("  - Mode 4: TeamPassNetworkVisualizer (Réseau d'équipe)")
        print("\nVeuillez utiliser le Mode 1 pour l'analyse individuelle.")
    
    else:
        print("❌ Mode invalide. Veuillez choisir entre 1 et 4.")

if __name__ == "__main__":
    try:
        # Ajoute le dossier 'src' au sys.path si main.py est exécuté depuis la racine
        # (Nécessaire pour que 'make run' fonctionne)
        sys.path.append(os.path.dirname(__file__))
        
        interactive_main()
    except Exception as main_e:
        print(f"\n💥 ERREUR CRITIQUE dans main():")
        print(f"   Type: {type(main_e).__name__}")
        print(f"   Message: {str(main_e)}")
        print(f"\n📋 STACK TRACE COMPLÈTE:")
        print("=" * 60)
        traceback.print_exc()
        print("=" * 60)
        sys.exit(1)