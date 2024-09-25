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

    def fetch_search_results(self):
        """Effectue la requête HTTP pour obtenir les résultats de la recherche."""
        response = requests.get(self.base_url, headers=self.headers)
        if response.status_code != 200:
            print(f"Erreur lors de la requête HTTP: {response.status_code}")
            return None
        return response.text

    def parse_profile_url(self, html_content):
        """Parse le contenu HTML pour extraire l'URL du profil du premier joueur."""
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table', class_='items')
        
        if table is None:
            print("Aucune table trouvée.")
            return None
        
        first_row = table.find('tbody').find('tr')
        if first_row is None:
            print("Aucune ligne trouvée dans la table.")
            return None
        
        # Récupérer le lien vers le profil du joueur dans la première ligne
        player_link = first_row.find('td', class_='hauptlink').find('a', href=True)
        
        if player_link is None:
            print("Aucun lien trouvé pour le joueur.")
            return None
        
        # Le lien extrait est relatif, on le complète avec le domaine
        profile_url = "https://www.transfermarkt.com" + player_link['href']
        return profile_url


    def scrape_profile_info(self, profile_url):
        print(profile_url)
        """Scrape des informations supplémentaires à partir du profil du joueur."""
        response = requests.get(profile_url, headers=self.headers)
        if response.status_code != 200:
            print(f"Erreur lors de la requête HTTP vers le profil: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')

        #print(soup)
        
        # Extraire le nom du joueur
        name = soup.find('h1', class_='data-header__headline').text if soup.find('h1', class_='data-header__headline') else "Nom inconnu"
        
        # Extraire la valeur marchande du joueur
        market_value = soup.find('div', class_='right-td').text.strip() if soup.find('div', class_='right-td') else "Valeur non disponible"
        
        # Extraire l'image depuis la balise meta
        og_image_meta = soup.find('meta', property="og:image")
        image_url = og_image_meta['content'] if og_image_meta else None
        
        # Vérification que l'image commence bien par l'URL demandée
        if image_url and image_url.startswith("https://img.a.transfermarkt.technology/portrait/big"):
            # Télécharger et sauvegarder l'image
            self.download_image(image_url, f"data/{self.full_name.replace(' ', '_')}_profile_image.jpg")
        else:
            print("Aucune image valide trouvée ou l'URL ne correspond pas aux critères.")
            image_url = None
        
        return {
            "name": name,
            "market_value": market_value,
            "image_url": image_url
        }

    def download_image(self, image_url, file_name):
        """Télécharge l'image à partir de l'URL et la sauvegarde localement."""
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            os.makedirs('data', exist_ok=True)  # Créer le dossier data s'il n'existe pas
            with open(file_name, 'wb') as file:
                file.write(image_response.content)
            print(f"Image téléchargée et enregistrée sous: {file_name}")
        else:
            print(f"Erreur lors du téléchargement de l'image : {image_response.status_code}")

    def save_player_profile(self):
        """Méthode principale pour rechercher le profil d'un joueur et extraire des informations."""
        html_content = self.fetch_search_results()
        if html_content:
            profile_url = self.parse_profile_url(html_content)
            if profile_url:
                print(f"Profil trouvé: {profile_url}")
                profile_info = self.scrape_profile_info(profile_url)
                if profile_info:
                    print(f"Informations du joueur : {profile_info}")
                    return profile_info
        return None