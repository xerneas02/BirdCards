from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import csv, random, math, requests
from abc import ABC, abstractmethod

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Nécessaire pour la gestion de session

CSV_FILE = "europe_bird_list_valid.csv"  # Doit contenir : Bird Name, French Name, Image URL, Sound URL, Score, Difficulty
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

# Sauvegarde des oiseaux dans le CSV.
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

# Sélection aléatoire pondérée d'un oiseau dans la liste filtrée.
def weighted_random_bird(birds_list):
    weights = [math.exp(-ALPHA * bird["Score"]) for bird in birds_list]
    return random.choices(birds_list, weights=weights, k=1)[0]

@app.route("/")
def index():
    language = session.get("language", "EN")
    # Récupération du filtre de difficulté via GET ("diff")
    diff_list = request.args.getlist("diff")
    if not diff_list:
        diff_list = ["1", "2", "3"]
    try:
        diff_list_int = [int(x) for x in diff_list]
    except Exception:
        diff_list_int = [1, 2, 3]
    filtered_birds = [bird for bird in birds if int(bird.get("Difficulty", 3)) in diff_list_int]
    
    # Filtrer par média
    media_filters = request.args.getlist("media")
    if not media_filters:
        media_filters = ["image", "sound"]
    def media_ok(bird):
        ok = True
        if "image" in media_filters:
            ok = ok and (bird.get("Image URL", "").strip() != "")
        if "sound" in media_filters:
            ok = ok and (bird.get("Sound URL", "").strip() != "")
        return ok
    filtered_birds = [bird for bird in filtered_birds if media_ok(bird)]
    if not filtered_birds:
        filtered_birds = birds

    bird = weighted_random_bird(filtered_birds)
    session["current_bird"] = bird["Bird Name"]

    # Récupération d'une image haute résolution via WikipediaBirdAPI.
    wiki_api = WikipediaBirdAPI(thumb_size=1024)
    high_res_url = wiki_api.get_bird_image(bird["Bird Name"], high_quality=True)
    if high_res_url and high_res_url != "No image found" and not high_res_url.startswith("Error"):
         bird["Image URL"] = high_res_url

    return render_template("index.html", bird=bird, language=language,
                           selected_diff=diff_list, selected_media=media_filters)

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
    change = int(request.form.get("change", 0))
    current_bird_name = session.get("current_bird")
    global birds
    for bird in birds:
        if bird["Bird Name"] == current_bird_name:
            bird["Score"] = int(bird["Score"]) + change
            break
    save_birds(birds)
    diff = request.args.getlist("diff")
    media = request.args.getlist("media")
    return redirect(url_for("index", diff=diff, media=media))

@app.route("/reveal")
def reveal():
    language = session.get("language", "EN")
    current_bird_name = session.get("current_bird")
    bird_obj = next((bird for bird in birds if bird["Bird Name"] == current_bird_name), None)
    if not bird_obj:
        return jsonify({"error": "Bird not found"}), 404
    if language == "FR" and "French Name" in bird_obj and bird_obj["French Name"].strip():
        name_to_display = bird_obj["French Name"]
    else:
        name_to_display = bird_obj["Bird Name"]
    result = {
        "name": name_to_display,
        "image_url": bird_obj.get("Image URL", ""),
        "sound_url": bird_obj.get("Sound URL", "")
    }
    return jsonify(result)

@app.route("/reset")
def reset():
    global birds
    for bird in birds:
        bird["Score"] = 0
    save_birds(birds)
    diff = request.args.getlist("diff")
    media = request.args.getlist("media")
    return redirect(url_for("index", diff=diff, media=media))

@app.route("/toggle_language")
def toggle_language():
    current = session.get("language", "EN")
    session["language"] = "FR" if current == "EN" else "EN"
    diff = request.args.getlist("diff")
    media = request.args.getlist("media")
    return redirect(url_for("index", diff=diff, media=media))

@app.route("/update", methods=["POST"])
def update():
    new_french_name = request.form.get("french_name", "").strip()
    chosen_difficulty = request.form.get("difficulty", None)
    global birds
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
    save_birds(birds)
    filter_diff = request.form.getlist("diff")
    filter_media = request.form.getlist("media")
    return redirect(url_for("index", diff=filter_diff, media=filter_media))

if __name__ == "__main__":
    app.run(debug=True)
