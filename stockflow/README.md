# ▣ StockFlow

**Application web de gestion d'inventaire pour les PME** : suivi des articles, entrées et sorties de stock, alertes de réapprovisionnement et export Excel.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?logo=flask)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![Tests](https://img.shields.io/badge/tests-7%20passed-brightgreen)
![Licence](https://img.shields.io/badge/licence-MIT-blue)

![Tableau de bord](docs/screenshots/dashboard.png)

---

## ✨ Fonctionnalités

- **Tableau de bord** : nombre d'articles, unités en stock, valeur totale du stock, articles sous le seuil, valeur par catégorie et derniers mouvements
- **Gestion des articles** : référence, désignation, catégorie, emplacement, prix unitaire et seuil d'alerte, avec recherche et filtre par catégorie
- **Mouvements de stock** : entrées et sorties avec motif, mise à jour automatique des quantités, refus des sorties supérieures au stock disponible
- **Alertes de réapprovisionnement** : liste des articles sous le seuil, avec une quantité à commander suggérée
- **Historique par article** : tous les mouvements d'un article, du plus récent au plus ancien
- **Export Excel** : inventaire complet au format `.xlsx`, avec en-têtes stylés et articles en alerte surlignés
- **Interface responsive** : utilisable sur ordinateur comme sur tablette

## 📸 Captures d'écran

| Liste des articles | Fiche article |
|---|---|
| ![Articles](docs/screenshots/articles.png) | ![Détail](docs/screenshots/article-detail.png) |

| Alertes de stock | Nouveau mouvement |
|---|---|
| ![Alertes](docs/screenshots/alertes.png) | ![Mouvement](docs/screenshots/nouveau-mouvement.png) |

## 🚀 Installation

**Prérequis :** Python 3.10 ou plus récent.

```bash
# 1. Cloner le dépôt
git clone https://github.com/<mohjir25>/stockflow.git
cd stockflow

# 2. Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. (Optionnel) Charger des données de démonstration
python seed.py

# 5. Lancer l'application
python app.py
```

Ouvrez ensuite **http://127.0.0.1:5000** dans votre navigateur.

## 🧪 Tests

```bash
pytest
```

Les tests couvrent la création d'articles, l'unicité des références, les entrées et sorties, le refus d'une sortie supérieure au stock, les alertes et l'export Excel.

## 🗂️ Structure du projet

```
stockflow/
├── app.py               # Application Flask : routes et logique métier
├── database.py          # Schéma SQLite et connexion
├── seed.py              # Données de démonstration
├── requirements.txt
├── static/css/style.css # Interface
├── templates/           # Pages HTML (Jinja2)
├── tests/test_app.py    # Tests automatisés (pytest)
└── docs/screenshots/    # Captures d'écran
```

## 🧱 Modèle de données

```
categories (id, nom)
      │ 1
      │
      ▼ n
articles (id, reference, nom, categorie_id, quantite, seuil_min, prix_unitaire, emplacement)
      │ 1
      │
      ▼ n
mouvements (id, article_id, type[entree|sortie], quantite, motif, date)
```

## 🛣️ Évolutions prévues

- [ ] Comptes utilisateurs et rôles (administrateur, magasinier)
- [ ] Gestion des fournisseurs et bons de commande
- [ ] Étiquettes avec code-barres / QR code
- [ ] Import d'inventaire depuis un fichier Excel
- [ ] API REST

## 📄 Licence

Projet distribué sous licence MIT. Voir [LICENSE](LICENSE).

---

Réalisé par **Mohamed Jirari**
