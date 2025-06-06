const translations = {
  "EN": {
    "reset": "Reset Data",
    "title": "Bird Learning App",
    "reveal": "Reveal Name",
    "wrong": "Got it Wrong",
    "wrongShort": "Wrong",
    "inbetween": "In Between",
    "inbetweenShort": "Neutral",
    "right": "Got it Right",
    "rightShort": "Right",
    "switch": "Switch to French",
    "diffLabel": "Select difficulty:",
    "diff1Label": "Easy",
    "diff2Label": "Medium",
    "diff3Label": "Difficult",
    "mediaLabel": "Select media type:",
    "mediaSoundLabel": "Sound",
    "filter": "Apply",
    "lightTheme": "Switch to Light Theme",
    "darkTheme": "Switch to Dark Theme",
    "noRepetition": "No Repetition Mode"
  },
  "FR": {
    "reset": "Réinitialiser les scores",
    "title": "Appli d'apprentissage des oiseaux",
    "reveal": "Révéler le nom",
    "wrong": "Mauvaise réponse",
    "wrongShort": "Faux",
    "inbetween": "Réponse partielle",
    "inbetweenShort": "Neutre",
    "right": "Bonne réponse",
    "rightShort": "Correct",
    "switch": "Passer en anglais",
    "diffLabel": "Sélectionnez la difficulté :",
    "diff1Label": "Facile",
    "diff2Label": "Moyen",
    "diff3Label": "Difficile",
    "mediaLabel": "Sélectionnez le type de média :",
    "mediaSoundLabel": "Son",
    "filter": "Appliquer",
    "lightTheme": "Passer au thème clair",
    "darkTheme": "Passer au thème sombre",
    "noRepetition": "Mode sans répétition"
  }
};

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  refreshThemeButton();
}

function refreshThemeButton() {
  const btn = document.getElementById("themeToggle");
  const currentTheme = localStorage.getItem('theme') || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const currentLang = document.getElementById("currentLanguage")?.value || "EN";
  if (btn) {
    btn.textContent = currentTheme === "dark" ? translations[currentLang]["lightTheme"] : translations[currentLang]["darkTheme"];
  }
}

window.onload = function() {
  const storedTheme = localStorage.getItem('theme');
  if (storedTheme) {
    setTheme(storedTheme);
  } else {
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    setTheme(systemPrefersDark ? "dark" : "light");
  }
  
  if (window.innerWidth < 768) {
    document.getElementById("sidebar")?.classList.remove("active");
  }
  
  loadHighResImage();
};

function toggleTheme() {
  const currentTheme = localStorage.getItem('theme') || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  setTheme(currentTheme === "dark" ? "light" : "dark");
}

function toggleLanguage() {
  const currentLangElem = document.getElementById("currentLanguage");
  if (!currentLangElem) return;
  const currentLang = currentLangElem.value;
  const newLang = currentLang === "EN" ? "FR" : "EN";
  currentLangElem.value = newLang;
  updateInterfaceLanguage(newLang);
  // On garde le rafraîchissement visuel via le fetch
  fetch("/set_language?lang=" + newLang)
    .then(() => {
      refreshThemeButton();
      updateBirdName();
    })
    .catch(error => console.error("Language toggle error:", error));
}

function updateInterfaceLanguage(lang) {
  const elementsToUpdate = [
    { id: "resetButton", key: "reset" },
    { selector: "h1", key: "title" },
    { id: "revealButton", key: "reveal" },
    { id: "wrongButtonLarge", key: "wrong" },
    { id: "wrongButtonSmall", key: "wrongShort" },
    { id: "inbetweenButtonLarge", key: "inbetween" },
    { id: "inbetweenButtonSmall", key: "inbetweenShort" },
    { id: "rightButtonLarge", key: "right" },
    { id: "rightButtonSmall", key: "rightShort" },
    { id: "langButton", key: "switch" },
    { id: "diffLabel", key: "diffLabel" },
    { id: "diff1Label", key: "diff1Label" },
    { id: "diff2Label", key: "diff2Label" },
    { id: "diff3Label", key: "diff3Label" },
    { id: "mediaLabel", key: "mediaLabel" },
    { id: "mediaSoundLabel", key: "mediaSoundLabel" },
    { id: "filterButton", key: "filter" },
    { id: "noRepLabel", key: "noRepetition" }
  ];
  
  elementsToUpdate.forEach(item => {
    let elem = item.id ? document.getElementById(item.id) : document.querySelector(item.selector);
    if (elem) {
      // Pour les boutons de feedback, on distingue large (texte complet) et small (texte court)
      if (elem.tagName === "INPUT" && elem.type === "submit") {
        elem.value = translations[lang][item.key];
      } else {
        elem.innerText = translations[lang][item.key];
      }
    }
  });
}

function updateBirdName() {
  const birdNameElem = document.getElementById("birdName");
  if (birdNameElem && birdNameElem.innerText.trim() !== "") {
    fetch("/reveal")
      .then(response => response.json())
      .then(data => {
        birdNameElem.innerText = data.name;
        const wikiLinkElem = document.getElementById("wikiLink");
        if (wikiLinkElem && data.wiki_url) {
          wikiLinkElem.href = data.wiki_url;
        }
      })
      .catch(error => console.error("Error updating bird name:", error));
  }
}

function loadHighResImage() {
  const container = document.getElementById("imageContainer");
  if (!container) {
    console.error("loadHighResImage: container not found");
    return;
  }
  container.classList.add("loading");
  const imgElement = document.getElementById("birdImage");
  const highResUrl = imgElement.getAttribute("data-src");
  console.log("Loading high resolution image from URL:", highResUrl);
  const asyncImage = new Image();
  asyncImage.onload = function() {
    imgElement.src = asyncImage.src;
    container.classList.remove("loading");
    console.log("High resolution image loaded successfully.");
  };
  asyncImage.onerror = function(e) {
    console.error("Error loading high resolution image from URL:", highResUrl, e);
    imgElement.alt = "Failed to load high resolution image";
    container.classList.remove("loading");
  };
  asyncImage.src = highResUrl;
}

function revealName() {
  fetch("/reveal")
    .then(response => response.json())
    .then(data => {
      document.getElementById("birdName").innerText = data.name;
      const wikiLinkElem = document.getElementById("wikiLink");
      if (wikiLinkElem && data.wiki_url) {
        wikiLinkElem.href = data.wiki_url;
        wikiLinkElem.style.display = 'inline-block';
      }
      toggleMediaDisplay(data);
      document.getElementById("revealButton").style.display = "none";
      document.body.classList.add("revealed");
    })
    .catch(error => console.error("Error revealing data:", error));
}

// Déclarez un flag global pour suivre le chargement de l'audio
let isLoading = false;
let sidebarOpenedManually = false;

function toggleMediaDisplay(data) {
  const imgElement = document.getElementById("birdImage");
  if (data.image_url && imgElement.src !== data.image_url) {
    console.log("Updating image source to:", data.image_url);
    imgElement.src = data.image_url;
  }
  
  const audioContainer = document.getElementById("audioContainer");
  if (audioContainer) {
    const audioElem = audioContainer.querySelector("audio");
    if (audioElem && data.sound_url) {
      const sourceElem = audioContainer.querySelector("audio source");
      console.log("Current audio source:", sourceElem.src);
      console.log("New audio source:", data.sound_url);
      
      if (sourceElem.src !== data.sound_url) {
        sourceElem.src = data.sound_url;
        // Indique que le chargement de l'audio débute
        isLoading = true;
        // Différer le chargement pour laisser le temps aux boutons de s'actualiser
        setTimeout(() => {
          try {
            audioElem.load();
            console.log("Audio source updated, load() called.");
          } catch (error) {
            console.error("Error calling audio.load():", error);
          }
          // Le chargement est terminé
          isLoading = false;
        }, 50);
      } else {
        console.log("Audio source unchanged, not reloading.");
      }
    }
    audioContainer.style.display = "block";
  }
}

function toggleMenu() {
  const sidebar = document.getElementById("sidebar");
  if (sidebar) {
    sidebar.classList.toggle("active");
    // On garde un flag pour savoir si l'utilisateur a ouvert le menu manuellement
    sidebarOpenedManually = sidebar.classList.contains("active");
  }
}

document.addEventListener("DOMContentLoaded", function() {
  const filterForm = document.getElementById("filterForm");
  if (filterForm) {
    const updateFilters = () => {
      const diffInputs = filterForm.querySelectorAll("input[name='diff']:checked");
      const mediaInputs = filterForm.querySelectorAll("input[name='media']:checked");
      const diff = Array.from(diffInputs).map(input => input.value);
      const media = Array.from(mediaInputs).map(input => input.value);
      const noRep = document.getElementById("noRep") && document.getElementById("noRep").checked ? "on" : "off";
      fetch("/update_filters", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ diff: diff, media: media, noRep: noRep })
      })
      .then(response => response.json())
      .then(data => console.log("Filters updated:", data))
      .catch(error => console.error("Error updating filters:", error));
    };

    const inputs = filterForm.querySelectorAll('input[type="checkbox"], input[type="radio"]');
    inputs.forEach(input => input.addEventListener("change", updateFilters));
  }
});

// Ajout d'un écouteur pour fermer la sidebar lorsque l'on clique en dehors (pour mobile)
document.addEventListener("click", function(event) {
  // Ne pas faire fermer si un chargement d'audio est en cours
  if (isLoading) return;

  const sidebar = document.getElementById("sidebar");
  const menuToggle = document.getElementById("menuToggle");
  
  // Ne rien faire si le menu n'est pas actif, sur desktop ou si le menu n'a pas été ouvert manuellement
  if (!sidebar.classList.contains("active") || window.innerWidth >= 768 || !sidebarOpenedManually) return;
  
  // Si le clic se fait à l'intérieur de la sidebar ou sur le bouton burger, ne rien faire
  if (sidebar.contains(event.target) || menuToggle.contains(event.target)) return;
  
  // Fermer la sidebar et réafficher le bouton burger
  sidebar.classList.remove("active");
  sidebarOpenedManually = false;
  menuToggle.style.display = "block";
});

