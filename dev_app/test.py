import csv
import requests

def get_sound_url(bird_name):
    """
    Recherche un enregistrement audio pour l'oiseau (nom anglais) via l'API Xeno‑canto.
    Retourne l'URL du fichier audio du premier enregistrement trouvé,
    ou une chaîne vide si aucun enregistrement n'est trouvé.
    """
    base_url = "https://www.xeno-canto.org/api/2/recordings"
    params = {"query": bird_name}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; MyApp/1.0; +http://example.com)"}
    try:
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Erreur lors de la récupération du son pour '{bird_name}': {e}")
        return ""
    try:
        data = response.json()
    except Exception as e:
        print(f"Erreur de décodage JSON pour '{bird_name}': {e}")
        return ""
    recordings = data.get("recordings", [])
    if recordings:
        file_url = recordings[0].get("file", "")
        if file_url:
            return file_url
        else:
            print(f"Aucun fichier audio trouvé dans l'enregistrement pour '{bird_name}'")
            return ""
    else:
        print(f"Aucun enregistrement trouvé pour '{bird_name}'")
        return ""

def update_csv_with_sounds(input_file, output_file):
    rows = []
    try:
        with open(input_file, "r", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            fieldnames = reader.fieldnames.copy() if reader.fieldnames is not None else []
            if "Sound URL" not in fieldnames:
                fieldnames.append("Sound URL")
            for row in reader:
                bird_name = row.get("Bird Name", "").strip()
                sound_url = get_sound_url(bird_name)
                row["Sound URL"] = sound_url
                rows.append(row)
    except Exception as e:
        print("Erreur lors de la lecture du CSV :", e)
        return

    try:
        with open(output_file, "w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Fichier CSV mis à jour avec les sons sauvegardé sous '{output_file}'")
    except Exception as e:
        print("Erreur lors de l'écriture du CSV :", e)

if __name__ == "__main__":
    input_csv = "europe_bird_list_valid.csv"
    output_csv = "europe_bird_list_valid_with_sounds.csv"
    update_csv_with_sounds(input_csv, output_csv)
