const translations = {
    "EN": {
       "reset": "Reset Data",
       "title": "Bird Learning App",
       "reveal": "Reveal Name",
       "wrong": "Got it Wrong",
       "inbetween": "In Between",
       "right": "Got it Right",
       "switch": "Switch to French",
       "diffLabel": "Select difficulty:",
       "diff1Label": "Easy",
       "diff2Label": "Medium",
       "diff3Label": "Difficult",
       "mediaLabel": "Select media type:",
       "mediaSoundLabel": "Sound",
       "filter": "Filter",
       "lightTheme": "Switch to Light Theme",
       "darkTheme": "Switch to Dark Theme"
    },
    "FR": {
       "reset": "Réinitialiser les scores",
       "title": "Appli d'apprentissage des oiseaux",
       "reveal": "Révéler le nom",
       "wrong": "Faux",
       "inbetween": "Neutre",
       "right": "Correct",
       "switch": "Passer en anglais",
       "diffLabel": "Sélectionnez la difficulté :",
       "diff1Label": "Facile",
       "diff2Label": "Moyen",
       "diff3Label": "Difficile",
       "mediaLabel": "Sélectionnez le type de média :",
       "mediaSoundLabel": "Son",
       "filter": "Filtrer",
       "lightTheme": "Passer au thème clair",
       "darkTheme": "Passer au thème sombre"
    }
  };
  
  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateThemeButton();
  }
  
  function updateThemeButton() {
    const btn = document.getElementById("themeToggle");
    const currentTheme = localStorage.getItem('theme') || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const currentLang = document.getElementById("currentLanguage").value || "EN";
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
      document.getElementById("sidebar").classList.remove("active");
    }

    const container = document.getElementById("imageContainer");
    if (container) {
      container.classList.add("loading");
      const imgElement = document.getElementById("birdImage");
      const highResUrl = imgElement.getAttribute("data-src");
      const asyncImage = new Image();
      asyncImage.onload = function() {
        imgElement.src = asyncImage.src; // Remplace l'image basse résolution par la haute
        container.classList.remove("loading");
      }
      asyncImage.onerror = function() {
        imgElement.alt = "Failed to load high resolution image";
        container.classList.remove("loading");
      }
      asyncImage.src = highResUrl;
    }
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
    const elementsToUpdate = [
      { id: "resetButton", key: "reset" },
      { selector: "h1", key: "title" },
      { id: "revealButton", key: "reveal" },
      { id: "wrongButton", key: "wrong" },
      { id: "inbetweenButton", key: "inbetween" },
      { id: "rightButton", key: "right" },
      { id: "langButton", key: "switch" },
      { id: "diffLabel", key: "diffLabel" },
      { id: "diff1Label", key: "diff1Label" },
      { id: "diff2Label", key: "diff2Label" },
      { id: "diff3Label", key: "diff3Label" },
      { id: "mediaLabel", key: "mediaLabel" },
      { id: "mediaSoundLabel", key: "mediaSoundLabel" },
      { id: "filterButton", key: "filter" }
    ];
    elementsToUpdate.forEach(item => {
      let elem = item.id ? document.getElementById(item.id) : document.querySelector(item.selector);
      if (elem) {
        if (elem.tagName === "INPUT" && elem.type === "submit") {
          elem.value = translations[newLang][item.key];
        } else {
          elem.innerText = translations[newLang][item.key];
        }
      }
    });
    fetch("/set_language?lang=" + newLang)
      .then(response => response.text())
      .then(translatedBirdName => {
        const birdNameElem = document.getElementById("birdName");
        if (birdNameElem) {
          birdNameElem.innerText = translatedBirdName;
        }
        updateThemeButton();
      })
      .catch(error => console.error("Language toggle error:", error));
  }
  
  function revealName() {
    fetch("/reveal")
      .then(response => response.json())
      .then(data => {
        const birdNameElem = document.getElementById("birdName");
        if (birdNameElem) birdNameElem.innerText = data.name;
        const imageContainer = document.getElementById("imageContainer");
        if (imageContainer && imageContainer.style.display === "none") {
          imageContainer.style.display = "block";
        }
        const imgElement = document.getElementById("birdImage");
        if (data.image_url && imgElement.src !== data.image_url) {
          imgElement.src = data.image_url;
        }
        const audioContainer = document.getElementById("audioContainer");
        if (audioContainer && audioContainer.style.display === "none") {
          audioContainer.style.display = "block";
        }
        const audioElem = audioContainer ? audioContainer.querySelector("audio source") : null;
        if (audioElem && data.sound_url && audioElem.src !== data.sound_url) {
          audioElem.src = data.sound_url;
          audioContainer.querySelector("audio").load();
        }
      })
      .catch(error => console.error("Error revealing data:", error));
  }
  
  function toggleMenu() {
    const sidebar = document.getElementById("sidebar");
    const menuToggle = document.getElementById("menuToggle");
    if (sidebar) {
      sidebar.classList.toggle("active");
      // Masquer le bouton burger quand le menu est ouvert, et le réafficher quand il est fermé
      if (sidebar.classList.contains("active")) {
        menuToggle.style.display = "none";
      } else {
        menuToggle.style.display = "block";
      }
    }
  }
  
  