import os
import shutil
import json
from datetime import date

DOSSIER_BOUTIQUE = "boutique"
DOSSIER_DIST = "dist"
DOMAINE = "https://lestyposdethalie.fr"

SCRIPT_STATS = '<script data-goatcounter="https://lestyposdethalie.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>\n</body>'


def ajouter_stats(html):
    return html.replace("</body>", SCRIPT_STATS)


def lire_infos_txt(chemin_fichier):
    infos = {
        "titre": "Sans titre",
        "categorie": "Autres",
        "prix": "Sur demande",
        "disponibilite": "Disponible immédiatement",
        "delai": "",
        "mots_cles": [],
        "dimensions": "Non précisées",
        "description": ""
    }
    with open(chemin_fichier, "r", encoding="utf-8-sig") as f:
        for ligne in f:
            if ":" in ligne:
                cle, valeur = ligne.split(":", 1)
                cle = cle.strip().lower()
                valeur = valeur.strip()
                if cle == "titre":
                    infos["titre"] = valeur
                elif cle in ["catégorie", "categorie"]:
                    infos["categorie"] = valeur
                elif cle == "prix":
                    infos["prix"] = valeur
                elif cle in ["disponibilité", "disponibilite"]:
                    infos["disponibilite"] = valeur
                elif cle in ["délai", "delai"]:
                    infos["delai"] = valeur
                elif cle in ["mots-clés", "mots-cles", "mots clefs"]:
                    infos["mots_cles"] = [m.strip() for m in valeur.split(",") if m.strip()]
                elif cle == "dimensions":
                    infos["dimensions"] = valeur
                elif cle == "description":
                    infos["description"] = valeur
    return infos


def formater_prix(prix_str):
    try:
        float(prix_str.replace(",", "."))
        return f"{prix_str} €"
    except ValueError:
        return prix_str


def generer_site():
    # 1. Nettoyer et recréer le dossier dist/
    if os.path.exists(DOSSIER_DIST):
        shutil.rmtree(DOSSIER_DIST)
    os.makedirs(os.path.join(DOSSIER_DIST, "creations"), exist_ok=True)
    os.makedirs(os.path.join(DOSSIER_DIST, "produits"), exist_ok=True)

    # 2. Copier les fichiers statiques (CSS, JS, images fixes, CNAME)
    for dossier in ["css", "js", "images"]:
        if os.path.exists(dossier):
            shutil.copytree(dossier, os.path.join(DOSSIER_DIST, dossier))
    if os.path.exists("CNAME"):
        shutil.copy("CNAME", os.path.join(DOSSIER_DIST, "CNAME"))

    catalogue = []
    categories_trouvees = set()
    urls_sitemap = [
        f"{DOMAINE}/",
        f"{DOMAINE}/catalogue.html",
        f"{DOMAINE}/a-propos.html",
        f"{DOMAINE}/contact.html"
    ]

    # 3. Parcourir chaque sous-dossier de boutique/
    if os.path.exists(DOSSIER_BOUTIQUE):
        for slug in sorted(os.listdir(DOSSIER_BOUTIQUE)):
            chemin_article = os.path.join(DOSSIER_BOUTIQUE, slug)
            if not os.path.isdir(chemin_article):
                continue

            fichier_txt = os.path.join(chemin_article, "infos.txt")
            if not os.path.exists(fichier_txt):
                print(f"⚠️ Ignoré (pas de infos.txt) : {slug}")
                continue

            infos = lire_infos_txt(fichier_txt)
            infos["slug"] = slug
            categories_trouvees.add(infos["categorie"])

            # Récupérer et copier les images par ordre alphabétique
            extensions_valides = (".jpg", ".jpeg", ".png", ".webp")
            images = sorted([
                f for f in os.listdir(chemin_article)
                if f.lower().endswith(extensions_valides)
            ])

            dest_images = os.path.join(DOSSIER_DIST, "produits", slug)
            os.makedirs(dest_images, exist_ok=True)
            for img in images:
                shutil.copy(os.path.join(chemin_article, img), os.path.join(dest_images, img))

            infos["images"] = [f"produits/{slug}/{img}" for img in images]
            infos["image_principale"] = infos["images"][0] if infos["images"] else ""
            catalogue.append(infos)

            # Générer la fiche individuelle dist/creations/<slug>.html
            generer_page_creation(infos)
            urls_sitemap.append(f"{DOMAINE}/creations/{slug}.html")

    # 4. Sauvegarder catalogue.json
    with open(os.path.join(DOSSIER_DIST, "produits", "catalogue.json"), "w", encoding="utf-8") as f:
        json.dump(catalogue, f, ensure_ascii=False, indent=2)

    # 5. Générer les pages principales et le sitemap.xml
    generer_pages_principales(catalogue, sorted(categories_trouvees))
    generer_sitemap(urls_sitemap)
    print(f"✅ Site généré avec succès ({len(catalogue)} création(s) dans dist/) !")


def generer_page_creation(item):
    with open("templates/creation.html", "r", encoding="utf-8") as f:
        html = f.read()

    galerie_html = "\n".join([
        f'<img src="../{img}" alt="{item["titre"]}" class="miniature" onclick="changerPhoto(this.src)">'
        for img in item["images"]
    ])

    statut_texte = item["disponibilite"]
    if item["delai"] and "commande" in statut_texte.lower():
        statut_texte += f" ({item['delai']})"

    remplacements = {
        "{{TITRE}}": item["titre"],
        "{{CATEGORIE}}": item["categorie"],
        "{{PRIX}}": formater_prix(item["prix"]),
        "{{DISPONIBILITE}}": statut_texte,
        "{{DIMENSIONS}}": item["dimensions"],
        "{{DESCRIPTION}}": item["description"],
        "{{IMAGE_PRINCIPALE}}": f"../{item['image_principale']}",
        "{{GALERIE}}": galerie_html,
        "{{LIEN_COMMANDE}}": f"../contact.html?creation={item['titre']}"
    }
    for cle, val in remplacements.items():
        html = html.replace(cle, val)

    with open(os.path.join(DOSSIER_DIST, "creations", f"{item['slug']}.html"), "w", encoding="utf-8") as f:
        f.write(ajouter_stats(html))


def generer_pages_principales(catalogue, categories):
    for page in ["a-propos.html", "contact.html"]:
        if os.path.exists(f"templates/{page}"):
            with open(f"templates/{page}", "r", encoding="utf-8") as f:
                html = f.read()
            with open(os.path.join(DOSSIER_DIST, page), "w", encoding="utf-8") as f:
                f.write(ajouter_stats(html))

    # Boutons de filtres automatiques selon les catégories présentes dans boutique/
    boutons_html = '<button class="filtre-btn actif" onclick="filtrerCategorie(\'Toutes\', this)">Toutes</button>\n'
    for cat in categories:
        boutons_html += f'<button class="filtre-btn" onclick="filtrerCategorie(\'{cat}\', this)">{cat}</button>\n'

    # Cartes produits
    cartes_html = ""
    for item in catalogue:
        cartes_html += f"""
        <article class="carte-creation" data-categorie="{item['categorie']}" data-tags="{','.join(item['mots_cles']).lower()}">
            <a href="creations/{item['slug']}.html">
                <div class="carte-image">
                    <img src="{item['image_principale']}" alt="{item['titre']}" loading="lazy">
                    <span class="badge-dispo">{item['disponibilite']}</span>
                </div>
                <div class="carte-infos">
                    <span class="carte-cat">{item['categorie']}</span>
                    <h3>{item['titre']}</h3>
                    <p class="carte-prix">{formater_prix(item['prix'])}</p>
                </div>
            </a>
        </article>
        """

    # Image d'accueil (la 1ère création trouvée par défaut)
    image_hero = catalogue[0]["image_principale"] if catalogue else ""

    if os.path.exists("templates/index.html"):
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html = f.read()
        html = html.replace("{{GRILLE_CREATIONS}}", cartes_html)
        html = html.replace("{{IMAGE_HERO}}", image_hero)
        with open(os.path.join(DOSSIER_DIST, "index.html"), "w", encoding="utf-8") as f:
            f.write(ajouter_stats(html))

    if os.path.exists("templates/catalogue.html"):
        with open("templates/catalogue.html", "r", encoding="utf-8") as f:
            html = f.read()
        html = html.replace("{{GRILLE_CREATIONS}}", cartes_html)
        html = html.replace("{{BOUTONS_CATEGORIES}}", boutons_html)
        with open(os.path.join(DOSSIER_DIST, "catalogue.html"), "w", encoding="utf-8") as f:
            f.write(ajouter_stats(html))


def generer_sitemap(urls):
    aujourdhui = date.today().isoformat()
    lignes = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for url in urls:
        lignes.append(f"  <url><loc>{url}</loc><lastmod>{aujourdhui}</lastmod></url>")
    lignes.append("</urlset>")
    with open(os.path.join(DOSSIER_DIST, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lignes))


if __name__ == "__main__":
    generer_site()