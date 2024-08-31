import re
import pandas as pd
import json
import os

# URL du match à analyser
URL_MATCH = "data/Zambia 0-1 Morocco - Africa Cup of Nations 2023 Direct.html"

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

    # Debugging: Affichage des clés principales pour inspection
    #print("Clés principales du dictionnaire data:", list(data.keys()))
    #print("-------------------------")
    #print("Clés de 'matchCentreData':", list(data["matchCentreData"].keys()))
    #print("Clés de 'matchCentreEventTypeJson':", list(data["matchCentreEventTypeJson"].keys()))
    #print("-------------------------")
    #print("Exemple d'événements dans 'matchCentreData':", data["matchCentreData"]["events"][:2])  # Afficher les deux premiers événements pour l'exemple

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










#
#    # Extraire les statistiques du joueur
#    player_stats = []
#    stats = data['matchCentreData']['home']['stats']
#    
#    for stat_type, values in stats.items():
#        if isinstance(values, dict):
#            for minute, value in values.items():
#                if isinstance(value, dict):
#                    stat_value = value.get(player_id, None)
#                    if stat_value is not None:
#                        # Récupérer les coordonnées x et y s'il y en a
#                        x = value.get('x')
#                        y = value.get('y')
#                        player_stats.append({
#                            "minute": minute,
#                            "stat_type": stat_type,
#                            "value": stat_value,
#                            "x": x,
#                            "y": y
#                        })
#                elif isinstance(value, float):
#                    player_stats.append({
#                        "minute": minute,
#                        "stat_type": stat_type,
#                        "value": value,
#                        "x": None,
#                        "y": None
#                    })
#
#    # Sauvegarder les statistiques du joueur dans un fichier CSV
#    stats_file_name = f"{output_dir}/{player_name.replace(' ', '_')}_stats.csv"
#    save_to_csv(player_stats, stats_file_name)
#
#    # Extraire les événements détaillés liés au joueur
#    events = data['matchCentreData']['home']['incidentEvents']
#    
#    # Regrouper les événements par type
#    events_by_type = {}
#    
#    for event in events:
#        # Vérifier si l'événement est lié au joueur via playerId ou relatedPlayerId
#        if 'playerId' in event and event['playerId'] == int(player_id) or \
#           'relatedPlayerId' in event and event['relatedPlayerId'] == int(player_id):
#            
#            event_type = event['type']['displayName']
#            
#            # Extraction des coordonnées de début et de fin
#            start_x = event.get('x', None)
#            start_y = event.get('y', None)
#            end_x = None
#            end_y = None
#            
#            # Chercher les qualifiers pour trouver EndX et EndY
#            if 'qualifiers' in event:
#                for qualifier in event['qualifiers']:
#                    if qualifier['type']['displayName'] == 'EndX':
#                        end_x = float(qualifier['value'])
#                    elif qualifier['type']['displayName'] == 'EndY':
#                        end_y = float(qualifier['value'])
#
#            event_details = {
#                "id": event.get('id'),
#                "eventId": event.get('eventId'),
#                "minute": event.get('minute'),
#                "second": event.get('second'),
#                "teamId": event.get('teamId'),
#                "playerId": event.get('playerId'),
#                "relatedPlayerId": event.get('relatedPlayerId'),
#                "x": start_x,
#                "y": start_y,
#                "endX": end_x,
#                "endY": end_y,
#                "expandedMinute": event.get('expandedMinute'),
#                "period": event.get('period', {}).get('displayName'),
#                "outcomeType": event.get('outcomeType', {}).get('displayName'),
#                "relatedEventId": event.get('relatedEventId'),
#                "qualifiers": event.get('qualifiers')
#            }
#            
#            if event_type not in events_by_type:
#                events_by_type[event_type] = []
#            
#            events_by_type[event_type].append(event_details)
#    
#    # Sauvegarder chaque type d'événement dans un fichier CSV distinct
#    for event_type, event_list in events_by_type.items():
#        sanitized_event_type = event_type.replace(" ", "_").replace("/", "_")
#        file_name = f"{output_dir}/{player_name.replace(' ', '_')}_{sanitized_event_type}_events.csv"
#        save_to_csv(event_list, file_name)
#
#    print(f"All player data has been saved in the directory: {output_dir}")





# Utilisation complète du code
data = extract_data_html(URL_MATCH)  # Extraction des données JSON depuis l'HTML
player_name = "Stoppila Sunzu"  # Nom du joueur à analyser
extract_player_stats_and_events(data, player_name)  # Extraction des stats et événements détaillés du joueur et sauvegarde en CSV
