import re
import pandas as pd
import json
import os

# URL du match à analyser
URL_MATCH = "data/Toulouse 1-3 Marseille - Ligue 1 2024_2025 Direct.html"

def extract_data_html(html_path=URL_MATCH):
    with open(html_path, 'r') as html_file:
        html = html_file.read()
        
    regex_pattern = r'(?<=require\.config\.params\["args"\].=.)[\s\S]*?;'
    data_txt = re.findall(regex_pattern, html)[0]

    # Add quotations for JSON parser
    data_txt = data_txt.replace('matchId', '"matchId"')
    data_txt = data_txt.replace('matchCentreData', '"matchCentreData"')
    data_txt = data_txt.replace('matchCentreEventTypeJson', '"matchCentreEventTypeJson"')
    data_txt = data_txt.replace('formationIdNameMappings', '"formationIdNameMappings"')
    data_txt = data_txt.replace('};', '}')

    # Convert extracted data to JSON
    data_json = json.loads(data_txt)

    return data_json

def save_to_csv(data_list, file_name):
    if data_list:  # Check if the list is not empty
        df = pd.DataFrame(data_list)
        df.to_csv(file_name, index=False)
        print(f"Saved {file_name}")
    else:
        print(f"No data to save for {file_name}")


def extract_player_stats_and_events(data, player_name, output_dir="player_data"):
    print("Extraction des données pour le joueur - ", player_name)

    # Créer un répertoire pour stocker les fichiers JSON
    os.makedirs(output_dir, exist_ok=True)

    # Trouver l'ID du joueur à partir du nom
    player_id = None
    for pid, name in data['matchCentreData']['playerIdNameDictionary'].items():
        if name.lower() == player_name.lower():
            player_id = pid
            break
    
    if not player_id:
        return f"Player '{player_name}' not found."
    
    # Extraction des événements
    events = data["matchCentreData"]["events"]
    player_events = []

    # Parcourir les événements et ajouter ceux correspondant au joueur
    for event in events:
        if event.get('playerId') == int(player_id):
            player_events.append(event)
            
    # Extraire les statistiques du joueur à partir des événements filtrés
    player_stats = {
        "player_name": player_name,
        "player_id": player_id,
        "events": player_events
    }
    
    # Créer le fichier JSON avec les données extraites
    output_file = os.path.join(output_dir, f"{player_name.replace(' ', '_')}_stats.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(player_stats, f, ensure_ascii=False, indent=4)
    
    print(f"Les données pour le joueur '{player_name}' ont été enregistrées dans {output_file}")


# Utilisation complète du code
data = extract_data_html(URL_MATCH)  # Extraction des données JSON depuis l'HTML
player_name = "Amine Harit"  # Nom du joueur à analyser
extract_player_stats_and_events(data, player_name)  # Extraction des stats et événements détaillés du joueur et sauvegarde en CSV
