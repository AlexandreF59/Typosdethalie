function changerPhoto(src) {
    const principale = document.getElementById("photo-principale");
    if (principale) {
        principale.src = src;
    }
}

function filtrerCategorie(categorie, bouton) {
    document.querySelectorAll(".filtre-btn").forEach(btn => btn.classList.remove("actif"));
    if (bouton) {
        bouton.classList.add("actif");
    }

    document.querySelectorAll(".carte-creation").forEach(carte => {
        const catCarte = carte.getAttribute("data-categorie");
        if (categorie === "Toutes" || catCarte === categorie) {
            carte.style.display = "block";
        } else {
            carte.style.display = "none";
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(window.location.search);
    const creation = params.get("creation");
    const champMessage = document.getElementById("message");
    if (creation && champMessage) {
        champMessage.value = `Bonjour Thalie,\n\nJe souhaiterais commander ou obtenir plus d'informations concernant la création : "${creation}".\n\nMerci !`;
    }
});