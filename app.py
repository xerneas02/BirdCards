from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import csv, random, math, requests
from abc import ABC, abstractmethod
from flask_session import Session  # Import de Flask-Session
import urllib.parse  # Ajoutez ceci en haut du fichier

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Nécessaire pour la sécurité des sessions

# Configuration de Flask-Session pour stocker les données côté serveur (ici dans le système de fichiers)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./flask_session"  # Dossier de stockage (à créer ou adapter)
app.config["SESSION_PERMANENT"] = False
Session(app)

CSV_FILE = "europe_bird_list.csv"
ALPHA = 0.5  # Poids : exp(-ALPHA * score)

# Interface BirdAPI et implémentation WikipediaBirdAPI.
class BirdAPI(ABC):
    @abstractmethod
    def get_bird_image(self, bird_name: str, high_quality: bool = False) -> str:
        pass

class WikipediaBirdAPI(BirdAPI):
    def __init__(self, thumb_size: int = 300):
        self.base_url = "https://en.wikipedia.org/w/api.php"
        self.thumb_size = thumb_size

    def get_bird_image(self, bird_name: str, high_quality: bool = False) -> str:
        size = self.thumb_size
        if high_quality:
            size = 1024  # Demande une image en haute résolution
        params = {
            "action": "query",
            "prop": "pageimages|pageprops",
            "format": "json",
            "piprop": "thumbnail|original",
            "titles": bird_name,
            "pithumbsize": size,
            "redirects": 1
        }
        headers = {
            "User-Agent": "BirdLearningApp/1.0 (your-email@example.com)"
        }
        try:
            response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            return f"Error: {e}"
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if high_quality and "original" in page:
                return page["original"].get("source", "No image found")
            thumbnail = page.get("thumbnail", {})
            if thumbnail:
                return thumbnail.get("source", "No image found")
        return "No image found"

# Chargement des oiseaux depuis le CSV.
def load_birds():
    birds = []
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                try:
                    row["Score"] = int(row.get("Score", 0))
                except ValueError:
                    row["Score"] = 0
                if "Difficulty" in row and row["Difficulty"]:
                    try:
                        row["Difficulty"] = int(row["Difficulty"])
                    except ValueError:
                        row["Difficulty"] = 3
                else:
                    row["Difficulty"] = 3
                if "Sound URL" not in row:
                    row["Sound URL"] = ""
                birds.append(row)
    except Exception as e:
        print(f"Error loading CSV: {e}")
    return birds

# La sauvegarde globale reste inchangée.
def save_birds(birds):
    try:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as outfile:
            fieldnames = ["Bird Name", "French Name", "Image URL", "Sound URL", "Score", "Difficulty"]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            for bird in birds:
                writer.writerow(bird)
    except Exception as e:
        print(f"Error saving CSV: {e}")

birds = load_birds()

# Initialiser les scores pour l'utilisateur dans la session.
def init_user_scores():
    if "scores" not in session:
        session["scores"] = { bird["Bird Name"]: bird["Score"] for bird in birds }

# Sélection aléatoire pondérée d'un oiseau dans la liste filtrée.
# En mode sans répétition, la liste des oiseaux restants est stockée dans la session.
def weighted_random_bird(birds_list):
    init_user_scores()
    if session.get("no_repetition", False):
        # Construire la liste des noms d'oiseaux correspondant aux filtres
        filtered_names = [bird["Bird Name"] for bird in birds_list]
        # Vérifier si les filtres ont changé
        stored_filter = session.get("filtered_names")
        if stored_filter is None or set(stored_filter) != set(filtered_names):
            # Réinitialiser la liste et stocker les filtres actuels
            remaining = filtered_names.copy()
            session["filtered_names"] = filtered_names
        else:
            remaining = session.get("remaining_birds", [])
            if not remaining:
                remaining = filtered_names.copy()
        chosen_name = random.choice(remaining)
        remaining.remove(chosen_name)
        session["remaining_birds"] = remaining
        bird = next(b for b in birds_list if b["Bird Name"] == chosen_name)
        return bird
    else:
        scores = session["scores"]
        weights = [math.exp(-ALPHA * scores.get(bird["Bird Name"], 0)) for bird in birds_list]
        return random.choices(birds_list, weights=weights, k=1)[0]


@app.route("/")
def index():
    language = session.get("language", "EN")
    diff_list = request.args.getlist("diff") or ["1", "2", "3"]
    try:
        diff_list_int = [int(x) for x in diff_list]
    except Exception:
        diff_list_int = [1, 2, 3]
    filtered_birds = [bird for bird in birds if int(bird.get("Difficulty", 3)) in diff_list_int]
    
    media_filters = request.args.getlist("media") or ["image", "sound"]
    def media_ok(bird):
        ok = True
        if "image" in media_filters:
            ok = ok and (bird.get("Image Low", "").strip() != "")
        if "sound" in media_filters:
            ok = ok and (bird.get("Sound URL", "").strip() != "")
        return ok
    filtered_birds = [bird for bird in filtered_birds if media_ok(bird)]
    if not filtered_birds:
        filtered_birds = birds

    # Mettez à jour la session pour le mode sans répétition
    no_rep = request.args.get("noRep")
    if no_rep is not None:
        session["no_repetition"] = (no_rep == "on")
    
    current_bird_name = session.get("current_bird")
    bird = None
    if current_bird_name:
        bird_obj = next((b for b in filtered_birds if b["Bird Name"] == current_bird_name), None)
        if bird_obj is not None:
            bird = bird_obj
    if bird is None:
        bird = weighted_random_bird(filtered_birds)
        session["current_bird"] = bird["Bird Name"]

    # Utilisation des nouvelles colonnes pré-calculées dans le CSV
    wiki_url_en = bird.get("URL anglais", "")
    wiki_url_fr = bird.get("URL français", "")
    has_fr = bool(wiki_url_fr and wiki_url_fr != wiki_url_en)
    bird["wiki_url_en"] = wiki_url_en
    bird["wiki_url_fr"] = wiki_url_fr
    bird["has_french_wiki"] = has_fr

    # Utilisation des images pré-calculées dans le CSV
    low_res_url = bird.get("Image Low", "")
    high_res_url = bird.get("Image High", "")
    bird["Image URL"] = low_res_url  # Ancienne colonne pour compatibilité, si nécessaire
    bird["High Image URL"] = high_res_url

    return render_template("index.html", bird=bird, language=language,
                           selected_diff=diff_list, selected_media=media_filters)


@app.route("/toggle_no_repetition")
def toggle_no_repetition():
    current = session.get("no_repetition", False)
    session["no_repetition"] = not current
    session.pop("remaining_birds", None)
    diff = request.args.getlist("diff")
    media = request.args.getlist("media")
    noRep = "on" if session["no_repetition"] else "off"
    return redirect(url_for("index", diff=diff, media=media, noRep=noRep))

@app.route("/set_language")
def set_language():
    lang = request.args.get("lang", "EN")
    session["language"] = lang
    current_bird_name = session.get("current_bird")
    bird_obj = next((bird for bird in birds if bird["Bird Name"] == current_bird_name), None)
    if not bird_obj:
        return ""
    if lang == "FR" and "French Name" in bird_obj and bird_obj["French Name"].strip():
        return bird_obj["French Name"]
    else:
        return bird_obj["Bird Name"]

@app.route("/score", methods=["POST"])
def update_score():
    init_user_scores()
    change = int(request.form.get("change", 0))
    current_bird_name = session.get("current_bird")
    scores = session["scores"]
    if current_bird_name in scores:
        scores[current_bird_name] += change
    else:
        scores[current_bird_name] = change
    session["scores"] = scores
    # Supprime l'oiseau courant pour forcer la sélection d'un nouvel oiseau
    session.pop("current_bird", None)
    diff = request.args.getlist("diff")
    media = request.args.getlist("media")
    noRep = "on" if session.get("no_repetition", False) else "off"
    return redirect(url_for("index", diff=diff, media=media, noRep=noRep))




# Helper to check if a French Wikipedia page exists
def french_page_exists(wiki_title: str) -> bool:
    url = "https://fr.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": wiki_title,
        "format": "json",
        "redirects": 1
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "missing" not in page:  # page exists
                return True
        return False
    except Exception as e:
        print("Error checking French Wiki page:", e)
        return False

@app.route("/reveal")
def reveal():
    language = session.get("language", "EN")
    current_bird_name = session.get("current_bird")
    bird_obj = next((bird for bird in birds if bird["Bird Name"] == current_bird_name), None)
    if not bird_obj:
        return jsonify({"error": "Bird not found"}), 404

    # Utilisation des liens pré-calculés.
    if language == "FR" and "French Name" in bird_obj and bird_obj["French Name"].strip():
        name_to_display = bird_obj["French Name"]
        wiki_url = bird_obj.get("wiki_url_fr", bird_obj.get("wiki_url_en"))
    else:
        name_to_display = bird_obj["Bird Name"]
        wiki_url = bird_obj.get("wiki_url_en")
    result = {
        "name": name_to_display,
        "image_url": bird_obj.get("High Image URL", bird_obj.get("Image URL", "")),
        "sound_url": bird_obj.get("Sound URL", ""),
        "wiki_url": wiki_url
    }
    return jsonify(result)

@app.route("/reset")
def reset():
    session["scores"] = { bird["Bird Name"]: 0 for bird in birds }
    session.pop("remaining_birds", None)
    diff = request.args.getlist("diff")
    media = request.args.getlist("media")
    noRep = "on" if session.get("no_repetition", False) else "off"
    return redirect(url_for("index", diff=diff, media=media, noRep=noRep))

@app.route("/toggle_language")
def toggle_language():
    current = session.get("language", "EN")
    session["language"] = "FR" if current == "EN" else "EN"
    diff = request.args.getlist("diff")
    media = request.args.getlist("media")
    noRep = "on" if session.get("no_repetition", False) else "off"
    return redirect(url_for("index", diff=diff, media=media, noRep=noRep))

@app.route("/update", methods=["POST"])
def update():
    new_french_name = request.form.get("french_name", "").strip()
    chosen_difficulty = request.form.get("difficulty", None)
    current_bird_name = session.get("current_bird")
    for bird in birds:
        if bird["Bird Name"] == current_bird_name:
            bird["French Name"] = new_french_name
            if chosen_difficulty:
                try:
                    bird["Difficulty"] = int(chosen_difficulty)
                except ValueError:
                    bird["Difficulty"] = 3
            break
    diff = request.form.getlist("diff")
    media = request.form.getlist("media")
    noRep = "on" if session.get("no_repetition", False) else "off"
    return redirect(url_for("index", diff=diff, media=media, noRep=noRep))

if __name__ == "__main__":
    app.run(debug=True)#, host="0.0.0.0", port=8080)
