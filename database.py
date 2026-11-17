"""Accès à la base de données SQLite de StockFlow."""

import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    nom  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS articles (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    reference     TEXT NOT NULL UNIQUE,
    nom           TEXT NOT NULL,
    categorie_id  INTEGER REFERENCES categories(id),
    quantite      INTEGER NOT NULL DEFAULT 0 CHECK (quantite >= 0),
    seuil_min     INTEGER NOT NULL DEFAULT 0 CHECK (seuil_min >= 0),
    prix_unitaire REAL    NOT NULL DEFAULT 0 CHECK (prix_unitaire >= 0),
    emplacement   TEXT,
    cree_le       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS mouvements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id  INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    type        TEXT    NOT NULL CHECK (type IN ('entree', 'sortie')),
    quantite    INTEGER NOT NULL CHECK (quantite > 0),
    motif       TEXT,
    date        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_mouvements_article ON mouvements(article_id);
CREATE INDEX IF NOT EXISTS idx_mouvements_date    ON mouvements(date);
"""


def get_db() -> sqlite3.Connection:
    """Retourne la connexion SQLite de la requête en cours."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(path: str) -> None:
    """Crée les tables si elles n'existent pas."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
