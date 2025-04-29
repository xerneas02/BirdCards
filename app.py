from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import csv, random, requests
from abc import ABC, abstractmethod
from flask_session import Session

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Configure session to use the filesystem
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./flask_session"
app.config["SESSION_PERMANENT"] = False
Session(app)

CSV_FILE = "europe_bird_list.csv"

# -------------------------------------------------------------------
# CSV loading and saving
# -------------------------------------------------------------------
def load_birds():
    birds = []
    try:
        with open(CSV_FILE, "r", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                try:
                    row["Difficulty"] = int(row.get("Difficulty", 3))
                except ValueError:
                    row["Difficulty"] = 3
                if "Sound URL" not in row:
                    row["Sound URL"] = ""
                birds.append(row)
    except Exception as e:
        print(f"Error loading CSV: {e}")
    return birds

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

# -------------------------------------------------------------------
# Queue-based bird selection and helper functions
# -------------------------------------------------------------------
def initialize_queue():
    all_names = [bird["Bird Name"] for bird in birds]
    random.shuffle(all_names)
    session["bird_queue"] = all_names

def get_next_bird(selected_diff):
    """Return the first bird in the queue matching the selected difficulties.
       If none match, return the first bird in the queue."""
    queue = session.get("bird_queue", [])
    index = None
    for idx, bird_name in enumerate(queue):
        bird_obj = next((b for b in birds if b["Bird Name"] == bird_name), None)
        if bird_obj and str(bird_obj.get("Difficulty", 3)) in selected_diff:
            index = idx
            break
    if index is None and queue:
        index = 0
    if index is not None:
        selected_name = queue.pop(index)
        session["bird_queue"] = queue
        session["current_bird"] = selected_name
        return next(b for b in birds if b["Bird Name"] == selected_name)
    initialize_queue()
    return get_next_bird(selected_diff)

# -------------------------------------------------------------------
# Helper for reordering feedback based on visible (filtered) birds
# -------------------------------------------------------------------
def get_insertion_index(visible_indices, lower_visible, upper_visible, overall_length):
    if len(visible_indices) >= upper_visible:
        lower_overall = visible_indices[lower_visible - 1]
        upper_overall = visible_indices[upper_visible - 1]
        return random.randint(lower_overall, upper_overall)
    elif len(visible_indices) >= lower_visible:
        lower_overall = visible_indices[lower_visible - 1]
        upper_overall = visible_indices[-1]
        return random.randint(lower_overall, upper_overall)
    else:
        return overall_length

# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------
@app.route("/")
def index():
    language = session.get("language", "EN")
    diff_list = request.args.getlist("diff") or ["1", "2", "3"]
    session["selected_diff"] = diff_list  

    if "bird_queue" not in session or not session["bird_queue"]:
        initialize_queue()

    current_bird = session.get("current_bird")
    bird_obj = None
    if current_bird:
        bird_obj = next((b for b in birds if b["Bird Name"] == current_bird and str(b.get("Difficulty", 3)) in diff_list), None)
    if bird_obj is None:
        bird_obj = get_next_bird(diff_list)

    wiki_url_en = bird_obj.get("URL anglais", "")
    wiki_url_fr = bird_obj.get("URL français", "")
    bird_obj["wiki_url_en"] = wiki_url_en
    bird_obj["wiki_url_fr"] = wiki_url_fr
    bird_obj["has_french_wiki"] = bool(wiki_url_fr and wiki_url_fr != wiki_url_en)

    low_res_url = bird_obj.get("Image Low", "")
    high_res_url = bird_obj.get("Image High", "")
    bird_obj["Image URL"] = low_res_url  
    bird_obj["High Image URL"] = high_res_url

    return render_template("index.html", bird=bird_obj,
                           language=language,
                           selected_diff=diff_list,
                           selected_media=request.args.getlist("media") or ["image", "sound"])

@app.route("/toggle_no_repetition")
def toggle_no_repetition():
    session["no_repetition"] = not session.get("no_repetition", False)
    session.pop("remaining_birds", None)
    diff = request.args.getlist("diff")
    media = request.args.getlist("media")
    noRep = "on" if session.get("no_repetition") else "off"
    return redirect(url_for("index", diff=diff, media=media, noRep=noRep))

@app.route("/set_language")
def set_language():
    lang = request.args.get("lang", "EN")
    session["language"] = lang
    return redirect(url_for("index",
                            diff=request.args.getlist("diff"),
                            media=request.args.getlist("media"),
                            noRep="on" if session.get("no_repetition") else "off"))

@app.route("/process_feedback", methods=["POST"])
def process_feedback():
    current_bird_name = session.get("current_bird")
    queue = session.get("bird_queue", [])
    if not current_bird_name:
        return redirect(url_for("index", diff=session.get("selected_diff"), media=request.args.getlist("media")))
    
    feedback = int(request.form.get("change", 0))
    if feedback > 0:
        # Positive feedback: push current bird to the end.
        queue.append(current_bird_name)
    else:
        # Build list of overall indices for birds matching the current difficulty.
        selected_diff = session.get("selected_diff", [])
        visible_indices = [idx for idx, bird_name in enumerate(queue)
                           if next((b for b in birds if b["Bird Name"] == bird_name and str(b.get("Difficulty", 3)) in selected_diff), None)]
        overall_length = len(queue)
        if feedback < 0:
            # Negative feedback: reinsert between the 10th and 20th visible birds.
            insertion_index = get_insertion_index(visible_indices, 10, 20, overall_length)
        else:
            # Neutral feedback: reinsert between the 30th and 40th visible birds.
            insertion_index = get_insertion_index(visible_indices, 30, 40, overall_length)
        queue.insert(insertion_index, current_bird_name)
    
    session["bird_queue"] = queue
    session.pop("current_bird", None)
    return redirect(url_for("index",
                            diff=request.args.getlist("diff"),
                            media=request.args.getlist("media"),
                            noRep="on" if session.get("no_repetition") else "off"))

@app.route("/reveal")
def reveal():
    language = session.get("language", "EN")
    current_bird_name = session.get("current_bird")
    bird_obj = next((bird for bird in birds if bird["Bird Name"] == current_bird_name), None)
    if not bird_obj:
        return jsonify({"error": "Bird not found"}), 404

    if language == "FR" and bird_obj.get("French Name", "").strip():
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
    current_bird = session.get("current_bird")
    all_names = [bird["Bird Name"] for bird in birds]
    if current_bird:
        try:
            all_names.remove(current_bird)
        except ValueError:
            pass
        random.shuffle(all_names)
        new_queue = [current_bird] + all_names
    else:
        random.shuffle(all_names)
        new_queue = all_names
    session["bird_queue"] = new_queue
    session.pop("remaining_birds", None)
    return redirect(url_for("index",
                            diff=request.args.getlist("diff"),
                            media=request.args.getlist("media"),
                            noRep="on" if session.get("no_repetition") else "off"))

@app.route("/update", methods=["POST"])
def update():
    new_french_name = request.form.get("french_name", "").strip()
    chosen_difficulty = request.form.get("difficulty")
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
    return redirect(url_for("index",
                            diff=request.form.getlist("diff"),
                            media=request.form.getlist("media"),
                            noRep="on" if session.get("no_repetition") else "off"))

@app.route("/update_filters", methods=["POST"])
def update_filters():
    data = request.get_json()
    if data is not None:
        session["selected_diff"] = data.get("diff", [])
        session["selected_media"] = data.get("media", [])
        session["no_repetition"] = (data.get("noRep", "off") == "on")
        filtered_names = [bird["Bird Name"] for bird in birds if is_valid(bird)]
        session["filtered_names"] = filtered_names
        if not session.get("remaining_birds"):
            session["remaining_birds"] = filtered_names.copy()
    return jsonify({"status": "ok"})

def is_valid(bird):
    selected_diff = session.get("selected_diff", [])
    selected_media = session.get("selected_media", [])
    if selected_diff and str(bird.get("Difficulty")) not in selected_diff:
        return False
    if selected_media and bird.get("Media Type") not in selected_media:
        return False
    return True

def get_filtered_birds(birds_list):
    return [bird for bird in birds_list if is_valid(bird)]

if __name__ == "__main__":
    app.run(debug=True)
