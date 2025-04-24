let birds = [];
let currentBird = null;
let scores = {};
let noRepetition = false;
let remainingBirds = [];
let language = "EN"; // Default language

// Load bird data
fetch("birds.json")
  .then(response => response.json())
  .then(data => {
    birds = data;
    initScores();
    selectRandomBird();
  });

// Initialize scores using cookies
function initScores() {
  const storedScores = getCookie("scores");
  scores = storedScores ? JSON.parse(storedScores) : {};
  birds.forEach(bird => {
    if (!(bird["Bird Name"] in scores)) {
      scores[bird["Bird Name"]] = 0;
    }
  });
  setCookie("scores", JSON.stringify(scores), 365);
}

// Select a random bird
function selectRandomBird() {
  const filteredBirds = applyFilters();
  if (noRepetition) {
    if (remainingBirds.length === 0) {
      remainingBirds = [...filteredBirds];
    }
    const index = Math.floor(Math.random() * remainingBirds.length);
    currentBird = remainingBirds.splice(index, 1)[0];
  } else {
    const weights = filteredBirds.map(bird => Math.exp(-0.5 * scores[bird["Bird Name"]]));
    const totalWeight = weights.reduce((a, b) => a + b, 0);
    const random = Math.random() * totalWeight;
    let cumulativeWeight = 0;
    for (let i = 0; i < filteredBirds.length; i++) {
      cumulativeWeight += weights[i];
      if (random < cumulativeWeight) {
        currentBird = filteredBirds[i];
        break;
      }
    }
  }
  displayBird(currentBird);
}

// Display bird information
function displayBird(bird) {
  document.getElementById("birdImage").src = bird["Image URL"] || "";
  document.getElementById("birdSound").src = bird["Sound URL"] || "";
  document.getElementById("birdName").textContent = "";
  const wikiUrl = language === "FR" && bird["French Name"]
    ? `https://fr.wikipedia.org/wiki/${encodeURIComponent(bird["French Name"])}`
    : `https://en.wikipedia.org/wiki/${encodeURIComponent(bird["Bird Name"])}`;
  document.getElementById("wikiLink").href = wikiUrl;
}

// Reveal the bird's name
function revealName() {
  document.getElementById("birdName").textContent =
    language === "FR" && currentBird["French Name"]
      ? currentBird["French Name"]
      : currentBird["Bird Name"];
}

// Update the score
function updateScore(change) {
  scores[currentBird["Bird Name"]] += change;
  setCookie("scores", JSON.stringify(scores), 365);
  selectRandomBird();
}

// Reset scores
function resetScores() {
  scores = {};
  birds.forEach(bird => {
    scores[bird["Bird Name"]] = 0;
  });
  setCookie("scores", JSON.stringify(scores), 365);
  alert("Scores reset!");
}

// Apply filters
function applyFilters() {
  const selectedDifficulties = Array.from(document.querySelectorAll("input[name='diff']:checked")).map(input => parseInt(input.value));
  const selectedMedia = Array.from(document.querySelectorAll("input[name='media']:checked")).map(input => input.value);
  noRepetition = document.getElementById("noRep").checked;

  return birds.filter(bird => {
    return selectedDifficulties.includes(bird.Difficulty) &&
           (selectedMedia.includes("image") ? bird["Image URL"] : true) &&
           (selectedMedia.includes("sound") ? bird["Sound URL"] : true);
  });
}

// Toggle theme
function toggleTheme() {
  const theme = document.documentElement.getAttribute("data-theme") === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("theme", theme);
}

// Toggle menu
function toggleMenu() {
  document.getElementById("sidebar").classList.toggle("active");
}

// Toggle language
function toggleLanguage() {
  language = language === "EN" ? "FR" : "EN";
  document.getElementById("langButton").textContent = language === "EN" ? "Switch to French" : "Passer en anglais";
  selectRandomBird();
}

// Cookie helpers
function setCookie(name, value, days) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
}

function getCookie(name) {
  return document.cookie.split("; ").reduce((r, v) => {
    const parts = v.split("=");
    return parts[0] === name ? decodeURIComponent(parts[1]) : r;
  }, "");
}