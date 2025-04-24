import csv
import requests

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

def add_latin_names_to_csv(input_csv, output_csv):
    updated_rows = []
    with open(input_csv, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Ajout de la nouvelle colonne "Latin Name"
        fieldnames = reader.fieldnames + ["Latin Name"]
        for row in reader:
            english_name = row["Bird Name"]
            latin = get_scientific_name(english_name)
            row["Latin Name"] = latin
            print(f"{english_name}: {latin}")
            updated_rows.append(row)
    with open(output_csv, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)
    print(f"Fichier CSV mis à jour : {output_csv}")

if __name__ == "__main__":
    input_file = "europe_bird_list.csv"
    output_file = "europe_bird_list_with_latin.csv"
    add_latin_names_to_csv(input_file, output_file)