import csv
import requests
import urllib.parse
import sys
import time

def get_bird_image(bird_name, high_quality=False, retries=1):
    """
    Récupère l'image de la page Wikipedia de l'oiseau.
    Pour high_quality True, utilise pithumbsize=1024 sinon 500.
    Effectue jusqu'à 'retries' tentative(s) en cas d'échec.
    """
    base_url = "https://en.wikipedia.org/w/api.php"
    size = 1024 if high_quality else 500
    params = {
        "action": "query",
        "format": "json",
        "titles": bird_name,
        "prop": "pageimages",
        "pithumbsize": size,
        "redirects": 1
    }
    for attempt in range(retries + 1):
        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                thumbnail = page.get("thumbnail", {})
                if thumbnail:
                    return thumbnail.get("source", "")
        except Exception as e:
            print(f"Debug: Erreur récupération image pour '{bird_name}' (high_quality={high_quality}), tentative {attempt+1} : {e}")
        if attempt < retries:
            time.sleep(1)  # petite pause avant réessai
    return ""

def is_url_valid(url):
    """
    Vérifie que l'URL renvoie un status code 200.
    """
    try:
        r = requests.head(url, timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def update_csv(csv_file, output_file):
    """
    Parcourt le CSV et pour chaque oiseau :
      - Construit "URL anglais" à partir du nom anglais (Bird Name)
      - Construit "URL français" à partir du nom français, puis vérifie sa validité pour toutes les lignes.
         Si l'URL est invalide, il la régénère à partir du French Name et, si cela échoue, utilise l'URL anglais.
         Ajoute des messages de debug si l'URL est modifiée.
      - Ne traite les images que si "Image Low" ou "Image High" est manquante.
         Affiche des messages de debug en cas d'images manquantes ou récupérées.
      - Affiche la progression du traitement.
    """
    updated_rows = []
    with open(csv_file, mode='r', newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        original_fieldnames = reader.fieldnames if reader.fieldnames else []
        # On retire la colonne "Image URL" et on s'assure d'avoir nos nouvelles colonnes
        fieldnames = [fn for fn in original_fieldnames if fn != "Image URL"]
        new_columns = ["URL anglais", "URL français", "Image Low", "Image High"]
        for col in new_columns:
            if col not in fieldnames:
                fieldnames.append(col)
        rows = list(reader)
        total_rows = len(rows)

    for index, row in enumerate(rows, start=1):
        # Affichage de la progression
        print(f"Traitement de la ligne {index}/{total_rows}...", end="\r")
        sys.stdout.flush()

        # Construction de l'URL anglais à partir du nom anglais (Bird Name)
        english_name = row.get("Bird Name", "").strip()
        wiki_title_en = english_name.replace(" ", "_")
        url_anglais = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(wiki_title_en)
        
        # Construction de l'URL français à partir du nom français si disponible
        french_name = row.get("French Name", "").strip()
        if french_name:
            wiki_title_fr = french_name.replace(" ", "_")
            url_francais = "https://fr.wikipedia.org/wiki/" + urllib.parse.quote(wiki_title_fr)
        else:
            url_francais = url_anglais
        
        # Vérification systématique de l'URL français pour toute les lignes
        if not is_url_valid(url_francais):
            print(f"\nDebug: URL français invalide pour '{english_name}'. Tentative de régénération...")
            if french_name:
                new_wiki_title_fr = french_name.replace(" ", "_")
                regenerated_url = "https://fr.wikipedia.org/wiki/" + urllib.parse.quote(new_wiki_title_fr)
                if is_url_valid(regenerated_url):
                    print(f"Debug: URL français régénérée pour '{english_name}' : {regenerated_url}")
                    url_francais = regenerated_url
                else:
                    print(f"Debug: Régénération échouée pour '{english_name}'. Utilisation de l'URL anglais.")
                    url_francais = url_anglais
            else:
                print(f"Debug: Aucun French Name disponible pour '{english_name}'. Utilisation de l'URL anglais.")
                url_francais = url_anglais
        row["URL anglais"] = url_anglais
        row["URL français"] = url_francais

        # Vérification des images uniquement si elles sont manquantes
        image_low = row.get("Image Low", "").strip()
        image_high = row.get("Image High", "").strip()
        if not image_low or not image_high:
            print(f"Debug: Images manquantes pour '{english_name}'. Tentative de récupération...")
            # Nous ne récupérons les images que si elles sont absentes
            if not image_low:
                image_low = get_bird_image(english_name, high_quality=False, retries=1)
                if image_low:
                    print(f"Debug: Image low récupérée pour '{english_name}'.")
                else:
                    print(f"Debug: Aucune image low trouvée pour '{english_name}'.")
            if not image_high:
                image_high = get_bird_image(english_name, high_quality=True, retries=1)
                if image_high:
                    print(f"Debug: Image high récupérée pour '{english_name}'.")
                else:
                    if image_low:
                        print(f"Debug: Image high introuvable pour '{english_name}'. Copie de l'image low.")
                        image_high = image_low
                    else:
                        print(f"Debug: Aucune image trouvée pour '{english_name}'.")
            row["Image Low"] = image_low
            row["Image High"] = image_high

        # On retire la colonne "Image URL" si elle existe
        if "Image URL" in row:
            del row["Image URL"]

        updated_rows.append(row)
    
    # Écriture du CSV mis à jour
    with open(output_file, mode="w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)
    print(f"\nCSV mis à jour enregistré dans '{output_file}'.")

if __name__ == "__main__":
    csv_file = "europe_bird_list_updated.csv"
    output_file = "europe_bird_list_updated2.csv"
    update_csv(csv_file, output_file)