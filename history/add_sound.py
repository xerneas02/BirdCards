import csv
import requests

def fetch_sound_url(bird_name):
    """
    Recherche sur xeno-canto le premier enregistrement pour
    l'oiseau dont le nom (latin ou autre) est passé en paramètre.
    Renvoie le lien vers le fichier sonore s'il est trouvé.
    """
    base_url = "https://www.xeno-canto.org/api/2/recordings"
    params = {"query": bird_name}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        recordings = data.get("recordings", [])
        if recordings:
            # On prend le lien du premier enregistrement trouvé
            return recordings[0].get("file")
    except Exception as e:
        print(f"Erreur lors de la recherche pour '{bird_name}': {e}")
    return None

def main():
    input_file = "europe_bird_list_with_latin.csv"
    output_file = "europe_bird_list_updated.csv"

    updated_rows = []

    with open(input_file, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        headers = reader.fieldnames
        for row in reader:
            # Si le champ "Sound URL" est vide, on recherche une URL sur xeno-canto
            if not row["Sound URL"].strip():
                sound_url = None
                # Tentative avec le nom latin
                if "Latin Name" in row and row["Latin Name"].strip():
                    latin_name = row["Latin Name"]
                    print(f"Recherche du son pour '{latin_name}' (nom latin)...")
                    sound_url = fetch_sound_url(latin_name)
                # Si la recherche avec le nom latin échoue, on tente avec le nom anglais
                if not sound_url:
                    bird_name_english = row["Bird Name"]
                    print(f"Aucun son trouvé avec le nom latin, recherche du son pour '{bird_name_english}' (nom anglais)...")
                    sound_url = fetch_sound_url(bird_name_english)
                    # Si toujours aucun résultat, tentative avec le nom français si disponible
                    if not sound_url and "French Name" in row and row["French Name"].strip():
                        bird_name_french = row["French Name"]
                        print(f"Aucun son trouvé pour '{bird_name_english}', tentative avec '{bird_name_french}' (nom français)...")
                        sound_url = fetch_sound_url(bird_name_french)
                if sound_url:
                    print(f"Son trouvé pour '{row['Bird Name']}': {sound_url}")
                    row["Sound URL"] = sound_url
                else:
                    print(f"Aucun son trouvé pour '{row['Bird Name']}'")
            updated_rows.append(row)

    with open(output_file, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(updated_rows)
    print(f"CSV mis à jour sauvegardé dans '{output_file}'.")

if __name__ == "__main__":
    main()