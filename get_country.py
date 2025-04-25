import requests
import pycountry
import pycountry_convert

def get_species_key(name):
    resp = requests.get(
        "https://api.gbif.org/v1/species/match",
        params={"name": name}
    )
    resp.raise_for_status()
    data = resp.json()
    key = data.get("usageKey")
    if not key:
        raise ValueError(f"Aucun taxon trouvé pour « {name} »")
    return key

def extract_countries(results):
    """
    Extrait au mieux des codes ISO alpha-2 ou des textes décrivant des régions à partir d'une liste
    de résultats de distributions. La fonction utilise en priorité le champ "country" puis "locationId".
    Si ces champs ne permettent pas d'obtenir un code valide, elle examine le champ "locality" pour détecter
    un nom de continent ou une région (comparaison insensible à la casse). 
    Pour le cas particulier de "middle america", on le considère comme "MX" (Mexique).
    Renvoie un dictionnaire {code: occurrence}.
    """
    freq = {}
    # Liste des continents/régions connus en minuscule
    known_continents = {"africa", "antarctica", "asia", "europe", "north america", "oceania", "south america", "middle america"}
    for d in results:
        code = None
        handled = False
        # Priorité au champ "country"
        if "country" in d:
            val = d["country"].strip()
            if len(val) == 2 and val.isalpha():
                code = val.upper()
                handled = True
            else:
                try:
                    matches = pycountry.countries.search_fuzzy(val)
                    if matches:
                        code = matches[0].alpha_2
                        handled = True
                except Exception:
                    pass
        # Ensuite, le champ "locationId"
        if not handled and "locationId" in d:
            loc = d["locationId"].strip()
            if loc.upper().startswith("ISO3166:"):
                code = loc.split("ISO3166:")[1].strip().upper()
                handled = True
            else:
                try:
                    matches = pycountry.countries.search_fuzzy(loc)
                    if matches:
                        code = matches[0].alpha_2
                        handled = True
                except Exception:
                    code = loc.upper()
                    handled = True
        # Enfin, on teste le champ "locality" de façon insensible à la casse
        if not handled and "locality" in d:
            loc = d["locality"].strip()
            candidate = loc.lower()
            if candidate == "middle america":
                # Considère "middle america" comme le Mexique (code ISO MX)
                code = "MX"
                handled = True
            elif candidate in known_continents:
                code = candidate.capitalize()
                handled = True
        if code:
            freq[code] = freq.get(code, 0) + 1
    return freq

def get_countries_from_distributions(key):
    """
    Récupère les codes ou régions des distributions via l’endpoint /distributions.
    Agrège les occurrences sur toutes les pages et retire le code "NO" (Norway)
    s'il apparaît moins de 2 fois.
    Renvoie une liste triée des codes/régions retenus.
    """
    countries_count = {}
    offset = 0
    while True:
        resp = requests.get(
            f"https://api.gbif.org/v1/species/{key}/distributions",
            params={"limit": 1000, "offset": offset}
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        print(results)
        if not results:
            break
        page_counts = extract_countries(results)
        for code, count in page_counts.items():
            countries_count[code] = countries_count.get(code, 0) + count
        offset += len(results)
        if data.get("endOfRecords", True):
            break
    # Ne conserver "NO" (Norway) que s'il apparaît au moins 2 fois.
    if "NO" in countries_count and countries_count["NO"] < 2:
        del countries_count["NO"]
    return sorted(countries_count.keys())

def iso2_to_name(codes):
    """
    Convertit uniquement les codes ISO alpha-2 valides en noms de pays.
    Les codes non valides (ex. "Africa", "Middle America") sont ignorés.
    """
    names = []
    for code in codes:
        if len(code) == 2 and code.isalpha():
            country = pycountry.countries.get(alpha_2=code)
            names.append(country.name if country else code)
    return names

def iso2_to_continents(codes):
    """
    Convertit une liste de codes (ISO alpha-2 ou noms de régions) en noms de continents/régions.
    Si le code est composé de 2 lettres, il est converti en continent via pycountry_convert.
    Sinon, s'il correspond exactement (insensible à la casse) à l'un des continents reconnus,
    il est intégré tel quel.
    """
    continent_mapping = {
        'AF': 'Africa',
        'AN': 'Antarctica',
        'AS': 'Asia',
        'EU': 'Europe',
        'NA': 'North America',
        'OC': 'Oceania',
        'SA': 'South America'
    }
    valid_continents = set(continent_mapping.values())
    continents = set()
    for code in codes:
        if len(code) == 2 and code.isalpha():
            try:
                continent_code = pycountry_convert.country_alpha2_to_continent_code(code)
                continent_name = continent_mapping.get(continent_code)
                if continent_name:
                    continents.add(continent_name)
            except Exception as e:
                print(f"Erreur lors de la conversion du code {code} en continent: {e}")
        else:
            candidate = code.strip().lower()
            valid = {c.lower() for c in valid_continents}
            if candidate in valid:
                for c in valid_continents:
                    if c.lower() == candidate:
                        continents.add(c)
                        break
    return sorted(continents)

if __name__ == "__main__":
    bird = "Phylloscopus schwarzi"
    try:
        key = get_species_key(bird)
        print(f"Clé du taxon pour « {bird} » : {key}")
        codes = get_countries_from_distributions(key)
        print(f"Codes/régions extraits : {codes}")
        pays = iso2_to_name(codes)
        if pays:
            print(f"L’oiseau « {bird} » est documenté dans {len(pays)} pays :")
            for p in sorted(pays):
                print(f" - {p}")
        else:
            print(f"Aucune distribution pays trouvée pour « {bird} ».")
        continents = iso2_to_continents(codes)
        if continents:
            print(f"Et il est présent sur {len(continents)} continents/régions:")
            for c in continents:
                print(f" - {c}")
        else:
            print("Aucun continent trouvé.")
    except Exception as e:
        print(f"Erreur : {e}")
