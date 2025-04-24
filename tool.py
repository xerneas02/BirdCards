import csv
import requests
import re
import urllib.parse
import time

def get_scientific_name(english_name):
    # Recherche la page Wikipedia de l'oiseau (ajoute " bird" pour plus de précision)
    search_url = "https://en.wikipedia.org/w/api.php"
    params_search = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": english_name + " bird"
    }
    try:
        response = requests.get(search_url, params=params_search, timeout=10)
        data = response.json()
    except Exception as e:
        print(f"Erreur lors de la recherche de {english_name}: {e}")
        return ""
    search_results = data.get("query", {}).get("search", [])
    if not search_results:
        return ""
    page_title = search_results[0]["title"]

    # Récupérer l'identifiant Wikidata via les pageprops de la page Wikipedia
    params_page = {
        "action": "query",
        "format": "json",
        "titles": page_title,
        "prop": "pageprops"
    }
    try:
        response_page = requests.get(search_url, params=params_page, timeout=10)
        data_page = response_page.json()
    except Exception as e:
        print(f"Erreur lors de la récupération de la page {page_title}: {e}")
        return ""
    pages = data_page.get("query", {}).get("pages", {})
    wikidata_id = ""
    for page in pages.values():
        wikidata_id = page.get("pageprops", {}).get("wikibase_item", "")
        if wikidata_id:
            break
    if not wikidata_id:
        return ""
    
    # Interroger Wikidata pour obtenir le nom scientifique (P225)
    wikidata_url = "https://www.wikidata.org/w/api.php"
    params_wd = {
        "action": "wbgetclaims",
        "format": "json",
        "entity": wikidata_id,
        "property": "P225"
    }
    try:
        response_wd = requests.get(wikidata_url, params=params_wd, timeout=10)
        data_wd = response_wd.json()
    except Exception as e:
        print(f"Erreur lors de la récupération de Wikidata pour {wikidata_id}: {e}")
        return ""
    claims = data_wd.get("claims", {}).get("P225", [])
    if claims:
        try:
            latin_name = claims[0]["mainsnak"]["datavalue"]["value"]
            return latin_name
        except Exception as e:
            print(f"Erreur lors de l'extraction du nom latin pour {english_name}: {e}")
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

def get_bird_image(bird_name, high_quality=False):
    """
    Récupère l'image d'une page Wikipedia via API, 
    en utilisant le paramètre pithumbsize (500 pour basse qualité,
    1024 pour haute qualité).
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
        print(f"Erreur lors de la récupération de l'image pour '{bird_name}': {e}")
    return ""

def fetch_sound_url(bird_name):
    """
    Recherche le premier enregistrement sur xeno-canto pour l'oiseau.
    """
    base_url = "https://www.xeno-canto.org/api/2/recordings"
    params = {"query": bird_name}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        recordings = data.get("recordings", [])
        if recordings:
            return recordings[0].get("file")
    except Exception as e:
        print(f"Erreur lors de la recherche du son pour '{bird_name}': {e}")
    return None

def fetch_view_count(bird_name, lang="fr"):
    """
    Récupère le nombre total de vues d'un article Wikipedia sur une période donnée.
    """
    project = f"{lang}.wikipedia.org"
    access = "all-access"
    agent = "user"
    granularity = "monthly"
    start_str = "20240301"
    end_str = "20250331"
    article = bird_name.replace(" ","_")
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/{access}/{agent}/{article}/{granularity}/{start_str}/{end_str}"
    headers = {"User-Agent": "BirdCardsApp/1.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    total_views = sum(item.get("views", 0) for item in data.get("items", []))
    return total_views

def get_bird_info_by_latin(latin_name):
    """
    Recherche sur Wikipedia en utilisant une recherche avec "latin_name bird"
    pour obtenir la page correspondante. Extrait le nom anglais (titre de la page)
    et le nom français via langlinks.
    Génère également :
      - URL anglais et URL français (vérifiée, sinon URL anglais)
      - Image Low et Image High (si Image High manquante, copie Image Low)
      - Sound URL, Score, View Count et Difficulty.
    """
    search_url = "https://en.wikipedia.org/w/api.php"
    params_search = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": latin_name + " bird",
        "srlimit": 1
    }
    try:
        response = requests.get(search_url, params=params_search, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Erreur lors de la recherche Wikipedia pour '{latin_name}': {e}")
        return None
    data = response.json()
    search_results = data.get("query", {}).get("search", [])
    if not search_results:
        print(f"Aucun article trouvé pour '{latin_name}'")
        return None
    page_title = search_results[0]["title"]
    english_name = page_title  # Utilisé comme nom anglais

    # Récupérer le nom français via langlinks
    params_lang = {
        "action": "query",
        "format": "json",
        "titles": page_title,
        "prop": "langlinks",
        "lllang": "fr"
    }
    try:
        response_lang = requests.get(search_url, params=params_lang, timeout=10)
        response_lang.raise_for_status()
    except Exception as e:
        print(f"Erreur lors de la récupération du titre français pour '{page_title}': {e}")
        french_name = english_name
    else:
        data_lang = response_lang.json()
        pages = data_lang.get("query", {}).get("pages", {})
        french_name = english_name
        for page in pages.values():
            langlinks = page.get("langlinks", [])
            if langlinks:
                french_name = langlinks[0].get("*", english_name)
                break

    # Constructions des URLs
    wiki_title_en = english_name.replace(" ", "_")
    url_anglais = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(wiki_title_en)
    if french_name:
        wiki_title_fr = french_name.replace(" ", "_")
        url_francais = "https://fr.wikipedia.org/wiki/" + urllib.parse.quote(wiki_title_fr)
    else:
        url_francais = url_anglais
    if not is_url_valid(url_francais):
        print(f"Warning: URL français invalide pour '{english_name}'. Utilisation de l'URL anglais à la place.")
        url_francais = url_anglais

    # Récupérer l'image basse qualité et haute qualité
    image_low = get_bird_image(english_name, high_quality=False)
    image_high = get_bird_image(english_name, high_quality=True)
    if not image_high and image_low:
        print(f"Warning: Image haute qualité introuvable pour '{english_name}'. Copie de l'image basse qualité.")
        image_high = image_low

    # Récupérer le son via xeno-canto
    sound_url = fetch_sound_url(english_name)
    if not sound_url and french_name != english_name:
        sound_url = fetch_sound_url(french_name)

    score = 0
    try:
        view_count = fetch_view_count(french_name)
    except Exception as e:
        print(f"Erreur lors de la récupération des vues pour {french_name}: {e}")
        view_count = 0

    try:
        numeric_views = int(view_count)
        if numeric_views > 53000:
            difficulty = 1
        elif numeric_views > 2000:
            difficulty = 2
        else:
            difficulty = 3
    except Exception:
        difficulty = 3

    # Affichage des informations récupérées (une ligne par information)
    print(f"Bird Name: {english_name}")
    print(f"French Name: {french_name}")
    print(f"Latin Name: {latin_name}")
    print(f"URL anglais: {url_anglais}")
    print(f"URL français: {url_francais}")
    print(f"Image Low: {image_low}")
    print(f"Image High: {image_high}")
    print(f"Sound URL: {sound_url if sound_url else 'None'}")
    print(f"View Count: {view_count}")
    print(f"Difficulty: {difficulty}")
    print(f"Score: {score}")

    return {
        "Bird Name": english_name,
        "French Name": french_name,
        "Latin Name": latin_name,
        "URL anglais": url_anglais,
        "URL français": url_francais,
        "Image Low": image_low,
        "Image High": image_high,
        "Sound URL": sound_url if sound_url else "",
        "Score": score,
        "View Count": view_count,
        "Difficulty": difficulty
    }

def get_bird_info_by_english(english_name):
    """
    Recherche sur Wikipedia en utilisant le nom anglais pour obtenir la page correspondante.
    Extrait le nom anglais officiel (titre de la page) et le nom français via langlinks.
    Génère également :
      - URL anglais et URL français (vérifiée, sinon URL anglais)
      - Image Low et Image High (si Image High manquante, copie Image Low)
      - Sound URL, Score, View Count et Difficulty.
    Le champ "Latin Name" est laissé vide.
    """
    search_url = "https://en.wikipedia.org/w/api.php"
    params_search = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": english_name,
        "srlimit": 1
    }
    try:
        response = requests.get(search_url, params=params_search, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Erreur lors de la recherche Wikipedia pour '{english_name}': {e}")
        return None
    data = response.json()
    search_results = data.get("query", {}).get("search", [])
    if not search_results:
        print(f"Aucun article trouvé pour '{english_name}'")
        return None
    page_title = search_results[0]["title"]
    official_english_name = page_title  # Titre officiel de la page

    # Récupérer le nom français via langlinks
    params_lang = {
        "action": "query",
        "format": "json",
        "titles": page_title,
        "prop": "langlinks",
        "lllang": "fr"
    }
    try:
        response_lang = requests.get(search_url, params=params_lang, timeout=10)
        response_lang.raise_for_status()
    except Exception as e:
        print(f"Erreur lors de la récupération du titre français pour '{page_title}': {e}")
        french_name = official_english_name
    else:
        data_lang = response_lang.json()
        pages = data_lang.get("query", {}).get("pages", {})
        french_name = official_english_name
        for page in pages.values():
            langlinks = page.get("langlinks", [])
            if langlinks:
                french_name = langlinks[0].get("*", official_english_name)
                break

    # Constructions des URLs
    wiki_title_en = official_english_name.replace(" ", "_")
    url_anglais = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(wiki_title_en)
    if french_name:
        wiki_title_fr = french_name.replace(" ", "_")
        url_francais = "https://fr.wikipedia.org/wiki/" + urllib.parse.quote(wiki_title_fr)
    else:
        url_francais = url_anglais
    if not is_url_valid(url_francais):
        print(f"Warning: URL français invalide pour '{official_english_name}'. Utilisation de l'URL anglais à la place.")
        url_francais = url_anglais

    # Récupérer l'image basse qualité et haute qualité
    image_low = get_bird_image(official_english_name, high_quality=False)
    image_high = get_bird_image(official_english_name, high_quality=True)
    if not image_high and image_low:
        print(f"Warning: Image haute qualité introuvable pour '{official_english_name}'. Copie de l'image basse qualité.")
        image_high = image_low

    # Récupérer le son via xeno-canto
    sound_url = fetch_sound_url(official_english_name)
    if not sound_url and french_name != official_english_name:
        sound_url = fetch_sound_url(french_name)

    score = 0
    try:
        view_count = fetch_view_count(french_name)
    except Exception as e:
        print(f"Erreur lors de la récupération des vues pour {french_name}: {e}")
        view_count = 0

    try:
        numeric_views = int(view_count)
        if numeric_views > 53000:
            difficulty = 1
        elif numeric_views > 2000:
            difficulty = 2
        else:
            difficulty = 3
    except Exception:
        difficulty = 3

    latin_name = get_scientific_name(official_english_name)
    # Affichage des informations récupérées (une ligne par information)
    print(f"Bird Name: {official_english_name}")
    print(f"French Name: {french_name}")
    print(f"Latin Name: {latin_name}")
    print(f"URL anglais: {url_anglais}")
    print(f"URL français: {url_francais}")
    print(f"Image Low: {image_low}")
    print(f"Image High: {image_high}")
    print(f"Sound URL: {sound_url if sound_url else 'None'}")
    print(f"View Count: {view_count}")
    print(f"Difficulty: {difficulty}")
    print(f"Score: {score}")

    return {
        "Bird Name": official_english_name,
        "French Name": french_name,
        "Latin Name": latin_name,
        "URL anglais": url_anglais,
        "URL français": url_francais,
        "Image Low": image_low,
        "Image High": image_high,
        "Sound URL": sound_url if sound_url else "",
        "Score": score,
        "View Count": view_count,
        "Difficulty": difficulty
    }

def add_bird_by_latin(latin_name, csv_file):
    """
    Prend en paramètre le nom latin d'un oiseau, vérifie qu'il n'est pas déjà présent
    dans le fichier CSV et ajoute une nouvelle ligne avec les informations récupérées :
      - Bird Name, French Name et Latin Name
      - URL anglais et URL français (validée)
      - Image Low et Image High (Image High = Image Low si non disponible)
      - Sound URL, Score, View Count et Difficulty.
    """
    try:
        with open(csv_file, mode='r', newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames if reader.fieldnames else []
    except FileNotFoundError:
        rows = []
        fieldnames = ["Bird Name", "French Name", "Latin Name", "URL anglais", "URL français",
                      "Image Low", "Image High", "Sound URL", "Score", "View Count", "Difficulty"]

    # Vérifier si l'oiseau existe déjà (comparaison par Latin Name, insensible à la casse)
    for row in rows:
        if row.get("Latin Name", "").strip().lower() == latin_name.strip().lower():
            print(f"L'oiseau avec le nom latin '{latin_name}' existe déjà.")
            return

    bird_info = get_bird_info_by_latin(latin_name)
    if not bird_info:
        print(f"Echec de récupération des informations pour '{latin_name}'.")
        return

    rows.append(bird_info)
    # S'assurer que toutes les clés sont présentes
    keys = set()
    for row in rows:
        keys.update(row.keys())
    fieldnames = list(keys)

    with open(csv_file, mode='w', newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"L'oiseau '{latin_name}' a été ajouté au fichier CSV '{csv_file}'.")

def add_bird_by_english(english_name, csv_file):
    """
    Prend en paramètre le nom anglais d'un oiseau, vérifie qu'il n'est pas déjà présent
    dans le fichier CSV et ajoute une nouvelle ligne avec les informations récupérées via get_bird_info_by_english.
    """
    try:
        with open(csv_file, mode='r', newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = reader.fieldnames if reader.fieldnames else []
    except FileNotFoundError:
        rows = []
        fieldnames = ["Bird Name", "French Name", "Latin Name", "URL anglais", "URL français",
                      "Image Low", "Image High", "Sound URL", "Score", "View Count", "Difficulty"]

    # Vérifier si l'oiseau existe déjà (comparaison par Bird Name, insensible à la casse)
    for row in rows:
        if row.get("Bird Name", "").strip().lower() == english_name.strip().lower():
            print(f"L'oiseau avec le nom anglais '{english_name}' existe déjà.")
            return

    bird_info = get_bird_info_by_english(english_name)
    if not bird_info:
        print(f"Echec de récupération des informations pour '{english_name}'.")
        return

    rows.append(bird_info)
    # S'assurer que toutes les clés sont présentes
    keys = set()
    for row in rows:
        keys.update(row.keys())
    fieldnames = list(keys)

    with open(csv_file, mode='w', newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"L'oiseau '{english_name}' a été ajouté au fichier CSV '{csv_file}'.")

def sort_csv_by_latin(csv_file, output_file=None):
    """
    Trie le fichier CSV par ordre alphabétique des noms latins, réorganise les colonnes selon l'ordre défini
    et réécrit le fichier. Si output_file n'est pas fourni, le fichier d'origine est écrasé.
    L'ordre des colonnes sera :
      Latin Name, Bird Name, French Name, Difficulty, View Count, URL anglais, URL français, Image Low, Image High, Sound URL, Score
    """
    if output_file is None:
        output_file = csv_file

    with open(csv_file, mode='r', newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        existing_fields = reader.fieldnames if reader.fieldnames else []

    rows.sort(key=lambda row: row.get("Latin Name", "").lower())

    ordered_fields = ["Latin Name", "Bird Name", "French Name", "Difficulty", "View Count",
                      "URL anglais", "URL français", "Image Low", "Image High", "Sound URL", "Score"]

    for field in existing_fields:
        if field not in ordered_fields:
            ordered_fields.append(field)

    with open(output_file, mode='w', newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Fichier CSV trié par ordre alphabétique (Latin Name) et réorganisé, enregistré dans '{output_file}'.")

if __name__ == "__main__":
    english_name_input = "Kea"
    csv_file = "europe_bird_list.csv"
    # Pour ajouter un nouvel oiseau par nom anglais, décommentez la ligne suivante :
    add_bird_by_english(english_name_input, csv_file)
    sort_csv_by_latin(csv_file)