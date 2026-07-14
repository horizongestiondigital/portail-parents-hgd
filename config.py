"""
Portail Parents HGD - Configuration cloud
Toutes les valeurs sensibles viennent des variables d'environnement (jamais écrites en dur),
configurées dans le tableau de bord Render.
"""
import os


class Config:
    # Sur Render, on définit DATABASE_URL avec l'URL de connexion Supabase (PostgreSQL).
    # En local (pour tester avant de déployer), on retombe sur SQLite.
    _database_url = os.environ.get("DATABASE_URL", "sqlite:///portail_parents_test.db")
    # Supabase/Render fournissent parfois "postgres://", SQLAlchemy veut "postgresql://"
    if _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.environ.get("PORTAIL_SECRET_KEY", "change-moi-avant-la-mise-en-ligne")

    # Clé secrète que l'app locale doit fournir pour synchroniser des données.
    # Doit être identique à ECOLEGEST_SYNC_KEY dans la config de l'app locale.
    SYNC_API_KEY = os.environ.get("SYNC_API_KEY", "change-moi-aussi")
