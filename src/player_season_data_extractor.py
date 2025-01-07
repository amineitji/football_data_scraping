from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import json
import os

class PlayerSeasonDataExtractor:
    def __init__(self, html_path):
        self.html_path = html_path
        self.data = self._extract_data_html()

    def convert_to_json(self,data_txt):
        """Nettoie et convertit data_txt en JSON valide."""
        # Ajout des guillemets autour des clés
        cleaned_data = re.sub(r'(\w+):', r'"\1":', data_txt)

        # Suppression des espaces superflus avant ou après les accolades et crochets
        cleaned_data = re.sub(r'\s*([\{\}\[\]])\s*', r'\1', cleaned_data)

        # Correction des espaces dans les valeurs (par exemple : "Name": " ")
        cleaned_data = re.sub(r'"Name":" "', r'"Name":""', cleaned_data)

        # Correction des champs null
        cleaned_data = cleaned_data.replace('null', 'null')

        # Ajout des accolades manquantes au début et à la fin si nécessaire
        if not cleaned_data.startswith('{'):
            cleaned_data = '{' + cleaned_data
        if not cleaned_data.endswith('}'):
            cleaned_data = cleaned_data + '}'

        # Chargement en JSON
        try:
            data_json = json.loads(cleaned_data)
            return data_json
        except json.JSONDecodeError as e:
            print("Erreur lors de la conversion en JSON :", e)
            return None

    def _extract_data_html(self):
        """Méthode pour extraire et nettoyer le contenu de require.config.params['args']."""
        print("Configuration de Selenium avec le mode headless...")
        options = Options()
        options.headless = True
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36')

        driver = webdriver.Chrome(options=options)

        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"Chargement de la page WhoScored {self.html_path}...")
        driver.get(self.html_path)

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        html = driver.page_source
        driver.quit()

        print("Extraction des données avec le modèle regex...")
        regex_pattern = r"require\.config\.params\['args'\]\s*=\s*\{([\s\S]*?)\};(?=\n)"
        matches = re.findall(regex_pattern, html, re.DOTALL)

        if not matches:
            print("Aucune correspondance trouvée. Vérifiez le format HTML ou ajustez la regex.")
            return None

        data_txt = matches[0]
        print("Données extraites :")
        print(data_txt)

        # Convertir les données extraites en JSON
        data_json = self.convert_to_json(data_txt)
        if not data_json:
            print("Erreur lors de la conversion en JSON. Abandon de la sauvegarde.")
            return None

        # Chemin où sauvegarder les données
        output_path = os.path.join(os.getcwd(), "player_data/player_season.json")

        # Création du répertoire "data" si nécessaire
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Sauvegarde des données dans le fichier JSON
        try:
            with open(output_path, "w", encoding="utf-8") as file:
                json.dump(data_json, file, ensure_ascii=False, indent=4)
            print(f"Données sauvegardées avec succès dans {output_path}.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données : {e}")
            return None

        print("Extraction et conversion terminées.")
        return data_json

    

url = "https://fr.whoscored.com/Players/384887/Show/Vitinha"  # Exemple d'URL
extractor = PlayerSeasonDataExtractor(url)
print(json.dumps(extractor.data, indent=4))
