"""
Portail Parents HGD - Application cloud
Reçoit les données synchronisées depuis l'app locale (API sécurisée par clé),
et affiche le portail de consultation pour les parents (connexion par code élève).
"""
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

from config import Config
from models import (
    db, SyncEcole, SyncEleve, SyncNoteMatiere, SyncResultatGeneral,
    SyncPaiement, SyncPresenceMois,
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # -----------------------------------------------------------------
    # API DE SYNCHRONISATION (appelée par l'app locale, pas par un humain)
    # -----------------------------------------------------------------
    @app.route("/api/sync", methods=["POST"])
    def api_sync():
        cle_fournie = request.headers.get("Authorization", "").replace("Bearer ", "")
        if cle_fournie != app.config["SYNC_API_KEY"]:
            return jsonify({"erreur": "Clé de synchronisation invalide"}), 401

        donnees = request.get_json(silent=True)
        if not donnees:
            return jsonify({"erreur": "Aucune donnée reçue"}), 400

        ecole_data = donnees.get("ecole", {})
        eleves_data = donnees.get("eleves", [])

        ecole = SyncEcole.query.filter_by(ecole_id_local=ecole_data.get("id_local")).first()
        if not ecole:
            ecole = SyncEcole(ecole_id_local=ecole_data.get("id_local"))
            db.session.add(ecole)
        ecole.nom = ecole_data.get("nom", "")
        ecole.logo_url = ecole_data.get("logo_url")

        nb_eleves_synchronises = 0
        for e in eleves_data:
            eleve = SyncEleve.query.filter_by(eleve_id_local=e["id_local"]).first()
            if not eleve:
                eleve = SyncEleve(eleve_id_local=e["id_local"], code_acces=e["code_acces"])
                db.session.add(eleve)

            eleve.ecole_id_local = ecole_data.get("id_local")
            eleve.nom_complet = e.get("nom_complet", "")
            eleve.matricule = e.get("matricule", "")
            eleve.classe_nom = e.get("classe_nom", "")
            eleve.code_acces = e.get("code_acces", eleve.code_acces)

            # Remplacement complet des sous-données (façon simple et fiable : on efface, on remet)
            SyncNoteMatiere.query.filter_by(eleve_id=eleve.id).delete()
            SyncResultatGeneral.query.filter_by(eleve_id=eleve.id).delete()
            SyncPaiement.query.filter_by(eleve_id=eleve.id).delete()
            SyncPresenceMois.query.filter_by(eleve_id=eleve.id).delete()
            db.session.flush()  # pour s'assurer que eleve.id existe si c'est un nouvel élève

            for n in e.get("notes", []):
                db.session.add(SyncNoteMatiere(
                    eleve_id=eleve.id, periode_nom=n.get("periode"), matiere_nom=n.get("matiere"),
                    coefficient=n.get("coefficient"), moyenne_evaluations=n.get("moyenne_evaluations"),
                    composition=n.get("composition"), moyenne_matiere=n.get("moyenne_matiere"),
                ))

            for r in e.get("resultats", []):
                db.session.add(SyncResultatGeneral(
                    eleve_id=eleve.id, periode_nom=r.get("periode"),
                    moyenne_generale=r.get("moyenne_generale"), rang=str(r.get("rang", "")),
                ))

            for p in e.get("paiements", []):
                db.session.add(SyncPaiement(
                    eleve_id=eleve.id, type_frais_nom=p.get("type_frais"),
                    montant_attendu=p.get("attendu"), montant_paye=p.get("paye"), reste=p.get("reste"),
                ))

            for pr in e.get("presences", []):
                db.session.add(SyncPresenceMois(
                    eleve_id=eleve.id, mois_libelle=pr.get("mois"),
                    nb_absences=pr.get("absences", 0), nb_retards=pr.get("retards", 0),
                    nb_malades=pr.get("malades", 0),
                ))

            nb_eleves_synchronises += 1

        db.session.commit()
        return jsonify({"ok": True, "eleves_synchronises": nb_eleves_synchronises})

    # -----------------------------------------------------------------
    # PORTAIL PARENTS (connexion par code élève)
    # -----------------------------------------------------------------
    def parent_connecte(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not session.get("eleve_sync_id"):
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return wrapped

    @app.route("/", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            code = request.form.get("code", "").strip().upper()
            eleve = SyncEleve.query.filter_by(code_acces=code).first()

            if not eleve:
                flash("Code invalide. Vérifie auprès de l'école.", "danger")
                return render_template("login.html")

            session["eleve_sync_id"] = eleve.id
            return redirect(url_for("portail"))

        return render_template("login.html")

    @app.route("/portail")
    @parent_connecte
    def portail():
        eleve = SyncEleve.query.get(session["eleve_sync_id"])
        if not eleve:
            session.clear()
            return redirect(url_for("login"))

        ecole = SyncEcole.query.filter_by(ecole_id_local=eleve.ecole_id_local).first()

        notes_par_periode = {}
        for n in eleve.notes:
            notes_par_periode.setdefault(n.periode_nom, []).append(n)

        return render_template(
            "portail.html", eleve=eleve, ecole=ecole,
            notes_par_periode=notes_par_periode, resultats=eleve.resultats,
            paiements=eleve.paiements, presences=eleve.presences,
        )

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
