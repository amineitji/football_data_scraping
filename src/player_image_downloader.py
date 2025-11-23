# player_image_downloader.py
import requests
from bs4 import BeautifulSoup
import os

class PlayerProfileScraper:
    def __init__(self, full_name):
        self.full_name = full_name
        self.full_name_for_url = full_name.replace(' ', '+')
        self.base_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={self.full_name_for_url}"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        self.image_save_path = f"data/photo/{self.full_name.replace(' ', '_')}_profile_image.jpg"

    def fetch_search_results(self):
        """Effectue la requête HTTP pour obtenir les résultats de la recherche."""
        try:
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête HTTP: {e}")
            return None

    def parse_profile_url(self, html_content):
        """Parse le contenu HTML pour extraire l'URL du profil du premier joueur."""
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table', class_='items')
        
        if table is None:
            print("Aucune table de résultats trouvée sur Transfermarkt.")
            return None
        
        first_row = table.find('tbody').find('tr')
        if first_row is None:
            print("Aucune ligne trouvée dans la table des résultats.")
            return None
        
        player_link = first_row.find('td', class_='hauptlink').find('a', href=True)
        
        if player_link is None:
            print("Aucun lien de profil trouvé pour le joueur.")
            return None
        
        profile_url = "https://www.transfermarkt.com" + player_link['href']
        return profile_url

    def scrape_profile_info(self, profile_url):
        """Scrape l'URL de l'image à partir du profil du joueur."""
        try:
            response = requests.get(profile_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extraire l'image depuis la balise meta
            og_image_meta = soup.find('meta', property="og:image")
            image_url = og_image_meta['content'] if og_image_meta else None
            
            if image_url:
                self.download_image(image_url, self.image_save_path)
            else:
                print("Aucune balise meta 'og:image' trouvée.")
            
            return image_url

        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête HTTP vers le profil: {e}")
            return None

    def download_image(self, image_url, file_name):
        """Télécharge l'image à partir de l'URL et la sauvegarde localement."""
        try:
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            with open(file_name, 'wb') as file:
                file.write(image_response.content)
            print(f"Image téléchargée et enregistrée sous: {file_name}")
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors du téléchargement de l'image : {e}")

    def save_player_profile(self):
        """Méthode principale pour rechercher et télécharger la photo du joueur."""
        # Vérifie si l'image existe déjà
        if os.path.exists(self.image_save_path):
            print(f"L'image pour {self.full_name} existe déjà. Utilisation du cache.")
            return self.image_save_path

        print(f"Recherche de la photo de profil pour {self.full_name}...")
        html_content = self.fetch_search_results()
        if html_content:
            profile_url = self.parse_profile_url(html_content)
            if profile_url:
                print(f"Profil Transfermarkt trouvé: {profile_url}")
                self.scrape_profile_info(profile_url)
            else:
                print(f"Aucun profil Transfermarkt trouvé pour {self.full_name}.")
        
        if not os.path.exists(self.image_save_path):
            print(f"AVERTISSEMENT: La photo de {self.full_name} n'a pas pu être téléchargée.")
            return None # Retourne None si echec total
            
        return self.image_save_path