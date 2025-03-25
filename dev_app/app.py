from flask import Flask, render_template, request, redirect, url_for, session
import csv, random, math, requests
from abc import ABC, abstractmethod

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Nécessaire pour la gestion de session

CSV_FILE = "europe_bird_list_valid.csv"  
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

# Chargement des données depuis le CSV.
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
                # Si la colonne Difficulty n'existe pas ou est vide, on affecte une valeur par défaut (ici 3)
                if "Difficulty" in row and row["Difficulty"]:
                    try:
                        row["Difficulty"] = int(row["Difficulty"])
                    except ValueError:
                        row["Difficulty"] = 3
                else:
                    row["Difficulty"] = 3
                birds.append(row)
    except Exception as e:
        print(f"Error loading CSV: {e}")
    return birds

# Sauvegarde des données dans le CSV.
def save_birds(birds):
    try:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as outfile:
            fieldnames = ["Bird Name", "French Name", "Image URL", "Score", "Difficulty"]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            for bird in birds:
                writer.writerow(bird)
    except Exception as e:
        print(f"Error saving CSV: {e}")

birds = load_birds()

# Ici, nous utilisons l'index pour parcourir les enregistrements
@app.route("/")
def index():
    try:
        index = int(request.args.get("index", 0))
    except ValueError:
        index = 0
    if index < 0 or index >= len(birds):
        index = 0
    language = session.get("language", "EN")
    bird = birds[index]
    session["current_bird"] = bird["Bird Name"]
    
    # Récupère une image en haute résolution via WikipediaBirdAPI.
    wiki_api = WikipediaBirdAPI(thumb_size=1024)
    high_res_url = wiki_api.get_bird_image(bird["Bird Name"], high_quality=True)
    if high_res_url and high_res_url != "No image found" and not high_res_url.startswith("Error"):
         bird["Image URL"] = high_res_url
         
    return render_template("index.html", bird=bird, language=language, index=index, total=len(birds))

@app.route("/previous")
def previous():
    try:
        index = int(request.args.get("index", 0))
    except ValueError:
        index = 0
    index = max(0, index - 1)
    return redirect(url_for("index", index=index))

@app.route("/next_record")
def next_record():
    try:
        index = int(request.args.get("index", 0))
    except ValueError:
        index = 0
    index = min(len(birds) - 1, index + 1)
    return redirect(url_for("index", index=index))

@app.route("/set_language")
def set_language():
    lang = request.args.get("lang", "EN")
    session["language"] = lang
    current_bird_name = session.get("current_bird")
    bird_obj = next((bird for bird in birds if bird["Bird Name"] == current_bird_name), None)
    if not bird_obj:
        return ""
    if lang == "FR" and "French Name" in bird_obj and bird_obj["French Name"].strip():
        name_to_display = bird_obj["French Name"]
    else:
        name_to_display = bird_obj["Bird Name"]
    return name_to_display

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
    return redirect(url_for("index"))

@app.route("/reveal")
def reveal():
    language = session.get("language", "EN")
    current_bird_name = session.get("current_bird")
    bird_obj = next((bird for bird in birds if bird["Bird Name"] == current_bird_name), None)
    if not bird_obj:
        return ""
    if language == "FR" and "French Name" in bird_obj and bird_obj["French Name"].strip():
        name_to_display = bird_obj["French Name"]
    else:
        name_to_display = bird_obj["Bird Name"]
    return name_to_display

@app.route("/reset")
def reset():
    global birds
    for bird in birds:
        bird["Score"] = 0
    save_birds(birds)
    return redirect(url_for("index"))

@app.route("/toggle_language")
def toggle_language():
    current = session.get("language", "EN")
    session["language"] = "FR" if current == "EN" else "EN"
    return redirect(url_for("index"))

# Nouvelle route pour mettre à jour le nom français ET la difficulté.
@app.route("/update", methods=["POST"])
def update():
    try:
        index = int(request.args.get("index", 0))
    except ValueError:
        index = 0
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
                    bird["Difficulty"] = chosen_difficulty
            break
    save_birds(birds)
    return redirect(url_for("index", index=index))

if __name__ == "__main__":
    app.run(debug=True)
