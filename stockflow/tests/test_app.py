"""Tests de StockFlow.  Lancer avec :  pytest"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.test_client() as client:
        yield client


def creer_article(client, ref="TST-001", quantite=10, seuil=3):
    return client.post("/articles/nouveau", data={
        "reference": ref, "nom": "Article test", "quantite": quantite,
        "seuil_min": seuil, "prix_unitaire": "12,50", "emplacement": "Z9",
    }, follow_redirects=True)


def test_dashboard_vide(client):
    rep = client.get("/")
    assert rep.status_code == 200
    assert "Tableau de bord" in rep.get_data(as_text=True)


def test_creation_article(client):
    rep = creer_article(client)
    assert "TST-001" in rep.get_data(as_text=True)


def test_reference_unique(client):
    creer_article(client)
    rep = creer_article(client)
    assert "existe déjà" in rep.get_data(as_text=True)


def test_entree_et_sortie(client):
    creer_article(client, quantite=10)
    client.post("/mouvements/nouveau", data={"article_id": 1, "type": "entree", "quantite": 5})
    client.post("/mouvements/nouveau", data={"article_id": 1, "type": "sortie", "quantite": 8})
    page = client.get("/articles/1").get_data(as_text=True)
    assert "<strong>7</strong>" in page


def test_sortie_superieure_au_stock_refusee(client):
    creer_article(client, quantite=2)
    rep = client.post("/mouvements/nouveau",
                      data={"article_id": 1, "type": "sortie", "quantite": 5},
                      follow_redirects=True)
    assert "Stock insuffisant" in rep.get_data(as_text=True)


def test_alerte_seuil(client):
    creer_article(client, quantite=2, seuil=5)
    assert "TST-001" in client.get("/alertes").get_data(as_text=True)


def test_export_excel(client):
    creer_article(client)
    rep = client.get("/export.xlsx")
    assert rep.status_code == 200
    assert rep.data[:2] == b"PK"  # un .xlsx est une archive zip
