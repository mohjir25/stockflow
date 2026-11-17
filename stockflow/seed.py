"""Remplit la base avec des données de démonstration.

Usage :  python seed.py          (ajoute les données si la base est vide)
         python seed.py --reset  (efface tout et recommence)
"""

import random
import sqlite3
import sys
from datetime import datetime, timedelta

from app import create_app

CATEGORIES = ["Informatique", "Fournitures de bureau", "Outillage",
              "Consommables", "Mobilier", "Sécurité / EPI"]

ARTICLES = [
    # ref, nom, catégorie, qté, seuil, prix, emplacement
    ("INF-001", "Écran 24\" Full HD", "Informatique", 14, 5, 129.90, "A1-02"),
    ("INF-002", "Clavier sans fil AZERTY", "Informatique", 3, 8, 24.50, "A1-03"),
    ("INF-003", "Souris optique USB", "Informatique", 42, 10, 9.90, "A1-03"),
    ("INF-004", "Câble HDMI 2 m", "Informatique", 6, 10, 7.80, "A1-04"),
    ("INF-005", "Disque SSD 1 To", "Informatique", 9, 4, 74.00, "A1-05"),
    ("INF-006", "Station d'accueil USB-C", "Informatique", 2, 3, 89.00, "A1-05"),
    ("BUR-001", "Ramette papier A4 80 g", "Fournitures de bureau", 120, 40, 4.20, "B2-01"),
    ("BUR-002", "Stylos bille bleus (boîte de 50)", "Fournitures de bureau", 7, 5, 11.50, "B2-02"),
    ("BUR-003", "Classeur à levier A4", "Fournitures de bureau", 35, 15, 2.90, "B2-03"),
    ("BUR-004", "Post-it 76x76 (lot de 12)", "Fournitures de bureau", 4, 6, 8.40, "B2-02"),
    ("OUT-001", "Perceuse-visseuse 18 V", "Outillage", 5, 2, 159.00, "C1-01"),
    ("OUT-002", "Jeu de tournevis 12 pièces", "Outillage", 11, 4, 22.00, "C1-02"),
    ("OUT-003", "Mètre ruban 5 m", "Outillage", 18, 6, 6.50, "C1-02"),
    ("OUT-004", "Niveau laser", "Outillage", 1, 2, 119.00, "C1-03"),
    ("CON-001", "Toner laser noir", "Consommables", 3, 4, 68.00, "B3-01"),
    ("CON-002", "Cartouche couleur (pack)", "Consommables", 8, 3, 52.00, "B3-01"),
    ("CON-003", "Piles AA (lot de 24)", "Consommables", 15, 5, 12.90, "B3-02"),
    ("MOB-001", "Chaise de bureau ergonomique", "Mobilier", 6, 2, 189.00, "D1-01"),
    ("MOB-002", "Caisson 3 tiroirs", "Mobilier", 4, 1, 99.00, "D1-02"),
    ("EPI-001", "Gants de protection (paire)", "Sécurité / EPI", 26, 20, 3.80, "C2-01"),
    ("EPI-002", "Lunettes de sécurité", "Sécurité / EPI", 9, 10, 5.60, "C2-01"),
    ("EPI-003", "Gilet haute visibilité", "Sécurité / EPI", 14, 6, 4.90, "C2-02"),
]

MOTIFS_ENTREE = ["Réception commande fournisseur", "Retour employé", "Réassort", "Inventaire annuel"]
MOTIFS_SORTIE = ["Attribution nouvel employé", "Remplacement matériel", "Service technique",
                 "Commande interne", "Casse / perte"]


def main(reset: bool = False) -> None:
    app = create_app()
    conn = sqlite3.connect(app.config["DATABASE"])
    cur = conn.cursor()
    if reset:
        cur.executescript("DELETE FROM mouvements; DELETE FROM articles; DELETE FROM categories;")
    elif cur.execute("SELECT COUNT(*) FROM articles").fetchone()[0]:
        print("La base contient déjà des données (utilisez --reset pour repartir de zéro).")
        return

    random.seed(42)
    cat_ids = {}
    for nom in CATEGORIES:
        cur.execute("INSERT INTO categories (nom) VALUES (?)", (nom,))
        cat_ids[nom] = cur.lastrowid

    maintenant = datetime.now()
    for ref, nom, cat, qte, seuil, prix, empl in ARTICLES:
        cur.execute(
            """INSERT INTO articles (reference, nom, categorie_id, quantite, seuil_min,
                                     prix_unitaire, emplacement) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ref, nom, cat_ids[cat], qte, seuil, prix, empl))
        art_id = cur.lastrowid
        # Historique cohérent : quelques mouvements sur les 30 derniers jours
        for _ in range(random.randint(1, 4)):
            type_ = random.choice(["entree", "sortie"])
            motif = random.choice(MOTIFS_ENTREE if type_ == "entree" else MOTIFS_SORTIE)
            date = maintenant - timedelta(days=random.randint(0, 30), hours=random.randint(0, 9))
            cur.execute(
                "INSERT INTO mouvements (article_id, type, quantite, motif, date) VALUES (?, ?, ?, ?, ?)",
                (art_id, type_, random.randint(1, 10), motif, date.strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()
    print(f"{len(ARTICLES)} articles et leur historique ont été ajoutés.")


if __name__ == "__main__":
    main(reset="--reset" in sys.argv)
