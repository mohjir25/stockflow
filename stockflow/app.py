"""StockFlow — application web de gestion d'inventaire.

Lancement :  python app.py   puis ouvrir http://127.0.0.1:5000
"""

import io
import os
from datetime import datetime

from flask import (Flask, abort, flash, redirect, render_template, request,
                   send_file, url_for)
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from database import close_db, get_db, init_db

__version__ = "1.2.0"


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("STOCKFLOW_SECRET", "dev-change-me"),
        DATABASE=os.path.join(app.instance_path, "stockflow.db"),
    )
    if config:
        app.config.update(config)

    init_db(app.config["DATABASE"])
    app.teardown_appcontext(close_db)

    @app.context_processor
    def inject_globals():
        nb_alertes = get_db().execute(
            "SELECT COUNT(*) FROM articles WHERE quantite <= seuil_min"
        ).fetchone()[0]
        return {"nb_alertes": nb_alertes, "version": __version__}

    @app.template_filter("euros")
    def euros(valeur):
        return f"{valeur:,.2f} €".replace(",", " ").replace(".", ",")

    # ------------------------------------------------------------------ #
    # Tableau de bord
    # ------------------------------------------------------------------ #
    @app.route("/")
    def dashboard():
        db = get_db()
        stats = db.execute(
            """SELECT COUNT(*)                         AS nb_articles,
                      COALESCE(SUM(quantite), 0)       AS nb_unites,
                      COALESCE(SUM(quantite * prix_unitaire), 0) AS valeur
               FROM articles"""
        ).fetchone()
        alertes = db.execute(
            """SELECT a.*, c.nom AS categorie FROM articles a
               LEFT JOIN categories c ON c.id = a.categorie_id
               WHERE a.quantite <= a.seuil_min
               ORDER BY (a.quantite * 1.0 / MAX(a.seuil_min, 1)) LIMIT 8"""
        ).fetchall()
        derniers = db.execute(
            """SELECT m.*, a.nom, a.reference FROM mouvements m
               JOIN articles a ON a.id = m.article_id
               ORDER BY m.date DESC, m.id DESC LIMIT 8"""
        ).fetchall()
        par_categorie = db.execute(
            """SELECT COALESCE(c.nom, 'Sans catégorie') AS nom,
                      SUM(a.quantite * a.prix_unitaire) AS valeur
               FROM articles a LEFT JOIN categories c ON c.id = a.categorie_id
               GROUP BY c.nom ORDER BY valeur DESC"""
        ).fetchall()
        max_valeur = max((r["valeur"] or 0 for r in par_categorie), default=1) or 1
        return render_template(
            "dashboard.html", stats=stats, alertes=alertes, derniers=derniers,
            par_categorie=par_categorie, max_valeur=max_valeur,
        )

    # ------------------------------------------------------------------ #
    # Articles
    # ------------------------------------------------------------------ #
    @app.route("/articles")
    def articles():
        q = request.args.get("q", "").strip()
        cat = request.args.get("categorie", type=int)
        sql = """SELECT a.*, c.nom AS categorie FROM articles a
                 LEFT JOIN categories c ON c.id = a.categorie_id WHERE 1=1"""
        params: list = []
        if q:
            sql += " AND (a.nom LIKE ? OR a.reference LIKE ? OR a.emplacement LIKE ?)"
            params += [f"%{q}%"] * 3
        if cat:
            sql += " AND a.categorie_id = ?"
            params.append(cat)
        sql += " ORDER BY a.reference"
        db = get_db()
        return render_template(
            "articles.html",
            articles=db.execute(sql, params).fetchall(),
            categories=db.execute("SELECT * FROM categories ORDER BY nom").fetchall(),
            q=q, cat=cat,
        )

    def _lire_formulaire_article():
        f = request.form
        try:
            data = {
                "reference": f["reference"].strip().upper(),
                "nom": f["nom"].strip(),
                "categorie_id": f.get("categorie_id", type=int) or None,
                "quantite": int(f.get("quantite", 0) or 0),
                "seuil_min": int(f.get("seuil_min", 0) or 0),
                "prix_unitaire": float(str(f.get("prix_unitaire", 0) or 0).replace(",", ".")),
                "emplacement": f.get("emplacement", "").strip(),
            }
        except (KeyError, ValueError):
            return None, "Valeurs invalides dans le formulaire."
        if not data["reference"] or not data["nom"]:
            return None, "La référence et le nom sont obligatoires."
        if min(data["quantite"], data["seuil_min"], data["prix_unitaire"]) < 0:
            return None, "Les valeurs numériques doivent être positives."
        return data, None

    @app.route("/articles/nouveau", methods=["GET", "POST"])
    def article_nouveau():
        db = get_db()
        if request.method == "POST":
            data, erreur = _lire_formulaire_article()
            if not erreur:
                try:
                    db.execute(
                        """INSERT INTO articles (reference, nom, categorie_id, quantite,
                               seuil_min, prix_unitaire, emplacement)
                           VALUES (:reference, :nom, :categorie_id, :quantite,
                                   :seuil_min, :prix_unitaire, :emplacement)""", data)
                    db.commit()
                    flash(f"Article {data['reference']} créé.", "success")
                    return redirect(url_for("articles"))
                except db.IntegrityError:
                    erreur = "Cette référence existe déjà."
            flash(erreur, "error")
        return render_template(
            "article_form.html", article=request.form or None,
            categories=db.execute("SELECT * FROM categories ORDER BY nom").fetchall(),
        )

    @app.route("/articles/<int:article_id>/modifier", methods=["GET", "POST"])
    def article_modifier(article_id):
        db = get_db()
        article = db.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
        if article is None:
            abort(404)
        if request.method == "POST":
            data, erreur = _lire_formulaire_article()
            if not erreur:
                data["id"] = article_id
                try:
                    db.execute(
                        """UPDATE articles SET reference=:reference, nom=:nom,
                               categorie_id=:categorie_id, quantite=:quantite,
                               seuil_min=:seuil_min, prix_unitaire=:prix_unitaire,
                               emplacement=:emplacement WHERE id=:id""", data)
                    db.commit()
                    flash("Article mis à jour.", "success")
                    return redirect(url_for("article_detail", article_id=article_id))
                except db.IntegrityError:
                    erreur = "Cette référence existe déjà."
            flash(erreur, "error")
        return render_template(
            "article_form.html", article=article, edition=True,
            categories=db.execute("SELECT * FROM categories ORDER BY nom").fetchall(),
        )

    @app.route("/articles/<int:article_id>")
    def article_detail(article_id):
        db = get_db()
        article = db.execute(
            """SELECT a.*, c.nom AS categorie FROM articles a
               LEFT JOIN categories c ON c.id = a.categorie_id WHERE a.id = ?""",
            (article_id,)).fetchone()
        if article is None:
            abort(404)
        mouvements = db.execute(
            "SELECT * FROM mouvements WHERE article_id = ? ORDER BY date DESC, id DESC",
            (article_id,)).fetchall()
        return render_template("article_detail.html", article=article, mouvements=mouvements)

    @app.route("/articles/<int:article_id>/supprimer", methods=["POST"])
    def article_supprimer(article_id):
        db = get_db()
        db.execute("DELETE FROM articles WHERE id = ?", (article_id,))
        db.commit()
        flash("Article supprimé.", "success")
        return redirect(url_for("articles"))

    # ------------------------------------------------------------------ #
    # Mouvements de stock
    # ------------------------------------------------------------------ #
    @app.route("/mouvements")
    def mouvements():
        type_ = request.args.get("type")
        sql = """SELECT m.*, a.nom, a.reference FROM mouvements m
                 JOIN articles a ON a.id = m.article_id"""
        params = []
        if type_ in ("entree", "sortie"):
            sql += " WHERE m.type = ?"
            params.append(type_)
        sql += " ORDER BY m.date DESC, m.id DESC LIMIT 200"
        return render_template("mouvements.html",
                               mouvements=get_db().execute(sql, params).fetchall(),
                               type_=type_)

    @app.route("/mouvements/nouveau", methods=["GET", "POST"])
    def mouvement_nouveau():
        db = get_db()
        if request.method == "POST":
            article_id = request.form.get("article_id", type=int)
            type_ = request.form.get("type")
            quantite = request.form.get("quantite", type=int)
            motif = request.form.get("motif", "").strip()
            article = db.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()

            if article is None or type_ not in ("entree", "sortie") or not quantite or quantite <= 0:
                flash("Mouvement invalide.", "error")
            elif type_ == "sortie" and quantite > article["quantite"]:
                flash(f"Stock insuffisant : {article['quantite']} unité(s) disponible(s).", "error")
            else:
                delta = quantite if type_ == "entree" else -quantite
                db.execute(
                    "INSERT INTO mouvements (article_id, type, quantite, motif) VALUES (?, ?, ?, ?)",
                    (article_id, type_, quantite, motif))
                db.execute("UPDATE articles SET quantite = quantite + ? WHERE id = ?",
                           (delta, article_id))
                db.commit()
                flash("Mouvement enregistré.", "success")
                return redirect(request.args.get("next") or url_for("mouvements"))
        return render_template(
            "mouvement_form.html",
            articles=db.execute("SELECT id, reference, nom, quantite FROM articles ORDER BY reference").fetchall(),
            preselection=request.args.get("article", type=int),
            type_defaut=request.args.get("type", "entree"),
        )

    # ------------------------------------------------------------------ #
    # Alertes & export
    # ------------------------------------------------------------------ #
    @app.route("/alertes")
    def alertes():
        rows = get_db().execute(
            """SELECT a.*, c.nom AS categorie FROM articles a
               LEFT JOIN categories c ON c.id = a.categorie_id
               WHERE a.quantite <= a.seuil_min ORDER BY a.quantite - a.seuil_min"""
        ).fetchall()
        return render_template("alertes.html", alertes=rows)

    @app.route("/export.xlsx")
    def export_excel():
        rows = get_db().execute(
            """SELECT a.reference, a.nom, COALESCE(c.nom, ''), a.emplacement,
                      a.quantite, a.seuil_min, a.prix_unitaire,
                      a.quantite * a.prix_unitaire
               FROM articles a LEFT JOIN categories c ON c.id = a.categorie_id
               ORDER BY a.reference"""
        ).fetchall()
        wb = Workbook()
        ws = wb.active
        ws.title = "Inventaire"
        entetes = ["Référence", "Désignation", "Catégorie", "Emplacement",
                   "Quantité", "Seuil min.", "Prix unitaire (€)", "Valeur (€)"]
        ws.append(entetes)
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F4E79")
        alerte = PatternFill("solid", fgColor="FDE2E1")
        for r in rows:
            ws.append(list(r))
            if r[4] <= r[5]:
                for cell in ws[ws.max_row]:
                    cell.fill = alerte
        for col, largeur in zip("ABCDEFGH", (14, 34, 18, 14, 10, 10, 16, 14)):
            ws.column_dimensions[col].width = largeur
        ws.freeze_panes = "A2"
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        nom = f"inventaire_{datetime.now():%Y-%m-%d}.xlsx"
        return send_file(buf, as_attachment=True, download_name=nom,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    @app.errorhandler(404)
    def page_introuvable(_e):
        return render_template("404.html"), 404

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
