# -*- coding: utf-8 -*-
"""
Cahier de notes - interface graphique Flask

Ce fichier ne modifie pas moteur_nc.py.
Il utilise le moteur existant pour les structures et les sauvegardes,
mais l'affichage et les contrôles visuels sont gérés ici.
"""

from flask import Flask, request, jsonify, render_template_string
from decimal import Decimal, InvalidOperation

app = Flask(__name__)

# ============================================================
# CHARGEMENT DU MOTEUR
# ============================================================

try:
    from moteur_nc import (
        MoteurCarnet,
        AnneeScolaire,
        GestionMatieres,
        GestionInterrogations,
        GestionDevoirs,
    )
    MOTEUR_OK = True
    ERREUR_MOTEUR = ""
except Exception as e:
    MOTEUR_OK = False
    ERREUR_MOTEUR = str(e)

moteur = None
nom_eleve = ""
promotion = ""
semestre_actuel = "Premier semestre"

# Configuration demandée.
NB_INTERRO_DEFAUT = 5
NB_DEVOIR_DEFAUT = 2


# ============================================================
# INITIALISATION
# ============================================================

def initialiser():
    global moteur

    if not MOTEUR_OK:
        raise RuntimeError(
            "Impossible de charger moteur_nc.py : " + ERREUR_MOTEUR
        )

    if moteur is None:
        moteur = MoteurCarnet()

        # Le moteur actuel contient une ancienne référence à Annee().
        # La classe réellement disponible dans moteur_nc.py est
        # AnneeScolaire. On initialise donc directement cette structure
        # pour éviter que moteur.annee reste à None.
        try:
            moteur.charger()
        except Exception:
            moteur.annee = None

        if moteur.annee is None:
            moteur.annee = AnneeScolaire()
            moteur.dernier_resultat = None

    # Sécurité supplémentaire : si un appel précédent a laissé l'année
    # vide, on recrée uniquement la structure en mémoire.
    if moteur.annee is None:
        moteur.annee = AnneeScolaire()
        moteur.dernier_resultat = None

    return moteur


def obtenir_semestre():
    initialiser()

    if semestre_actuel == "Deuxième semestre":
        return moteur.annee.deuxieme_semestre

    return moteur.annee.premier_semestre


# ============================================================
# OUTILS NOMBRES
# ============================================================

def decimal_valeur(value, default=None):
    if value is None:
        return default

    if isinstance(value, Decimal):
        return value

    texte = str(value).strip().replace(",", ".")
    if texte == "":
        return default

    try:
        return Decimal(texte)
    except (InvalidOperation, ValueError):
        return default


def afficher_nombre(value):
    if value is None:
        return ""

    try:
        value = Decimal(str(value))
        if value == value.to_integral_value():
            return str(int(value))
        return format(value.normalize(), "f")
    except Exception:
        return str(value)


def valeur_note(note):
    if note is None:
        return None
    return getattr(note, "valeur", None)


def valeur_bareme(note):
    if note is None:
        return Decimal("20")
    return decimal_valeur(getattr(note, "bareme", 20), Decimal("20"))


def note_invalide(note):
    valeur = decimal_valeur(valeur_note(note))
    bareme = valeur_bareme(note)

    if valeur is None:
        return False

    return valeur < 0 or valeur > bareme


def obtenir_note(matiere, type_note, index):
    index = int(index)
    liste = (
        matiere.interrogations
        if type_note == "interrogation"
        else matiere.devoirs
    )

    if index < 0 or index >= len(liste):
        raise ValueError("Case introuvable.")

    return liste[index]


def obtenir_matiere(index):
    semestre = obtenir_semestre()
    index = int(index)

    if index < 0 or index >= len(semestre.matieres):
        raise ValueError("Matière introuvable.")

    return semestre.matieres[index]


# ============================================================
# CALCUL VISUEL SÛR
# ============================================================
#
# Le moteur original refuse une note supérieure au barème.
# L'interface doit cependant pouvoir la signaler en rouge sans
# casser l'affichage. Ces fonctions reproduisent la règle de
# calcul du moteur pour l'affichage, y compris pour une note
# momentanément hors barème.
#

def note_sur_20_interface(note):
    valeur = decimal_valeur(valeur_note(note))
    bareme = valeur_bareme(note)

    if valeur is None or bareme is None or bareme <= 0:
        return None

    return valeur * Decimal("20") / bareme


def moyenne_matiere_interface(matiere):
    composants = []

    for note in getattr(matiere, "interrogations", []):
        if valeur_note(note) is None:
            continue
        valeur = note_sur_20_interface(note)
        if valeur is not None:
            composants.append(valeur)

    if composants:
        moyenne_interro = sum(composants, Decimal("0")) / Decimal(len(composants))
    else:
        moyenne_interro = None

    composants_final = []

    if moyenne_interro is not None:
        composants_final.append(moyenne_interro)

    for note in getattr(matiere, "devoirs", []):
        if valeur_note(note) is None:
            continue
        valeur = note_sur_20_interface(note)
        if valeur is not None:
            composants_final.append(valeur)

    if not composants_final:
        return None

    return sum(composants_final, Decimal("0")) / Decimal(len(composants_final))


def calcul_semestre_interface(semestre):
    total_points = Decimal("0")
    total_coefficients_calcules = Decimal("0")
    resultats = []

    for matiere in semestre.matieres:
        moyenne = moyenne_matiere_interface(matiere)
        coefficient = decimal_valeur(getattr(matiere, "coefficient", 1), Decimal("1"))

        if moyenne is None:
            continue

        points = moyenne * coefficient
        total_points += points
        total_coefficients_calcules += coefficient

        resultats.append({
            "matiere": getattr(matiere, "nom", ""),
            "moyenne": moyenne,
            "coefficient": coefficient,
            "points": points,
        })

    moyenne = None
    if total_coefficients_calcules != 0:
        moyenne = total_points / total_coefficients_calcules

    return {
        "nom": getattr(semestre, "nom", ""),
        "moyenne": moyenne,
        "total_points": total_points,
        "total_coefficients": total_coefficients_calcules,
        "matieres": resultats,
    }


# ============================================================
# ÉTAT DE L'INTERFACE
# ============================================================

def construire_etat():
    semestre = obtenir_semestre()

    matieres = []
    maximum_interrogations = NB_INTERRO_DEFAUT
    maximum_devoirs = NB_DEVOIR_DEFAUT
    nombre_alertes = 0

    for index, matiere in enumerate(semestre.matieres):
        interrogations = []
        devoirs = []
        ligne_alerte = False

        for i, note in enumerate(getattr(matiere, "interrogations", [])):
            invalide = note_invalide(note)
            if invalide:
                ligne_alerte = True

            interrogations.append({
                "index": i,
                "value": afficher_nombre(valeur_note(note)),
                "bareme": afficher_nombre(valeur_bareme(note)),
                "invalid": invalide,
                "empty": valeur_note(note) is None,
            })

        for i, note in enumerate(getattr(matiere, "devoirs", [])):
            invalide = note_invalide(note)
            if invalide:
                ligne_alerte = True

            devoirs.append({
                "index": i,
                "value": afficher_nombre(valeur_note(note)),
                "bareme": afficher_nombre(valeur_bareme(note)),
                "invalid": invalide,
                "empty": valeur_note(note) is None,
            })

        maximum_interrogations = max(maximum_interrogations, len(interrogations))
        maximum_devoirs = max(maximum_devoirs, len(devoirs))

        if ligne_alerte:
            nombre_alertes += 1

        moyenne = moyenne_matiere_interface(matiere)

        matieres.append({
            "index": index,
            "nom": getattr(matiere, "nom", ""),
            "coefficient": afficher_nombre(getattr(matiere, "coefficient", 1)),
            "interrogations": interrogations,
            "devoirs": devoirs,
            "moyenne": afficher_nombre(moyenne),
            "alerte": ligne_alerte,
        })

    resultat = calcul_semestre_interface(semestre)

    # Le total affiché est le total des coefficients configurés
    # dans le tableau, même si une matière n'a pas encore de note.
    total_coefficients_configures = sum(
        (
            decimal_valeur(getattr(m, "coefficient", 1), Decimal("1"))
            for m in semestre.matieres
        ),
        Decimal("0")
    )

    # Une cellule vide est une absence de donnée, jamais un zéro.
    nombre_cases_vides = 0
    for matiere in semestre.matieres:
        for note in list(getattr(matiere, "interrogations", [])) + list(getattr(matiere, "devoirs", [])):
            if valeur_note(note) is None:
                nombre_cases_vides += 1

    return {
        "nom_eleve": nom_eleve,
        "promotion": promotion,
        "semestre": semestre_actuel,
        "matieres": matieres,
        "nombre_matieres": len(matieres),
        "total_coefficients": afficher_nombre(total_coefficients_configures),
        "moyenne": afficher_nombre(resultat["moyenne"]),
        "total_points": afficher_nombre(resultat["total_points"]),
        "maximum_interrogations": maximum_interrogations,
        "maximum_devoirs": maximum_devoirs,
        "nombre_alertes": nombre_alertes,
        "nombre_cases_vides": nombre_cases_vides,
    }


# ============================================================
# PAGE PRINCIPALE
# ============================================================

@app.route("/")
def accueil():
    initialiser()
    return render_template_string(PAGE)


# ============================================================
# ÉTAT / ÉLÈVE / PROMOTION / SEMESTRE
# ============================================================

@app.post("/api/etat")
def api_etat():
    global nom_eleve, promotion, semestre_actuel

    donnees = request.get_json(silent=True) or {}

    if "nom_eleve" in donnees:
        nom_eleve = str(donnees["nom_eleve"]).strip()

    if "promotion" in donnees:
        promotion = str(donnees["promotion"]).strip()

    if donnees.get("semestre") in ("Premier semestre", "Deuxième semestre"):
        semestre_actuel = donnees["semestre"]

    return jsonify(ok=True, data=construire_etat())


# ============================================================
# AJOUT MATIÈRE
# ============================================================

@app.post("/api/matiere")
def ajouter_matiere():
    try:
        donnees = request.get_json() or {}
        nom = str(donnees.get("nom", "")).strip()

        coefficient = decimal_valeur(donnees.get("coefficient", "1"))
        if coefficient is None:
            raise ValueError("Le coefficient doit être un nombre.")
        if coefficient <= 0:
            raise ValueError("Le coefficient doit être supérieur à zéro.")

        if not nom:
            raise ValueError("Le nom de la matière est obligatoire.")

        semestre = obtenir_semestre()
        matiere = GestionMatieres.ajouter(semestre, nom, float(coefficient))

        for _ in range(NB_INTERRO_DEFAUT):
            GestionInterrogations.ajouter(matiere, None, 20)

        for _ in range(NB_DEVOIR_DEFAUT):
            GestionDevoirs.ajouter(matiere, None, 20)

        moteur.sauvegarder()
        return jsonify(ok=True, data=construire_etat())

    except Exception as e:
        return jsonify(ok=False, error=str(e))


# ============================================================
# MODIFICATION NOTE
# ============================================================

@app.post("/api/note")
def modifier_note():
    try:
        donnees = request.get_json() or {}
        index_matiere = int(donnees["matiere"])
        type_note = donnees["type"]
        index_note = int(donnees["index"])
        texte = str(donnees.get("value", "")).strip().replace(",", ".")

        matiere = obtenir_matiere(index_matiere)
        note = obtenir_note(matiere, type_note, index_note)

        if texte == "":
            valeur = None
        else:
            valeur = Decimal(texte)

        if valeur is not None and valeur < 0:
            raise ValueError("Une note négative est impossible.")

        # IMPORTANT : contrairement à l'ancien code de l'interface,
        # une note supérieure au barème est conservée pour permettre
        # l'alerte visuelle rouge. Le moteur_nc.py reste inchangé.
        note.valeur = valeur

        moteur.sauvegarder()

        return jsonify(ok=True, data=construire_etat())

    except InvalidOperation:
        return jsonify(ok=False, error="La note doit être un nombre.")
    except Exception as e:
        return jsonify(ok=False, error=str(e))


# ============================================================
# BARÈME INDIVIDUEL
# ============================================================

@app.post("/api/bareme")
def modifier_bareme():
    try:
        donnees = request.get_json() or {}
        index_matiere = int(donnees["matiere"])
        type_note = donnees["type"]
        index_note = int(donnees["index"])
        bareme = decimal_valeur(donnees.get("bareme"))

        if bareme is None or bareme <= 0:
            raise ValueError("Le barème doit être supérieur à zéro.")

        matiere = obtenir_matiere(index_matiere)
        note = obtenir_note(matiere, type_note, index_note)

        # On conserve la note même si elle devient supérieure au nouveau barème.
        # La cellule sera alors affichée en rouge.
        note.bareme = bareme
        moteur.sauvegarder()

        return jsonify(ok=True, data=construire_etat())

    except Exception as e:
        return jsonify(ok=False, error=str(e))


# ============================================================
# AJOUT COLONNE
# ============================================================

@app.post("/api/ajouter-colonne")
def ajouter_colonne():
    try:
        donnees = request.get_json() or {}
        type_colonne = donnees.get("type")
        semestre = obtenir_semestre()

        for matiere in semestre.matieres:
            if type_colonne == "interrogation":
                GestionInterrogations.ajouter(matiere, None, 20)
            elif type_colonne == "devoir":
                GestionDevoirs.ajouter(matiere, None, 20)
            else:
                raise ValueError("Type de colonne inconnu.")

        moteur.sauvegarder()
        return jsonify(ok=True, data=construire_etat())

    except Exception as e:
        return jsonify(ok=False, error=str(e))


# ============================================================
# SUPPRESSION COLONNE
# ============================================================

@app.post("/api/supprimer-colonne")
def supprimer_colonne():
    try:
        donnees = request.get_json() or {}
        type_colonne = donnees.get("type")
        semestre = obtenir_semestre()

        if type_colonne not in ("interrogation", "devoir"):
            raise ValueError("Type de colonne inconnu.")

        for matiere in semestre.matieres:
            liste = (
                matiere.interrogations
                if type_colonne == "interrogation"
                else matiere.devoirs
            )
            if liste:
                liste.pop()

        moteur.sauvegarder()
        return jsonify(ok=True, data=construire_etat())

    except Exception as e:
        return jsonify(ok=False, error=str(e))


# ============================================================
# SUPPRESSION MATIÈRE
# ============================================================

@app.post("/api/supprimer-matiere")
def supprimer_matiere():
    try:
        donnees = request.get_json() or {}
        index = int(donnees["matiere"])
        semestre = obtenir_semestre()

        if index < 0 or index >= len(semestre.matieres):
            raise ValueError("Matière introuvable.")

        # Suppression par index : on n'a pas besoin de modifier le moteur.
        semestre.matieres.pop(index)
        moteur.sauvegarder()

        return jsonify(ok=True, data=construire_etat())

    except Exception as e:
        return jsonify(ok=False, error=str(e))


# ============================================================
# CALCUL
# ============================================================

@app.post("/api/calculer")
def calculer():
    try:
        # Calcul visuel robuste : une cellule hors barème ne bloque pas
        # l'interface et est signalée en rouge.
        semestre = obtenir_semestre()
        resultat = calcul_semestre_interface(semestre)
        etat = construire_etat()

        return jsonify(
            ok=True,
            data=etat,
            resultat={
                "moyenne": afficher_nombre(resultat["moyenne"]),
                "total_points": afficher_nombre(resultat["total_points"]),
                "total_coefficients": afficher_nombre(resultat["total_coefficients"]),
            },
        )

    except Exception as e:
        return jsonify(ok=False, error=str(e))


# ============================================================
# SAUVEGARDE
# ============================================================

@app.post("/api/sauvegarder")
def sauvegarder():
    try:
        moteur.sauvegarder()
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(ok=False, error=str(e))


# ============================================================
# NOUVEAU CAHIER
# ============================================================

@app.post("/api/nouveau")
def nouveau():
    global nom_eleve, promotion

    try:
        moteur.nouveau_carnet()
        nom_eleve = ""
        promotion = ""
        moteur.sauvegarder()
        return jsonify(ok=True, data=construire_etat())
    except Exception as e:
        return jsonify(ok=False, error=str(e))


# ============================================================
# HTML / CSS / JAVASCRIPT
# ============================================================

PAGE = r"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>Cahier de notes</title>
<style>
:root {
    --blue: #1769df;
    --blue-dark: #0f56bd;
    --blue-light: #eaf2ff;
    --white: #ffffff;
    --text: #172033;
    --muted: #687386;
    --border: #d5dce7;
    --danger: #e53935;
    --danger-light: #ffe7e6;
    --success: #168a45;
    --shadow: 0 4px 14px rgba(0,0,0,.10);
    --cell: 54px;
    --coef: 58px;
    --subject: 170px;
    --mean: 70px;
}

* { box-sizing: border-box; }

html, body {
    margin: 0;
    padding: 0;
    min-height: 100%;
    font-family: Arial, Helvetica, sans-serif;
    color: var(--text);
    background: #edf3fc;
}

body { overflow-x: auto; }

button, input, select { font: inherit; }
button { -webkit-tap-highlight-color: transparent; }

.app-header {
    background: var(--blue);
    color: white;
    padding: 18px 20px 16px;
}

.header-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
}

.title h1 {
    margin: 0;
    font-size: 31px;
    line-height: 1.1;
}

.title p {
    margin: 6px 0 0;
    font-size: 16px;
    opacity: .88;
}

.icon-button {
    width: 48px;
    height: 48px;
    border: 0;
    border-radius: 12px;
    background: white;
    color: #111;
    font-size: 25px;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0,0,0,.08);
}

.student-row {
    display: grid;
    grid-template-columns: minmax(240px, 1fr) 180px 220px;
    gap: 10px;
    margin-top: 16px;
}

.student-row input,
.student-row select {
    width: 100%;
    min-height: 50px;
    border: 1px solid #dfe4eb;
    border-radius: 12px;
    background: white;
    color: #222;
    padding: 10px 14px;
    outline: none;
}

.student-row input:focus,
.student-row select:focus {
    border-color: #8db5f5;
    box-shadow: 0 0 0 3px rgba(23,105,223,.16);
}

.toolbar {
    display: flex;
    align-items: center;
    gap: 9px;
    margin-top: 12px;
    flex-wrap: wrap;
}

.tool-button {
    min-height: 44px;
    border: 0;
    border-radius: 11px;
    padding: 8px 14px;
    background: white;
    color: #172033;
    cursor: pointer;
    font-weight: 700;
}

.tool-button.primary {
    background: #fff;
    color: var(--blue-dark);
}

.tool-button.danger {
    color: var(--danger);
}

.page {
    padding: 16px;
}

.notice {
    display: none;
    margin: 0 0 12px;
    border-radius: 12px;
    padding: 11px 14px;
    font-weight: 700;
    background: var(--danger-light);
    color: #b71c1c;
    border: 1px solid #f0aaa8;
}

.notice.show { display: block; }

.table-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 14px;
    box-shadow: var(--shadow);
    overflow: hidden;
}

.table-scroll {
    overflow-x: auto;
    overflow-y: visible;
    -webkit-overflow-scrolling: touch;
}

.grade-table {
    border-collapse: separate;
    border-spacing: 0;
    width: max-content;
    min-width: 100%;
}

.grade-table th,
.grade-table td {
    border-right: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    padding: 5px;
    text-align: center;
    background: white;
}

.grade-table thead th {
    background: #f7f9fd;
    font-weight: 800;
}

.grade-table thead tr:first-child th {
    height: 40px;
    color: #24314a;
}

.grade-table thead tr:nth-child(2) th {
    height: 38px;
    font-size: 13px;
}

.subject-head { width: var(--subject); min-width: var(--subject); }
.coef-head { width: var(--coef); min-width: var(--coef); }
.mean-head { width: var(--mean); min-width: var(--mean); }

.group-head { letter-spacing: .2px; }

.note-cell {
    width: var(--cell);
    min-width: var(--cell);
    height: var(--cell);
}

.note-input {
    width: 42px;
    height: 42px;
    border: 1px solid #c7d0df;
    border-radius: 7px;
    background: white;
    text-align: center;
    font-weight: 700;
    font-size: 16px;
    outline: none;
    padding: 0;
}

.note-input:focus {
    border-color: var(--blue);
    box-shadow: 0 0 0 3px rgba(23,105,223,.14);
}

.note-input.invalid {
    border: 3px solid var(--danger);
    background: var(--danger-light);
    color: #a50000;
}

.note-cell.invalid-cell {
    background: var(--danger-light);
}

.subject-cell {
    min-width: var(--subject);
    text-align: left !important;
    font-weight: 700;
}

.subject-wrap {
    display: flex;
    align-items: center;
    gap: 7px;
}

.subject-delete {
    border: 0;
    background: transparent;
    color: var(--danger);
    font-size: 17px;
    cursor: pointer;
    padding: 4px;
}

.coef-input {
    width: 42px;
    height: 42px;
    border: 1px solid #c7d0df;
    border-radius: 7px;
    text-align: center;
    font-weight: 800;
}

.mean-cell {
    min-width: var(--mean);
    font-weight: 800;
}

.mean-cell.alert {
    background: var(--danger-light);
    color: #b71c1c;
}

.bareme-mini {
    display: block;
    font-size: 10px;
    color: #177245;
    line-height: 1;
    margin-top: 2px;
}

.column-options {
    display: inline-block;
    margin-left: 3px;
    border: 0;
    background: transparent;
    color: #5d687b;
    cursor: pointer;
    font-size: 15px;
    vertical-align: middle;
}

.summary {
    display: grid;
    grid-template-columns: repeat(3, minmax(150px, 1fr));
    gap: 10px;
    padding: 14px;
    background: #f8faff;
}

.summary-card {
    min-height: 58px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: white;
    padding: 8px 11px;
}

.summary-card small {
    display: block;
    color: var(--muted);
    font-size: 11px;
    font-weight: 700;
}

.summary-card strong {
    display: block;
    margin-top: 3px;
    font-size: 20px;
}

.calculation-area {
    padding: 0 14px 16px;
    background: #f8faff;
}

.calculate-button {
    width: 100%;
    min-height: 52px;
    border: 0;
    border-radius: 11px;
    background: var(--blue);
    color: white;
    font-weight: 900;
    font-size: 17px;
    cursor: pointer;
    box-shadow: 0 3px 8px rgba(23,105,223,.25);
}

.calculate-button:active { transform: translateY(1px); }

.status-message {
    margin-top: 9px;
    min-height: 20px;
    font-size: 13px;
    font-weight: 700;
}

.status-message.error { color: var(--danger); }
.status-message.ok { color: var(--success); }

.empty-hint {
    padding: 26px 16px;
    text-align: center;
    color: var(--muted);
    background: white;
}

.modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 1000;
    display: none;
    align-items: center;
    justify-content: center;
    padding: 18px;
    background: rgba(0,0,0,.45);
}

.modal-backdrop.show { display: flex; }

.modal {
    width: min(420px, 100%);
    max-height: 90vh;
    overflow: auto;
    background: white;
    border-radius: 16px;
    box-shadow: 0 15px 50px rgba(0,0,0,.28);
    padding: 18px;
}

.modal h2 {
    margin: 0 0 7px;
    font-size: 20px;
}

.modal p {
    margin: 0 0 14px;
    color: var(--muted);
    font-size: 13px;
}

.modal-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}

.modal-grid button,
.modal-actions button {
    min-height: 45px;
    border: 1px solid var(--border);
    border-radius: 10px;
    background: white;
    font-weight: 800;
    cursor: pointer;
}

.modal-grid button:hover { border-color: var(--blue); }

.custom-bareme {
    margin-top: 12px;
    display: flex;
    gap: 8px;
}

.custom-bareme input {
    flex: 1;
    min-width: 0;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 10px;
}

.modal-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 14px;
}

.modal-actions .confirm { background: var(--blue); color: white; border-color: var(--blue); }
.modal-actions .cancel { background: #f4f6f9; }
.modal-actions .delete { color: var(--danger); }

.menu-panel {
    position: fixed;
    z-index: 900;
    top: 72px;
    right: 15px;
    width: min(330px, calc(100vw - 30px));
    display: none;
    background: white;
    border-radius: 14px;
    box-shadow: 0 12px 40px rgba(0,0,0,.22);
    border: 1px solid var(--border);
    overflow: hidden;
}

.menu-panel.show { display: block; }

.menu-panel button {
    width: 100%;
    border: 0;
    border-bottom: 1px solid #eef1f5;
    background: white;
    padding: 13px 15px;
    text-align: left;
    font-weight: 700;
    cursor: pointer;
}

.menu-panel button:last-child { border-bottom: 0; }
.menu-panel button:hover { background: #f5f8fd; }
.menu-panel .danger { color: var(--danger); }

@media (max-width: 720px) {
    .app-header { padding: 14px 14px 13px; }
    .title h1 { font-size: 27px; }
    .student-row { grid-template-columns: 1fr 1fr; }
    .student-row input:first-child { grid-column: 1 / -1; }
    .student-row select:last-child { grid-column: 1 / -1; }
    .summary { grid-template-columns: repeat(3, minmax(130px, 1fr)); }
}

@media (max-width: 480px) {
    :root {
        --cell: 52px;
        --subject: 145px;
        --coef: 54px;
        --mean: 64px;
    }

    .page { padding: 9px; }
    .student-row { grid-template-columns: 1fr; }
    .student-row input:first-child,
    .student-row select:last-child { grid-column: auto; }
    .toolbar { display: grid; grid-template-columns: 1fr 1fr 1fr; }
    .toolbar .tool-button:first-child { grid-column: 1 / -1; }
    .summary { grid-template-columns: 1fr 1fr 1fr; gap: 6px; padding: 9px; }
    .summary-card { padding: 7px; }
    .summary-card strong { font-size: 17px; }
}
</style>
</head>
<body>

<header class="app-header">
    <div class="header-top">
        <div class="title">
            <h1>Cahier de notes</h1>
            <p>Carnet scolaire</p>
        </div>
        <button class="icon-button" id="menuButton" title="Options">⋮</button>
    </div>

    <div class="student-row">
        <input id="nomEleve" type="text" placeholder="Nom et prénom de l'élève" autocomplete="name">
        <input id="promotion" type="text" placeholder="Promotion / classe">
        <select id="semestre">
            <option>Premier semestre</option>
            <option>Deuxième semestre</option>
        </select>
    </div>

    <div class="toolbar">
        <button class="tool-button primary" id="addSubject">＋ Matière</button>
        <button class="tool-button" id="helpButton">?</button>
        <button class="tool-button" id="saveButton">💾</button>
    </div>
</header>

<main class="page">
    <div class="notice" id="notice"></div>

    <section class="table-card">
        <div class="table-scroll">
            <table class="grade-table" id="gradeTable">
                <thead id="tableHead"></thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>

        <div class="empty-hint" id="emptyHint" style="display:none">
            Ajoute une matière pour commencer le carnet.
        </div>

        <div class="summary">
            <div class="summary-card">
                <small>Nombre total de matières</small>
                <strong id="totalMatieres">0</strong>
            </div>
            <div class="summary-card">
                <small>Total coefficients</small>
                <strong id="totalCoefficients">0</strong>
            </div>
            <div class="summary-card">
                <small>Moyenne totale</small>
                <strong id="moyenneTotale">—</strong>
            </div>
        </div>

        <div class="calculation-area">
            <button class="calculate-button" id="calculateButton">CALCULER</button>
            <div class="status-message" id="statusMessage"></div>
        </div>
    </section>
</main>

<!-- MENU ⋮ -->
<div class="menu-panel" id="menuPanel">
    <button id="menuAddInterro">＋ Ajouter une interrogation</button>
    <button id="menuAddDevoir">＋ Ajouter un devoir</button>
    <button id="menuDeleteInterro">− Supprimer une interrogation</button>
    <button id="menuDeleteDevoir">− Supprimer un devoir</button>
    <button id="menuNew">Nouveau cahier</button>
</div>

<!-- MODALE BARÈME -->
<div class="modal-backdrop" id="baremeModal">
    <div class="modal">
        <h2>Barème de cette case</h2>
        <p id="baremeInfo">Choisis le barème de cette seule case.</p>
        <div class="modal-grid">
            <button data-bareme="5">/5</button>
            <button data-bareme="10">/10</button>
            <button data-bareme="20">/20</button>
            <button data-bareme="30">/30</button>
            <button data-bareme="40">/40</button>
            <button data-bareme="50">/50</button>
            <button data-bareme="60">/60</button>
            <button data-bareme="100">/100</button>
            <button id="customBaremeButton">Personnalisé</button>
        </div>
        <div class="custom-bareme" id="customBaremeArea" style="display:none">
            <input id="customBaremeInput" type="number" min="0.01" step="any" placeholder="Barème personnalisé">
            <button id="customBaremeConfirm">OK</button>
        </div>
        <div class="modal-actions">
            <button class="cancel" id="baremeCancel">Annuler</button>
            <button class="confirm" id="baremeClose">Fermer</button>
        </div>
    </div>
</div>

<!-- MODALE CONFIRMATION -->
<div class="modal-backdrop" id="confirmModal">
    <div class="modal">
        <h2 id="confirmTitle">Confirmation</h2>
        <p id="confirmText">Confirmer cette action ?</p>
        <div class="modal-actions">
            <button class="cancel" id="confirmNo">Annuler</button>
            <button class="delete" id="confirmYes">Supprimer</button>
        </div>
    </div>
</div>

<!-- MODALE AJOUT MATIÈRE -->
<div class="modal-backdrop" id="subjectModal">
    <div class="modal">
        <h2>Ajouter une matière</h2>
        <p>Chaque nouvelle matière commence avec 5 interrogations et 2 devoirs.</p>
        <input id="subjectName" type="text" placeholder="Nom de la matière" style="width:100%;padding:12px;border:1px solid #d5dce7;border-radius:10px;margin-bottom:9px">
        <input id="subjectCoef" type="number" min="0.01" step="any" value="1" placeholder="Coefficient" style="width:100%;padding:12px;border:1px solid #d5dce7;border-radius:10px">
        <div class="modal-actions">
            <button class="cancel" id="subjectCancel">Annuler</button>
            <button class="confirm" id="subjectConfirm">Ajouter</button>
        </div>
    </div>
</div>

<!-- MODALE AIDE -->
<div class="modal-backdrop" id="helpModal">
    <div class="modal">
        <h2>Comment utiliser le cahier ?</h2>
        <p>
            Une petite case correspond à une note. La case vide reste vide et ne devient jamais 0.
            Une note supérieure à son barème est conservée mais signalée en rouge.
        </p>
        <p>
            Pour modifier le barème d'une seule case, appuie rapidement trois fois sur la case.
            Une fenêtre s'ouvre avec les barèmes disponibles et l'option personnalisé.
        </p>
        <div class="modal-actions">
            <button class="confirm" id="helpClose">Compris</button>
        </div>
    </div>
</div>

<script>
let etat = {
    matieres: [],
    maximum_interrogations: 5,
    maximum_devoirs: 2
};

let celluleBareme = null;
let pendingConfirm = null;
const tripleClicks = new Map();

function $(id) { return document.getElementById(id); }

function afficherMessage(message, erreur=false) {
    const box = $("statusMessage");
    box.textContent = message || "";
    box.className = "status-message" + (message ? (erreur ? " error" : " ok") : "");
}

function afficherNotice() {
    const notice = $("notice");
    const invalides = etat.nombre_alertes || 0;
    const vides = etat.nombre_cases_vides || 0;

    if (invalides > 0) {
        notice.textContent = "⚠ Des notes dépassent leur barème. Les cases concernées sont en rouge. Le calcul reste possible.";
        notice.classList.add("show");
    } else if (vides > 0 && etat.matieres.length > 0) {
        notice.textContent = "Certaines cases sont encore vides. Une case vide n'est pas comptée comme zéro.";
        notice.classList.add("show");
    } else {
        notice.classList.remove("show");
        notice.textContent = "";
    }
}

async function api(url, data={}) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });

    const result = await response.json();
    if (!result.ok) throw new Error(result.error || "Erreur inconnue.");
    return result;
}

function renderHead() {
    const head = $("tableHead");
    const ni = Math.max(5, etat.maximum_interrogations || 5);
    const nd = Math.max(2, etat.maximum_devoirs || 2);

    let row1 = `
        <tr>
            <th rowspan="2" class="subject-head">Matière</th>
            <th rowspan="2" class="coef-head">Coef.</th>
            <th colspan="${ni}" class="group-head">INTERROGATION</th>
            <th colspan="${nd}" class="group-head">DEVOIR</th>
            <th rowspan="2" class="mean-head">Moy.</th>
        </tr>`;

    let row2 = "<tr>";
    for (let i=0; i<ni; i++) {
        row2 += `<th>I${i+1}<button class="column-options" data-type="interrogation" data-index="${i}" title="Options">⋮</button></th>`;
    }
    for (let i=0; i<nd; i++) {
        row2 += `<th>D${i+1}<button class="column-options" data-type="devoir" data-index="${i}" title="Options">⋮</button></th>`;
    }
    row2 += "</tr>";

    head.innerHTML = row1 + row2;

    document.querySelectorAll(".column-options").forEach(button => {
        button.addEventListener("click", (event) => {
            event.stopPropagation();
            ouvrirOptionsColonne(button.dataset.type, Number(button.dataset.index));
        });
    });
}

function noteHTML(matiereIndex, type, index, note) {
    const invalid = note && note.invalid;
    const value = note ? (note.value || "") : "";
    const bareme = note ? (note.bareme || "20") : "20";

    return `
        <td class="note-cell ${invalid ? "invalid-cell" : ""}" data-matiere="${matiereIndex}" data-type="${type}" data-index="${index}" data-bareme="${bareme}">
            <input
                class="note-input ${invalid ? "invalid" : ""}"
                inputmode="decimal"
                type="number"
                step="any"
                min="0"
                value="${escapeHtml(value)}"
                data-matiere="${matiereIndex}"
                data-type="${type}"
                data-index="${index}"
                aria-label="Note ${type} ${index+1}"
            >
            <span class="bareme-mini">/${escapeHtml(bareme)}</span>
        </td>`;
}

function renderBody() {
    const body = $("tableBody");
    const ni = Math.max(5, etat.maximum_interrogations || 5);
    const nd = Math.max(2, etat.maximum_devoirs || 2);

    let html = "";

    etat.matieres.forEach((matiere) => {
        html += `<tr>`;
        html += `
            <td class="subject-cell">
                <div class="subject-wrap">
                    <button class="subject-delete" data-delete-matiere="${matiere.index}" title="Supprimer la matière">🗑</button>
                    <span>${escapeHtml(matiere.nom || "")}</span>
                </div>
            </td>`;

        html += `
            <td>
                <input class="coef-input" type="number" min="0.01" step="any" value="${escapeHtml(matiere.coefficient)}" data-coef="${matiere.index}">
            </td>`;

        for (let i=0; i<ni; i++) {
            html += noteHTML(matiere.index, "interrogation", i, matiere.interrogations[i]);
        }

        for (let i=0; i<nd; i++) {
            html += noteHTML(matiere.index, "devoir", i, matiere.devoirs[i]);
        }

        html += `<td class="mean-cell ${matiere.alerte ? "alert" : ""}">${escapeHtml(matiere.moyenne || "—")}</td>`;
        html += `</tr>`;
    });

    body.innerHTML = html;

    document.querySelectorAll(".note-input").forEach(input => {
        input.addEventListener("change", async () => {
            try {
                await api("/api/note", {
                    matiere: Number(input.dataset.matiere),
                    type: input.dataset.type,
                    index: Number(input.dataset.index),
                    value: input.value
                });
                await charger();
            } catch (e) {
                afficherMessage(e.message, true);
            }
        });

        input.addEventListener("click", (event) => {
            event.stopPropagation();
            gererTripleClic(input);
        });
    });

    document.querySelectorAll(".note-cell").forEach(cell => {
        cell.addEventListener("click", (event) => {
            if (event.target.classList.contains("note-input")) return;
            gererTripleClic(cell);
        });
    });

    document.querySelectorAll("[data-delete-matiere]").forEach(button => {
        button.addEventListener("click", (event) => {
            event.stopPropagation();
            demanderConfirmation(
                "Supprimer la matière ?",
                "Cette action supprimera toute la ligne et ses notes.",
                async () => {
                    await api("/api/supprimer-matiere", { matiere: Number(button.dataset.deleteMatiere) });
                    await charger();
                }
            );
        });
    });

    document.querySelectorAll("[data-coef]").forEach(input => {
        input.addEventListener("change", async () => {
            // Le moteur actuel ne fournit pas de route dédiée au coefficient.
            // On utilise l'objet du moteur directement côté serveur via cette route.
            try {
                await api("/api/coefficient", {
                    matiere: Number(input.dataset.coef),
                    coefficient: input.value
                });
                await charger();
            } catch (e) {
                afficherMessage(e.message, true);
            }
        });
    });
}

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function gererTripleClic(element) {
    const matiere = element.dataset.matiere;
    const type = element.dataset.type;
    const index = element.dataset.index;

    if (matiere === undefined || type === undefined || index === undefined) return;

    const key = `${matiere}-${type}-${index}`;
    const now = Date.now();
    const previous = tripleClicks.get(key) || { count: 0, time: 0 };

    let count = previous.count;
    if (now - previous.time < 650) count += 1;
    else count = 1;

    tripleClicks.set(key, { count, time: now });

    if (count >= 3) {
        tripleClicks.set(key, { count: 0, time: 0 });
        ouvrirBareme(Number(matiere), type, Number(index));
    }
}

function ouvrirBareme(matiere, type, index) {
    celluleBareme = { matiere, type, index };
    const m = etat.matieres.find(x => x.index === matiere);
    const liste = type === "interrogation" ? m?.interrogations : m?.devoirs;
    const note = liste?.find(x => x.index === index);
    $("baremeInfo").textContent = `Cette case utilise actuellement /${note?.bareme || 20}. Choisis un nouveau barème.`;
    $("customBaremeArea").style.display = "none";
    $("customBaremeInput").value = "";
    $("baremeModal").classList.add("show");
}

async function appliquerBareme(valeur) {
    if (!celluleBareme) return;

    try {
        await api("/api/bareme", {
            matiere: celluleBareme.matiere,
            type: celluleBareme.type,
            index: celluleBareme.index,
            bareme: valeur
        });
        fermerModal("baremeModal");
        await charger();
    } catch (e) {
        afficherMessage(e.message, true);
    }
}

function ouvrirOptionsColonne(type, index) {
    const label = type === "interrogation" ? `I${index+1}` : `D${index+1}`;
    demanderConfirmation(
        `${label} : options`,
        `Ajouter ou supprimer une colonne ${type === "interrogation" ? "d'interrogation" : "de devoir"}.`,
        null,
        true,
        type
    );
}

function demanderConfirmation(title, text, action, menuColonne=false, typeColonne=null) {
    $("confirmTitle").textContent = title;
    $("confirmText").textContent = text;
    $("confirmYes").textContent = menuColonne ? "Supprimer" : "Confirmer";
    pendingConfirm = action;

    $("confirmModal").classList.add("show");

    if (menuColonne) {
        $("confirmYes").onclick = async () => {
            fermerModal("confirmModal");
            demanderConfirmation(
                "Supprimer la dernière colonne ?",
                "La colonne sera retirée pour toutes les matières.",
                async () => {
                    await api("/api/supprimer-colonne", { type: typeColonne });
                    await charger();
                }
            );
        };
    } else {
        $("confirmYes").onclick = async () => {
            fermerModal("confirmModal");
            if (pendingConfirm) {
                try {
                    await pendingConfirm();
                } catch (e) {
                    afficherMessage(e.message, true);
                }
            }
        };
    }
}

function fermerModal(id) {
    $(id).classList.remove("show");
}

async function charger() {
    try {
        const result = await api("/api/etat", {});
        etat = result.data;

        $("nomEleve").value = etat.nom_eleve || "";
        $("promotion").value = etat.promotion || "";
        $("semestre").value = etat.semestre || "Premier semestre";

        renderHead();
        renderBody();
        afficherNotice();

        $("totalMatieres").textContent = etat.nombre_matieres || 0;
        $("totalCoefficients").textContent = etat.total_coefficients || 0;
        $("moyenneTotale").textContent = etat.moyenne || "—";

        $("emptyHint").style.display = etat.matieres.length ? "none" : "block";
    } catch (e) {
        afficherMessage(e.message, true);
    }
}

async function ajouterMatiere() {
    const nom = $("subjectName").value.trim();
    const coefficient = $("subjectCoef").value.trim() || "1";

    if (!nom) {
        afficherMessage("Le nom de la matière est obligatoire.", true);
        return;
    }

    try {
        await api("/api/matiere", { nom, coefficient });
        fermerModal("subjectModal");
        $("subjectName").value = "";
        $("subjectCoef").value = "1";
        await charger();
    } catch (e) {
        afficherMessage(e.message, true);
    }
}

$("addSubject").addEventListener("click", () => {
    $("subjectModal").classList.add("show");
    setTimeout(() => $("subjectName").focus(), 50);
});

$("subjectCancel").addEventListener("click", () => fermerModal("subjectModal"));
$("subjectConfirm").addEventListener("click", ajouterMatiere);

$("calculateButton").addEventListener("click", async () => {
    try {
        const result = await api("/api/calculer", {});
        etat = result.data;
        renderHead();
        renderBody();
        afficherNotice();
        $("totalMatieres").textContent = etat.nombre_matieres || 0;
        $("totalCoefficients").textContent = etat.total_coefficients || 0;
        $("moyenneTotale").textContent = etat.moyenne || "—";

        if ((etat.nombre_alertes || 0) > 0) {
            afficherMessage("Calcul effectué. Certaines cases restent en erreur : elles sont en rouge.", true);
        } else {
            afficherMessage("Calcul effectué.", false);
        }
    } catch (e) {
        afficherMessage(e.message, true);
    }
});

$("saveButton").addEventListener("click", async () => {
    try {
        await api("/api/sauvegarder", {});
        afficherMessage("Cahier sauvegardé.", false);
    } catch (e) {
        afficherMessage(e.message, true);
    }
});

$("helpButton").addEventListener("click", () => $("helpModal").classList.add("show"));
$("helpClose").addEventListener("click", () => fermerModal("helpModal"));

$("menuButton").addEventListener("click", (event) => {
    event.stopPropagation();
    $("menuPanel").classList.toggle("show");
});

$("menuAddInterro").addEventListener("click", async () => {
    $("menuPanel").classList.remove("show");
    try {
        await api("/api/ajouter-colonne", { type: "interrogation" });
        await charger();
    } catch (e) { afficherMessage(e.message, true); }
});

$("menuAddDevoir").addEventListener("click", async () => {
    $("menuPanel").classList.remove("show");
    try {
        await api("/api/ajouter-colonne", { type: "devoir" });
        await charger();
    } catch (e) { afficherMessage(e.message, true); }
});

$("menuDeleteInterro").addEventListener("click", () => {
    $("menuPanel").classList.remove("show");
    demanderConfirmation(
        "Supprimer une interrogation ?",
        "La dernière colonne d'interrogation sera supprimée pour toutes les matières.",
        async () => {
            await api("/api/supprimer-colonne", { type: "interrogation" });
            await charger();
        }
    );
});

$("menuDeleteDevoir").addEventListener("click", () => {
    $("menuPanel").classList.remove("show");
    demanderConfirmation(
        "Supprimer un devoir ?",
        "La dernière colonne de devoir sera supprimée pour toutes les matières.",
        async () => {
            await api("/api/supprimer-colonne", { type: "devoir" });
            await charger();
        }
    );
});

$("menuNew").addEventListener("click", () => {
    $("menuPanel").classList.remove("show");
    demanderConfirmation(
        "Créer un nouveau cahier ?",
        "Les données du cahier actuellement chargé seront remplacées.",
        async () => {
            await api("/api/nouveau", {});
            await charger();
        }
    );
});

$("confirmNo").addEventListener("click", () => {
    pendingConfirm = null;
    fermerModal("confirmModal");
});

$("baremeCancel").addEventListener("click", () => fermerModal("baremeModal"));
$("baremeClose").addEventListener("click", () => fermerModal("baremeModal"));

$("customBaremeButton").addEventListener("click", () => {
    $("customBaremeArea").style.display = "flex";
    $("customBaremeInput").focus();
});

$("customBaremeConfirm").addEventListener("click", () => {
    const value = $("customBaremeInput").value.trim();
    if (!value || Number(value) <= 0) {
        afficherMessage("Le barème personnalisé doit être supérieur à zéro.", true);
        return;
    }
    appliquerBareme(value);
});

document.querySelectorAll("[data-bareme]").forEach(button => {
    button.addEventListener("click", () => appliquerBareme(button.dataset.bareme));
});

$("nomEleve").addEventListener("change", async function() {
    try {
        await api("/api/etat", { nom_eleve: this.value });
    } catch (e) { afficherMessage(e.message, true); }
});

$("promotion").addEventListener("change", async function() {
    try {
        await api("/api/etat", { promotion: this.value });
    } catch (e) { afficherMessage(e.message, true); }
});

$("semestre").addEventListener("change", async function() {
    try {
        await api("/api/etat", { semestre: this.value });
        await charger();
    } catch (e) { afficherMessage(e.message, true); }
});

document.addEventListener("click", (event) => {
    if (!event.target.closest("#menuPanel") && !event.target.closest("#menuButton")) {
        $("menuPanel").classList.remove("show");
    }
});

window.addEventListener("beforeunload", () => {});

charger();
</script>
</body>
</html>
"""


# ============================================================
# COEFFICIENT
# ============================================================

@app.post("/api/coefficient")
def modifier_coefficient():
    try:
        donnees = request.get_json() or {}
        index = int(donnees["matiere"])
        coefficient = decimal_valeur(donnees.get("coefficient"))

        if coefficient is None or coefficient <= 0:
            raise ValueError("Le coefficient doit être supérieur à zéro.")

        matiere = obtenir_matiere(index)
        matiere.coefficient = coefficient
        moteur.sauvegarder()

        return jsonify(ok=True, data=construire_etat())
    except Exception as e:
        return jsonify(ok=False, error=str(e))


# ============================================================
# DÉMARRAGE
# ============================================================

if __name__ == "__main__":
    print("================================")
    print(" CAHIER DE NOTES")
    print(" Interface graphique")
    print("================================")

    if not MOTEUR_OK:
        print("ERREUR moteur_nc.py :", ERREUR_MOTEUR)
    else:
        print("Ouvre ton navigateur et va sur :")
        print("http://127.0.0.1:5000")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
