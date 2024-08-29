import re
import pandas as pd
import json

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

    # Save JSON data to a file (Optional)
    with open(f"{html_path}.json", "wt") as output_file:
        output_file.write(data_txt)

    # Convert extracted data to JSON
    data_json = json.loads(data_txt)

    return data_json

# Function to save a list of dictionaries to a CSV file
def save_to_csv(data_list, file_name):
    if data_list:  # Check if the list is not empty
        df = pd.DataFrame(data_list)
        df.to_csv(file_name, index=False)
        print(f"Saved {file_name}")
    else:
        print(f"No data to save for {file_name}")

# Extract JSON data from the HTML
data = extract_data_html(URL_MATCH)

# Example: Extracting different categories and saving them as CSVs

# 1. Extract and save player information
if 'matchCentreData' in data and 'playerIdNameDictionary' in data['matchCentreData']:
    players = [{'playerId': key, 'playerName': value} for key, value in data['matchCentreData']['playerIdNameDictionary'].items()]
    save_to_csv(players, 'data/players.csv')

# 2. Extract and save formations
if 'home' in data and 'formations' in data['home']:
    save_to_csv(data['home']['formations'], 'data/home_formations.csv')
if 'away' in data and 'formations' in data['away']:
    save_to_csv(data['away']['formations'], 'data/away_formations.csv')

# 3. Extract and save stats
if 'home' in data and 'stats' in data['home']:
    stats = []
    for stat_type, values in data['home']['stats'].items():
        for minute, value in values.items():
            stats.append({'minute': minute, 'stat_type': stat_type, 'value': value, 'team': 'home'})
    save_to_csv(stats, 'data/home_stats.csv')
if 'away' in data and 'stats' in data['away']:
    stats = []
    for stat_type, values in data['away']['stats'].items():
        for minute, value in values.items():
            stats.append({'minute': minute, 'stat_type': stat_type, 'value': value, 'team': 'away'})
    save_to_csv(stats, 'data/away_stats.csv')

# 4. Extract and save incidents/events
if 'incidentEvents' in data:
    save_to_csv(data['incidentEvents'], 'data/incident_events.csv')

# 5. Extract and save referee information
if 'referee' in data:
    referee = [data['referee']]
    save_to_csv(referee, 'data/referee.csv')

# 6. Extract and save general match information
general_info = {
    'matchId': data.get('matchId'),
    'attendance': data.get('attendance'),
    'venueName': data.get('venueName'),
    'timeStamp': data.get('timeStamp'),
    'startTime': data.get('startTime'),
    'startDate': data.get('startDate'),
    'score': data.get('score'),
    'htScore': data.get('htScore'),
    'ftScore': data.get('ftScore'),
    'etScore': data.get('etScore'),
    'pkScore': data.get('pkScore'),
}
save_to_csv([general_info], 'data/match_info.csv')

# 7. Extract and save weather and period information
if 'periodMinuteLimits' in data:
    period_limits = [{'period': key, 'minute_limit': value} for key, value in data['periodMinuteLimits'].items()]
    save_to_csv(period_limits, 'data/period_minute_limits.csv')

if 'weatherCode' in data:
    weather_info = [{'weatherCode': data['weatherCode']}]
    save_to_csv(weather_info, 'data/weather_info.csv')

# Continue to add more sections here if there are other categories in your JSON structure
