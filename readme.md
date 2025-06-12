# BirdCards

BirdCards is a personal project—born out of a desire to create a simple and user-friendly platform for learning about birds. The application allows users to learn bird names, view images, listen to sounds, and check additional information from Wikipedia. It supports both English and French languages and offers various options to filter birds according to difficulty and media type.

## Features

- **Bird Learning Interface:**  
  Display bird names (in English or French) along with images and sounds.  
- **Filtering Options:**  
  Users can filter birds by difficulty level and media type.
- **No Repetition Mode:**  
  A mode that ensures birds are not repeated until all have been seen.
- **Dynamic Theme:**  
  Users can toggle between dark and light themes with immediate visual feedback.
- **Language Toggle:**  
  Seamlessly switch between English and French.
- **Responsive Design:**  
  The interface adapts to different screen sizes, including mobile devices, with options such as a burger menu for navigation and shortened text on smaller screens.

## Technology Stack

- **Backend:**  
  - Python (Flask)  
  - CSV for storing bird information  
  - Flask-Session to manage server–side sessions  
  - Requests for API calls

- **Frontend:**  
  - HTML, CSS, and JavaScript  
  - AJAX for updating filters without full page reloads  
  - Responsive design to support mobile and desktop views

- **External Data Sources:**  
  - Bird names (English and French translations) and Latin names are sourced from Wikipedia.  
  - Bird images and sound URLs (from Xeno-canto) are also integrated into the application.  
  - The project combines multiple sources to build its bird list, including various image resolutions and translations.

## Installation

1. **Clone the repository:**
   ```
   git clone https://github.com/xerneas02/BirdCards.git
   cd BirdCards
   ```

2. **Set up your Python virtual environment:**
   ```
   python3 -m venv .venv
   source .venv/bin/activate   # On Windows use: .venv\Scripts\activate
   ```

3. **Install the required packages:**
   ```
   pip install -r requirements.txt
   ```
   The `requirements.txt` file includes:
   - Flask
   - Flask-Session
   - requests
   - pycountry
   - pycountry-convert
   - gunicorn

## Running the Application

For **development**, you can simply run:
```
python app.py
```

For a **production** setup, it is recommended to use Gunicorn (or another WSGI server). For example:
```
gunicorn -w 4 app:app
```
Additional options like binding to a specific address, timeout settings, and logging can be added as needed. See the [Gunicorn documentation](https://docs.gunicorn.org/en/stable/settings.html) for more details.

## How It Works

1. **Bird Selection:**  
   The application loads a list of birds from a CSV file and uses a weighted random selection algorithm based on the user’s score.  
   - In "No Repetition" mode, birds are not repeated until all filtered birds have been shown.
   - Filters based on user-selected difficulty and media type are applied. The filters are updated via AJAX and stored in the session.

2. **User Interaction:**  
   - Users can reveal the bird name, view its image, and play its sound.
   - Buttons for “Got it Wrong”, “In Between”, and “Got it Right” update the bird’s score and select the next bird.
   - A sidebar provides filtering options, theme toggling, language switching, and a reset option.

3. **Frontend Behavior:**  
   - Dynamic theme adjustment based on user preference, stored in localStorage.
   - The interface automatically updates filter settings without a full page reload.
   - The application adapts text labels on buttons for smaller screens.

4. **Data Sources & Credits:**  
   - Bird names, images, and both French and English translations are primarily sourced from Wikipedia.
   - Bird sound URLs are retrieved from Xeno-canto.
   - Additional data (such as difficulty scores) are curated and managed via CSV files.

## Usage

- **Filtering and Options:**  
  Change filters (difficulty, media type, and no repetition mode) using the sidebar. The updated filters are saved via AJAX, ensuring the next bird is selected based on your preferences.
  
- **Scoring:**  
  Click the respective score buttons (“Got it Wrong”, “In Between”, or “Got it Right”) after attempting to guess the bird’s name. This updates the bird’s score, and a new bird is selected accordingly.

- **Theme and Language:**  
  Use the toggle buttons in the sidebar to switch between dark/light themes and English/French languages seamlessly.

## Contributing

This project is a personal endeavor, but contributions and feedback are welcome. Feel free to fork the repository and submit pull requests.

## Contact

For questions or further discussion, you can reach me on 
  - Discord: **xerneas02**
  - email : **xerneas1702@gmail.com**
---

BirdCards is a simple, personal project designed to combine multiple online data sources into a unified bird learning platform. Enjoy learning about birds and feel free to enhance the project to suit your own needs!
