"""
Portail Parents HGD - Modèles de la base cloud (Supabase / PostgreSQL)

IMPORTANT : cette base ne contient AUCUN mot de passe, AUCUN compte
directeur/comptable/prof. Uniquement les données que les parents ont le
droit de consulter, envoyées par synchronisation depuis l'app locale.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SyncEcole(db.Model):
    __tablename__ = "sync_ecoles"

    id = db.Column(db.Integer, primary_key=True)
    ecole_id_local = db.Column(db.Integer, unique=True, nullable=False)  # id dans la base locale
    nom = db.Column(db.String(150), nullable=False)
    logo_url = db.Column(db.String(300))
    derniere_sync = db.Column(db.DateTime, default=datetime.utcnow)


class SyncEleve(db.Model):
    """Un élève synchronisé. Le code_acces sert de mot de passe pour le parent."""
    __tablename__ = "sync_eleves"

    id = db.Column(db.Integer, primary_key=True)
    eleve_id_local = db.Column(db.Integer, unique=True, nullable=False)
    ecole_id_local = db.Column(db.Integer, nullable=False)
    nom_complet = db.Column(db.String(200), nullable=False)
    matricule = db.Column(db.String(30))
    classe_nom = db.Column(db.String(50))
    code_acces = db.Column(db.String(20), unique=True, nullable=False)

    notes = db.relationship("SyncNoteMatiere", backref="eleve", cascade="all, delete-orphan")
    resultats = db.relationship("SyncResultatGeneral", backref="eleve", cascade="all, delete-orphan")
    paiements = db.relationship("SyncPaiement", backref="eleve", cascade="all, delete-orphan")
    presences = db.relationship("SyncPresenceMois", backref="eleve", cascade="all, delete-orphan")


class SyncNoteMatiere(db.Model):
    """Moyenne d'une matière pour une période (pas les notes individuelles, juste le résumé)."""
    __tablename__ = "sync_notes_matiere"

    id = db.Column(db.Integer, primary_key=True)
    eleve_id = db.Column(db.Integer, db.ForeignKey("sync_eleves.id"), nullable=False)
    periode_nom = db.Column(db.String(50), nullable=False)
    matiere_nom = db.Column(db.String(100), nullable=False)
    coefficient = db.Column(db.Float)
    moyenne_evaluations = db.Column(db.Float)
    composition = db.Column(db.Float)
    moyenne_matiere = db.Column(db.Float)


class SyncResultatGeneral(db.Model):
    """Moyenne générale + rang d'un élève pour une période."""
    __tablename__ = "sync_resultats_generaux"

    id = db.Column(db.Integer, primary_key=True)
    eleve_id = db.Column(db.Integer, db.ForeignKey("sync_eleves.id"), nullable=False)
    periode_nom = db.Column(db.String(50), nullable=False)
    moyenne_generale = db.Column(db.Float)
    rang = db.Column(db.String(10))


class SyncPaiement(db.Model):
    """Solde par type de frais (pas l'historique détaillé des paiements)."""
    __tablename__ = "sync_paiements"

    id = db.Column(db.Integer, primary_key=True)
    eleve_id = db.Column(db.Integer, db.ForeignKey("sync_eleves.id"), nullable=False)
    type_frais_nom = db.Column(db.String(100), nullable=False)
    montant_attendu = db.Column(db.Float, default=0)
    montant_paye = db.Column(db.Float, default=0)
    reste = db.Column(db.Float, default=0)


class SyncPresenceMois(db.Model):
    """Résumé des présences par mois (pas chaque présence individuelle)."""
    __tablename__ = "sync_presences_mois"

    id = db.Column(db.Integer, primary_key=True)
    eleve_id = db.Column(db.Integer, db.ForeignKey("sync_eleves.id"), nullable=False)
    mois_libelle = db.Column(db.String(30), nullable=False)  # "Octobre 2026"
    nb_absences = db.Column(db.Integer, default=0)
    nb_retards = db.Column(db.Integer, default=0)
    nb_malades = db.Column(db.Integer, default=0)
