from decimal import Decimal, InvalidOperation, getcontext

# ============================================================
# CARNET INTELLIGENT
# CŒUR DU MOTEUR DE CALCUL
# ============================================================

getcontext().prec = 50


# ------------------------------------------------------------
# CONVERSION SÉCURISÉE DES NOMBRES
# ------------------------------------------------------------

def nombre(valeur):
    """
    Transforme une valeur en Decimal.

    Une case vide reste None.
    Elle n'est JAMAIS transformée en zéro.
    """

    if valeur is None:
        return None

    valeur = str(valeur).strip().replace(",", ".")

    if valeur == "":
        return None

    try:
        return Decimal(valeur)
    except InvalidOperation:
        raise ValueError("La valeur entrée n'est pas un nombre valide.")


# ------------------------------------------------------------
# NOTE
# ------------------------------------------------------------

class Note:

    def __init__(self, valeur=None, bareme=20):

        self.valeur = nombre(valeur)
        self.bareme = nombre(bareme)

        if self.bareme is None or self.bareme <= 0:
            raise ValueError("Le barème doit être supérieur à zéro.")

    def est_vide(self):
        return self.valeur is None

    def est_valide(self):

        # Une case vide n'est pas une erreur.
        if self.est_vide():
            return True

        if self.valeur < 0:
            return False

        if self.valeur > self.bareme:
            return False

        return True

    def verifier(self):

        if self.est_vide():
            return

        if self.valeur < 0:
            raise ValueError("Une note négative n'est pas valide.")

        if self.valeur > self.bareme:
            raise ValueError(
                f"Erreur : {self.valeur} dépasse le barème "
                f"de {self.bareme}."
            )

    def sur_20(self):

        self.verifier()

        if self.est_vide():
            return None

        # Équilibrage interne du barème.
        #
        # Exemple :
        # 15/20 -> 15/20
        # 8/10  -> 16/20
        # 30/40 -> 15/20
        # 40/50 -> 16/20
        #
        # Le résultat original n'est pas modifié.
        return (
            self.valeur * Decimal("20")
        ) / self.bareme


# ------------------------------------------------------------
# MATIÈRE
# ------------------------------------------------------------

class Matiere:

    def __init__(self, nom, coefficient=1):

        self.nom = str(nom)

        self.coefficient = nombre(coefficient)

        if self.coefficient is None:
            self.coefficient = Decimal("1")

        if self.coefficient <= 0:
            raise ValueError(
                "Le coefficient doit être supérieur à zéro."
            )

        self.interrogations = []
        self.devoirs = []

    # --------------------------------------------------------
    # AJOUT
    # --------------------------------------------------------

    def ajouter_interrogation(
        self,
        valeur=None,
        bareme=20
    ):

        note = Note(valeur, bareme)

        # On vérifie immédiatement une note existante.
        note.verifier()

        self.interrogations.append(note)

    def ajouter_devoir(
        self,
        valeur=None,
        bareme=20
    ):

        note = Note(valeur, bareme)

        note.verifier()

        self.devoirs.append(note)

    # --------------------------------------------------------
    # SUPPRESSION
    # --------------------------------------------------------

    def supprimer_interrogation(self, numero):

        if 0 <= numero < len(self.interrogations):
            del self.interrogations[numero]

    def supprimer_devoir(self, numero):

        if 0 <= numero < len(self.devoirs):
            del self.devoirs[numero]

    # --------------------------------------------------------
    # MODIFICATION
    # --------------------------------------------------------

    def modifier_interrogation(
        self,
        numero,
        valeur,
        bareme=None
    ):

        if not 0 <= numero < len(self.interrogations):
            raise IndexError(
                "Cette interrogation n'existe pas."
            )

        ancienne = self.interrogations[numero]

        if bareme is None:
            bareme = ancienne.bareme

        nouvelle = Note(valeur, bareme)
        nouvelle.verifier()

        self.interrogations[numero] = nouvelle

    def modifier_devoir(
        self,
        numero,
        valeur,
        bareme=None
    ):

        if not 0 <= numero < len(self.devoirs):
            raise IndexError(
                "Ce devoir n'existe pas."
            )

        ancienne = self.devoirs[numero]

        if bareme is None:
            bareme = ancienne.bareme

        nouvelle = Note(valeur, bareme)
        nouvelle.verifier()

        self.devoirs[numero] = nouvelle

    # --------------------------------------------------------
    # MOYENNE DES INTERROGATIONS
    # --------------------------------------------------------

    def moyenne_interrogations(self):

        presentes = []

        for note in self.interrogations:

            # Case vide = on ne compte pas.
            if note.est_vide():
                continue

            note.verifier()

            presentes.append(note.sur_20())

        if len(presentes) == 0:
            return None

        somme = sum(
            presentes,
            Decimal("0")
        )

        return somme / Decimal(len(presentes))

    # --------------------------------------------------------
    # MOYENNE DES DEVOIRS
    # --------------------------------------------------------

    def moyenne_devoirs(self):

        presentes = []

        for note in self.devoirs:

            if note.est_vide():
                continue

            note.verifier()

            presentes.append(note.sur_20())

        if len(presentes) == 0:
            return None

        somme = sum(
            presentes,
            Decimal("0")
        )

        return somme / Decimal(len(presentes))

    # --------------------------------------------------------
    # MOYENNE D'INTÉGRATION
    # --------------------------------------------------------

    def moyenne(self):

        """
        Logique principale :

        1. On calcule d'abord la moyenne des interrogations.
        2. Les devoirs présents deviennent des éléments
           indépendants.
        3. On calcule avec uniquement les données présentes.

        Exemple :

        I1 = 16
        I2 = vide
        I3 = 14
        D1 = 10
        D2 = 14

        Moyenne interrogations :

            (16 + 14) / 2 = 15

        Puis :

            (15 + 10 + 14) / 3

        = 13

        Une case vide n'intervient absolument pas.
        """

        composants = []

        moyenne_interro = (
            self.moyenne_interrogations()
        )

        if moyenne_interro is not None:
            composants.append(moyenne_interro)

        # Chaque devoir présent est ajouté séparément.
        for devoir in self.devoirs:

            if devoir.est_vide():
                continue

            devoir.verifier()

            composants.append(
                devoir.sur_20()
            )

        # Rien n'est disponible.
        if len(composants) == 0:
            return None

        somme = sum(
            composants,
            Decimal("0")
        )

        moyenne = somme / Decimal(
            len(composants)
        )

        return moyenne

    # --------------------------------------------------------
    # POINTS AVEC COEFFICIENT
    # --------------------------------------------------------

    def points(self):

        moyenne = self.moyenne()

        if moyenne is None:
            return None

        return moyenne * self.coefficient


# ------------------------------------------------------------
# SEMESTRE
# ------------------------------------------------------------

class Semestre:

    def __init__(self, nom):

        self.nom = nom

        self.matieres = []

    # --------------------------------------------------------
    # MATIÈRES
    # --------------------------------------------------------

    def ajouter_matiere(
        self,
        nom,
        coefficient=1
    ):

        matiere = Matiere(
            nom,
            coefficient
        )

        self.matieres.append(matiere)

        return matiere

    def supprimer_matiere(self, numero):

        if 0 <= numero < len(self.matieres):

            return self.matieres.pop(numero)

        return None

    # --------------------------------------------------------
    # CALCUL DU SEMESTRE
    # --------------------------------------------------------

    def calculer(self):

        total_points = Decimal("0")
        total_coefficients = Decimal("0")

        resultats = []

        for matiere in self.matieres:

            moyenne = matiere.moyenne()

            # Une matière totalement vide
            # n'entre pas dans le calcul.
            if moyenne is None:
                continue

            points = (
                moyenne *
                matiere.coefficient
            )

            total_points += points

            total_coefficients += (
                matiere.coefficient
            )

            resultats.append({
                "matiere": matiere.nom,
                "moyenne": moyenne,
                "coefficient": str(matiere.coefficient),
                "points": points
            })

        if total_coefficients == 0:

            return {
                "nom": self.nom,
                "moyenne": None,
                "total_points": Decimal("0"),
                "total_coefficients": Decimal("0"),
                "matieres": resultats
            }

        moyenne_generale = (
            total_points /
            total_coefficients
        )

        return {
            "nom": self.nom,
            "moyenne": moyenne_generale,
            "total_points": total_points,
            "total_coefficients": total_coefficients,
            "matieres": resultats
        }


# ------------------------------------------------------------
# ANNÉE SCOLAIRE
# ------------------------------------------------------------

class AnneeScolaire:

    def __init__(self):

        self.premier_semestre = Semestre(
            "Premier semestre"
        )

        self.deuxieme_semestre = Semestre(
            "Deuxième semestre"
        )

    def calculer(self):

        premier = (
            self.premier_semestre.calculer()
        )

        deuxieme = (
            self.deuxieme_semestre.calculer()
        )

        m1 = premier["moyenne"]
        m2 = deuxieme["moyenne"]

        # Aucun semestre.
        if m1 is None and m2 is None:

            annuelle = None

        # Un seul semestre disponible.
        elif m1 is None:

            annuelle = m2

        elif m2 is None:

            annuelle = m1

        # Deux semestres.
        else:

            # Règle actuelle :
            #
            # (S1 × 2 + S2) / 3
            annuelle = (
                m1 * Decimal("2")
                + m2
            ) / Decimal("3")

        return {
            "premier_semestre": premier,
            "deuxieme_semestre": deuxieme,
            "moyenne_annuelle": annuelle
        }


# ------------------------------------------------------------
# AFFICHAGE
# ------------------------------------------------------------

def afficher_nombre(valeur):

    if valeur is None:
        return "—"

    return str(valeur)


def afficher_resultat(resultat):

    print()
    print("=" * 60)
    print("RÉSULTATS")
    print("=" * 60)

    premier = resultat[
        "premier_semestre"
    ]

    deuxieme = resultat[
        "deuxieme_semestre"
    ]

    annuelle = resultat[
        "moyenne_annuelle"
    ]

    print()
    print(
        "Premier semestre :",
        afficher_nombre(
            premier["moyenne"]
        )
    )

    print(
        "Deuxième semestre :",
        afficher_nombre(
            deuxieme["moyenne"]
        )
    )

    print(
        "Moyenne annuelle :",
        afficher_nombre(
            annuelle
        )
    )

    print("=" * 60)


# ------------------------------------------------------------
# TEST MANUEL DU MOTEUR
#
# Cette partie permet simplement de lancer moteur.py
# directement dans Termux.
# ------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 60)
    print("CARNET INTELLIGENT")
    print("MOTEUR DE CALCUL")
    print("=" * 60)

    annee = AnneeScolaire()

    # --------------------------------------------------------
    # PREMIER SEMESTRE
    # --------------------------------------------------------

    maths = (
        annee.premier_semestre
        .ajouter_matiere(
            "Mathématiques",
            4
        )
    )

    # Trois interrogations.
    maths.ajouter_interrogation(
        16,
        20
    )

    maths.ajouter_interrogation(
        14,
        20
    )

    # La troisième reste vide volontairement.
    maths.ajouter_interrogation()

    # Deux devoirs.
    maths.ajouter_devoir(
        10,
        20
    )

    maths.ajouter_devoir(
        14,
        20
    )

    # --------------------------------------------------------
    # PHYSIQUE AVEC BARÈMES DIFFÉRENTS
    # --------------------------------------------------------

    physique = (
        annee.premier_semestre
        .ajouter_matiere(
            "Physique",
            3
        )
    )

    physique.ajouter_interrogation(
        8,
        10
    )

    physique.ajouter_interrogation(
        30,
        40
    )

    physique.ajouter_devoir(
        15,
        20
    )

    # --------------------------------------------------------
    # FRANÇAIS AVEC UN VRAI ZÉRO
    # --------------------------------------------------------

    francais = (
        annee.premier_semestre
        .ajouter_matiere(
            "Français",
            2
        )
    )

    francais.ajouter_interrogation(
        0,
        20
    )

    francais.ajouter_interrogation(
        12,
        20
    )

    francais.ajouter_devoir(
        10,
        20
    )

    # --------------------------------------------------------
    # DEUXIÈME SEMESTRE
    # --------------------------------------------------------

    maths2 = (
        annee.deuxieme_semestre
        .ajouter_matiere(
            "Mathématiques",
            4
        )
    )

    maths2.ajouter_interrogation(
        17,
        20
    )

    maths2.ajouter_devoir(
        15,
        20
    )

    # --------------------------------------------------------
    # CALCUL MANUEL
    # --------------------------------------------------------

    resultat = annee.calculer()

    afficher_resultat(resultat)

    print()
    print("Le moteur est prêt.")
# ============================================================
# PILIER 2
# MÉMOIRE PERMANENTE DU CARNET
# ============================================================

import json
import os


FICHIER_MEMOIRE = "carnet_memoire.json"


# ------------------------------------------------------------
# CONVERSION DES NOTES POUR LA SAUVEGARDE
# ------------------------------------------------------------

def note_vers_dict(note):

    return {
        "valeur": (
            None
            if note.valeur is None
            else str(note.valeur)
        ),
        "bareme": str(note.bareme)
    }


def dict_vers_note(data):

    return Note(
        data.get("valeur"),
        data.get("bareme", "20")
    )


# ------------------------------------------------------------
# SAUVEGARDE D'UNE MATIÈRE
# ------------------------------------------------------------

def matiere_vers_dict(matiere):

    return {
        "nom": matiere.nom,
        "coefficient": str(
            matiere.coefficient
        ),

        "interrogations": [
            note_vers_dict(note)
            for note in matiere.interrogations
        ],

        "devoirs": [
            note_vers_dict(note)
            for note in matiere.devoirs
        ]
    }


def dict_vers_matiere(data):

    matiere = Matiere(
        data["nom"],
        data["coefficient"]
    )

    matiere.interrogations = [
        dict_vers_note(note)
        for note in data.get(
            "interrogations",
            []
        )
    ]

    matiere.devoirs = [
        dict_vers_note(note)
        for note in data.get(
            "devoirs",
            []
        )
    ]

    return matiere


# ------------------------------------------------------------
# SAUVEGARDE D'UN SEMESTRE
# ------------------------------------------------------------

def semestre_vers_dict(semestre):

    return {
        "nom": semestre.nom,

        "matieres": [
            matiere_vers_dict(matiere)
            for matiere in semestre.matieres
        ]
    }


def dict_vers_semestre(data):

    semestre = Semestre(
        data["nom"]
    )

    semestre.matieres = [
        dict_vers_matiere(matiere)
        for matiere in data.get(
            "matieres",
            []
        )
    ]

    return semestre


# ------------------------------------------------------------
# SAUVEGARDE DE L'ANNÉE
# ------------------------------------------------------------

def annee_vers_dict(annee):

    return {
        "premier_semestre":
            semestre_vers_dict(
                annee.premier_semestre
            ),

        "deuxieme_semestre":
            semestre_vers_dict(
                annee.deuxieme_semestre
            )
    }


def dict_vers_annee(data):

    annee = AnneeScolaire()

    annee.premier_semestre = (
        dict_vers_semestre(
            data["premier_semestre"]
        )
    )

    annee.deuxieme_semestre = (
        dict_vers_semestre(
            data["deuxieme_semestre"]
        )
    )

    return annee


# ------------------------------------------------------------
# ENREGISTRER
# ------------------------------------------------------------

def sauvegarder(annee):

    donnees = annee_vers_dict(
        annee
    )

    with open(
        FICHIER_MEMOIRE,
        "w",
        encoding="utf-8"
    ) as fichier:

        json.dump(
            donnees,
            fichier,
            ensure_ascii=False,
            indent=4
        )

    print()
    print("✓ Carnet sauvegardé.")


# ------------------------------------------------------------
# CHARGER
# ------------------------------------------------------------

def charger():

    if not os.path.exists(
        FICHIER_MEMOIRE
    ):

        print()
        print(
            "Aucune mémoire trouvée."
        )

        return AnneeScolaire()

    try:

        with open(
            FICHIER_MEMOIRE,
            "r",
            encoding="utf-8"
        ) as fichier:

            donnees = json.load(
                fichier
            )

        annee = dict_vers_annee(
            donnees
        )

        print()
        print(
            "✓ Carnet chargé depuis la mémoire."
        )

        return annee

    except Exception as erreur:

        print()
        print(
            "⚠ Impossible de charger "
            "la mémoire."
        )

        print(
            "Erreur :",
            erreur
        )

        print(
            "Un nouveau carnet sera créé."
        )

        return AnneeScolaire()


# ------------------------------------------------------------
# VÉRIFICATION RAPIDE DE LA MÉMOIRE
# ------------------------------------------------------------

def afficher_memoire():

    if not os.path.exists(
        FICHIER_MEMOIRE
    ):

        print()
        print(
            "La mémoire n'existe pas encore."
        )

        return

    print()
    print("=" * 60)
    print("CONTENU DE LA MÉMOIRE")
    print("=" * 60)

    with open(
        FICHIER_MEMOIRE,
        "r",
        encoding="utf-8"
    ) as fichier:

        donnees = json.load(
            fichier
        )

    for nom_semestre, semestre in [
        (
            "Premier semestre",
            donnees[
                "premier_semestre"
            ]
        ),
        (
            "Deuxième semestre",
            donnees[
                "deuxieme_semestre"
            ]
        )
    ]:

        print()
        print(nom_semestre)

        for matiere in semestre[
            "matieres"
        ]:

            print(
                "  -",
                matiere["nom"],
                "| coefficient :",
                matiere["coefficient"]
            )

            print(
                "    Interrogations :",
                len(
                    matiere[
                        "interrogations"
                    ]
                )
            )

            print(
                "    Devoirs :",
                len(
                    matiere[
                        "devoirs"
                    ]
                )
            )

    print()
    print("=" * 60)
    # ============================================================
    # PILIER 3
    # GESTIONNAIRE DE SAISIE DES NOTES
    # ============================================================
    
    class GestionSaisie:
    
        @staticmethod
        def lire_note(texte, bareme=20):
            """
            Transforme une saisie utilisateur en Note.
    
            Règles :
            - ""       -> case vide
            - "0"      -> vraie note zéro
            - "14.5"   -> note décimale
            - "14/20"  -> refusée ici : le barème est séparé
            - note > barème -> refus
            """
    
            texte = str(texte).strip()
    
            # CASE VIDE
            if texte == "":
                return Note(None, bareme)
    
            # NOMBRE
            valeur = nombre(texte)
    
            note = Note(
                valeur,
                bareme
            )
    
            # Vérification immédiate
            note.verifier()
    
            return note
    
        @staticmethod
        def remplacer_note(
            liste,
            position,
            texte,
            bareme=None
        ):
            """
            Remplace une note existante.
    
            Le moteur ne garde pas l'ancien résultat :
            la nouvelle note remplacera l'ancienne
            au prochain calcul manuel.
            """
    
            if not 0 <= position < len(liste):
                raise IndexError(
                    "Cette position n'existe pas."
                )
    
            ancienne = liste[position]
    
            if bareme is None:
                bareme = ancienne.bareme
    
            nouvelle = (
                GestionSaisie.lire_note(
                    texte,
                    bareme
                )
            )
    
            liste[position] = nouvelle
    
        @staticmethod
        def verifier_matiere(matiere):
            """
            Vérifie toutes les notes d'une matière.
    
            Une case vide est normale.
            Un zéro est une vraie note.
            Une note invalide bloque la matière.
            """
    
            erreurs = []
    
            groupes = [
                (
                    "interrogation",
                    matiere.interrogations
                ),
                (
                    "devoir",
                    matiere.devoirs
                )
            ]
    
            for nom_groupe, notes in groupes:
    
                for numero, note in enumerate(notes):
    
                    try:
                        note.verifier()
    
                    except ValueError as erreur:
    
                        erreurs.append({
                            "type": nom_groupe,
                            "numero": numero + 1,
                            "erreur": str(erreur)
                        })
    
            return erreurs
    
        @staticmethod
        def verifier_annee(annee):
            """
            Vérifie toutes les matières des deux semestres.
            """
    
            erreurs = []
    
            semestres = [
                annee.premier_semestre,
                annee.deuxieme_semestre
            ]
    
            for semestre in semestres:
    
                for matiere in semestre.matieres:
    
                    erreurs_matiere = (
                        GestionSaisie
                        .verifier_matiere(
                            matiere
                        )
                    )
    
                    for erreur in erreurs_matiere:
    
                        erreur["semestre"] = (
                            semestre.nom
                        )
    
                        erreur["matiere"] = (
                            matiere.nom
                        )
    
                        erreurs.append(
                            erreur
                        )
    
            return erreurs
    
    
    # ============================================================
    # PILIER 3 — TEST DU GESTIONNAIRE DE SAISIE
    # ============================================================
    
    def tester_gestion_saisie():
    
        print()
        print("=" * 60)
        print("GESTIONNAIRE DE SAISIE")
        print("=" * 60)
    
        # CASE VIDE
        vide = GestionSaisie.lire_note(
            "",
            20
        )
    
        print(
            "Case vide :",
            vide.valeur
        )
    
        # VRAI ZÉRO
        zero = GestionSaisie.lire_note(
            "0",
            20
        )
    
        print(
            "Zéro réel :",
            zero.valeur
        )
    
        # NOTE DÉCIMALE
        decimal = GestionSaisie.lire_note(
            "13.66",
            20
        )
    
        print(
            "Note décimale :",
            decimal.valeur
        )
    
        # BARÈME DIFFÉRENT
        note_sur_40 = GestionSaisie.lire_note(
            "30",
            40
        )
    
        print(
            "30/40 équilibré sur 20 :",
            note_sur_40.sur_20()
        )
    
        # NOTE INVALIDE
        try:
    
            GestionSaisie.lire_note(
                "25",
                20
            )
    
        except ValueError as erreur:
    
            print(
                "Note invalide correctement refusée :",
                erreur
            )
    
        print("=" * 60)
    
    
    # ============================================================
    # FIN DU PILIER 3
    # ============================================================
# ============================================================
# PILIER 4
# MOTEUR DE CALCUL DES MATIÈRES
# ============================================================

class MoteurCalcul:

    @staticmethod
    def notes_valides(notes):
        """
        Retourne uniquement les vraies notes.

        None = case vide -> ignorée
        0    = vraie note -> conservée
        """

        return [
            note
            for note in notes
            if note.valeur is not None
        ]

    @staticmethod
    def moyenne_notes(notes):
        """
        Calcule la moyenne des notes présentes.

        Une case vide n'entre pas dans le calcul.
        Un zéro entre réellement dans le calcul.
        """

        presentes = (
            MoteurCalcul
            .notes_valides(notes)
        )

        if len(presentes) == 0:
            return None

        total = 0.0

        for note in presentes:
            total += note.sur_20()

        return total / len(presentes)

    @staticmethod
    def moyenne_interrogations(
        matiere
    ):
        """
        Moyenne de toutes les interrogations
        réellement présentes.
        """

        return MoteurCalcul.moyenne_notes(
            matiere.interrogations
        )

    @staticmethod
    def moyenne_devoirs(
        matiere
    ):
        """
        Moyenne de tous les devoirs
        réellement présents.
        """

        return MoteurCalcul.moyenne_notes(
            matiere.devoirs
        )

    @staticmethod
    def moyenne_matiere(
        matiere
    ):
        """
        Calcule la moyenne générale
        de la matière.

        Logique :

        interrogations présentes
                 +
        devoirs présents

        Chaque groupe est d'abord
        équilibré sur 20.

        Si un seul groupe existe,
        on utilise uniquement ce groupe.

        Si aucun groupe n'existe,
        la matière reste vide.
        """

        moyenne_interro = (
            MoteurCalcul
            .moyenne_interrogations(
                matiere
            )
        )

        moyenne_devoir = (
            MoteurCalcul
            .moyenne_devoirs(
                matiere
            )
        )

        groupes = []

        if moyenne_interro is not None:
            groupes.append(
                moyenne_interro
            )

        if moyenne_devoir is not None:
            groupes.append(
                moyenne_devoir
            )

        # Aucune note
        if len(groupes) == 0:
            return None

        # Un seul groupe
        if len(groupes) == 1:
            return groupes[0]

        # Interrogations + devoirs
        return sum(groupes) / len(groupes)

    @staticmethod
    def resultat_avec_coefficient(
        matiere
    ):
        """
        Applique le coefficient
        après le calcul de la matière.
        """

        moyenne = (
            MoteurCalcul
            .moyenne_matiere(
                matiere
            )
        )

        if moyenne is None:
            return None

        coefficient = float(
            matiere.coefficient
        )

        return moyenne * coefficient


# ============================================================
# CALCUL D'UN SEMESTRE
# ============================================================

class MoteurSemestre:

    @staticmethod
    def calculer(semestre):

        total_points = Decimal("0")
        total_coefficients = Decimal("0")

        resultats = []

        for matiere in semestre.matieres:

            resultat = (
                MoteurCalcul
                .resultat_avec_coefficient(
                    matiere
                )
            )

            # Matière complètement vide
            if resultat is None:
                resultats.append({
                    "matiere": matiere.nom,
                    "moyenne": None,
                    "coefficient":
                        matiere.coefficient,
                    "points": None
                })

                continue

            moyenne = (
                MoteurCalcul
                .moyenne_matiere(
                    matiere
                )
            )

            coefficient = float(
                matiere.coefficient
            )

            total_points += resultat
            total_coefficients += coefficient

            resultats.append({
                "matiere": matiere.nom,
                "moyenne": moyenne,
                "coefficient": coefficient,
                "points": resultat
            })

        # Aucun coefficient exploitable
        if total_coefficients == 0:
            moyenne_generale = None

        else:
            moyenne_generale = (
                total_points
                / total_coefficients
            )

        return {
            "nom": semestre.nom,
            "moyenne": moyenne_generale,
            "total_points": total_points,
            "total_coefficients":
                total_coefficients,
            "matieres": resultats
        }


# ============================================================
# AFFICHAGE DU SEMESTRE
# ============================================================

def afficher_resultat_semestre(
    resultat
):

    print()
    print("=" * 60)
    print(
        "RÉSULTATS :",
        resultat["nom"]
    )
    print("=" * 60)

    for matiere in resultat["matieres"]:

        nom = matiere["matiere"]
        moyenne = matiere["moyenne"]
        coefficient = matiere["coefficient"]

        if moyenne is None:

            print(
                nom,
                "-> -"
            )

        else:

            print(
                nom,
                "->",
                round(moyenne, 6),
                "/20",
                "| Coef.",
                coefficient
            )

    print("-" * 60)

    if resultat["moyenne"] is None:

        print(
            "Moyenne générale : -"
        )

    else:

        print(
            "Moyenne générale :",
            round(
                resultat["moyenne"],
                6
            ),
            "/20"
        )

    print("=" * 60)


# ============================================================
# FIN DU PILIER 4
# ============================================================
# ============================================================
# LANCEMENT DU TEST DU PILIER 4
# ============================================================
# ============================================================
# PILIER 5
# CALCUL DES SEMESTRES ET DE L'ANNÉE
# ============================================================

class MoteurAnnee:

    @staticmethod
    def calculer_semestre(semestre):

        return MoteurSemestre.calculer(
            semestre
        )

    @staticmethod
    def calculer_annee(annee):

        premier = (
            MoteurAnnee.calculer_semestre(
                annee.premier_semestre
            )
        )

        deuxieme = (
            MoteurAnnee.calculer_semestre(
                annee.deuxieme_semestre
            )
        )

        s1 = premier["moyenne"]
        s2 = deuxieme["moyenne"]

        # Aucun semestre exploitable
        if s1 is None and s2 is None:

            moyenne_annuelle = None

        # Seulement le premier semestre
        elif s1 is not None and s2 is None:

            moyenne_annuelle = s1

        # Seulement le deuxième semestre
        elif s1 is None and s2 is not None:

            moyenne_annuelle = s2

        # Les deux semestres existent
        else:

            # Règle :
            # (S1 × 2 + S2) / 3

            moyenne_annuelle = (
                (s1 * 2) + s2
            ) / 3

        return {
            "premier_semestre": premier,
            "deuxieme_semestre": deuxieme,
            "moyenne_annuelle":
                moyenne_annuelle
        }


# ============================================================
# AFFICHAGE DE L'ANNÉE
# ============================================================

def afficher_resultat_annee(
    resultat
):

    print()
    print("=" * 60)
    print("RÉSULTAT ANNUEL")
    print("=" * 60)

    premier = resultat[
        "premier_semestre"
    ]

    deuxieme = resultat[
        "deuxieme_semestre"
    ]

    annuelle = resultat[
        "moyenne_annuelle"
    ]

    if premier["moyenne"] is None:

        print(
            "Premier semestre : -"
        )

    else:

        print(
            "Premier semestre :",
            round(
                premier["moyenne"],
                6
            ),
            "/20"
        )

    if deuxieme["moyenne"] is None:

        print(
            "Deuxième semestre : -"
        )

    else:

        print(
            "Deuxième semestre :",
            round(
                deuxieme["moyenne"],
                6
            ),
            "/20"
        )

    print("-" * 60)

    if annuelle is None:

        print(
            "Moyenne annuelle : -"
        )

    else:

        print(
            "Moyenne annuelle :",
            round(
                annuelle,
                6
            ),
            "/20"
        )

    print("=" * 60)


# ============================================================
# FIN DU PILIER 5
# ============================================================
# ============================================================
# PILIER 6
# GESTION INDÉPENDANTE DES MATIÈRES
# ============================================================

class GestionMatieres:

    @staticmethod
    def ajouter(semestre, nom, coefficient):
        """
        Ajoute une nouvelle matière.
        """

        nom = str(nom).strip()

        if nom == "":
            raise ValueError(
                "Le nom de la matière est obligatoire."
            )

        coefficient = float(coefficient)

        if coefficient <= 0:
            raise ValueError(
                "Le coefficient doit être supérieur à zéro."
            )

        # Empêcher deux matières portant exactement
        # le même nom dans le même semestre.
        for matiere in semestre.matieres:

            if matiere.nom.lower() == nom.lower():

                raise ValueError(
                    "Cette matière existe déjà."
                )

        nouvelle_matiere = Matiere(
            nom,
            coefficient
        )

        semestre.matieres.append(
            nouvelle_matiere
        )

        return nouvelle_matiere

    @staticmethod
    def trouver(semestre, nom):

        nom = str(nom).strip().lower()

        for matiere in semestre.matieres:

            if matiere.nom.lower() == nom:
                return matiere

        return None

    @staticmethod
    def modifier_coefficient(
        semestre,
        nom,
        nouveau_coefficient
    ):
        """
        Modifie uniquement le coefficient
        de la matière demandée.
        """

        matiere = (
            GestionMatieres.trouver(
                semestre,
                nom
            )
        )

        if matiere is None:
            raise ValueError(
                "Matière introuvable."
            )

        nouveau_coefficient = float(
            nouveau_coefficient
        )

        if nouveau_coefficient <= 0:
            raise ValueError(
                "Le coefficient doit être supérieur à zéro."
            )

        matiere.coefficient = (
            nouveau_coefficient
        )

        return matiere

    @staticmethod
    def supprimer(
        semestre,
        nom,
        confirmation=False
    ):
        """
        Suppression sécurisée.

        La matière ne peut pas être supprimée
        accidentellement.
        """

        matiere = (
            GestionMatieres.trouver(
                semestre,
                nom
            )
        )

        if matiere is None:
            raise ValueError(
                "Matière introuvable."
            )

        if confirmation is not True:
            raise PermissionError(
                "Confirmation obligatoire "
                "avant suppression."
            )

        semestre.matieres.remove(
            matiere
        )

        return matiere


# ============================================================
# GESTION DES INTERROGATIONS
# ============================================================

class GestionInterrogations:

    @staticmethod
    def ajouter(
        matiere,
        valeur,
        bareme=20
    ):

        note = GestionSaisie.lire_note(
            valeur,
            bareme
        )

        matiere.interrogations.append(
            note
        )

        return note

    @staticmethod
    def supprimer(
        matiere,
        position
    ):

        if not (
            0 <= position
            < len(matiere.interrogations)
        ):
            raise IndexError(
                "Interrogation inexistante."
            )

        return matiere.interrogations.pop(
            position
        )

    @staticmethod
    def modifier(
        matiere,
        position,
        valeur,
        bareme=None
    ):

        GestionSaisie.remplacer_note(
            matiere.interrogations,
            position,
            valeur,
            bareme
        )


# ============================================================
# GESTION DES DEVOIRS
# ============================================================

class GestionDevoirs:

    @staticmethod
    def ajouter(
        matiere,
        valeur,
        bareme=20
    ):

        note = GestionSaisie.lire_note(
            valeur,
            bareme
        )

        matiere.devoirs.append(
            note
        )

        return note

    @staticmethod
    def supprimer(
        matiere,
        position
    ):

        if not (
            0 <= position
            < len(matiere.devoirs)
        ):
            raise IndexError(
                "Devoir inexistant."
            )

        return matiere.devoirs.pop(
            position
        )

    @staticmethod
    def modifier(
        matiere,
        position,
        valeur,
        bareme=None
    ):

        GestionSaisie.remplacer_note(
            matiere.devoirs,
            position,
            valeur,
            bareme
        )


# ============================================================
# FIN DU PILIER 6
# ============================================================
# ============================================================
# PILIER 7
# GESTION ET ÉQUILIBRAGE DES BARÈMES
# ============================================================

class GestionBaremes:

    BASE_INTERNE = 20.0

    @staticmethod
    def verifier_bareme(bareme):
        """
        Vérifie qu'un barème est utilisable.
        """

        try:
            bareme = float(bareme)
        except (ValueError, TypeError):
            raise ValueError(
                "Le barème doit être un nombre."
            )

        if bareme <= 0:
            raise ValueError(
                "Le barème doit être supérieur à zéro."
            )

        return bareme

    @staticmethod
    def equilibrer(valeur, bareme):
        """
        Équilibre une note vers la base interne /20.

        Exemple :

        15/20 -> 15/20
        8/10  -> 16/20
        30/40 -> 15/20
        75/100 -> 15/20
        """

        bareme = GestionBaremes.verifier_bareme(
            bareme
        )

        valeur = float(valeur)

        if valeur < 0:
            raise ValueError(
                "Une note ne peut pas être négative."
            )

        if valeur > bareme:
            raise ValueError(
                "La note dépasse son barème."
            )

        return (
            valeur
            * GestionBaremes.BASE_INTERNE
            / bareme
        )

    @staticmethod
    def afficher_bareme(note):
        """
        Retourne le barème original de la note.
        """

        return note.bareme

    @staticmethod
    def convertir_note(note):
        """
        Équilibre une note sans modifier
        sa valeur originale.
        """

        if note.valeur is None:
            return None

        return GestionBaremes.equilibrer(
            note.valeur,
            note.bareme
        )


# ============================================================
# ÉQUILIBRAGE D'UN GROUPE DE NOTES
# ============================================================

class EquilibreurNotes:

    @staticmethod
    def equilibrer_groupe(notes):

        notes_valides = [
            note
            for note in notes
            if note.valeur is not None
        ]

        if len(notes_valides) == 0:
            return []

        resultats = []

        for note in notes_valides:

            valeur_equilibree = (
                GestionBaremes
                .convertir_note(note)
            )

            resultats.append(
                valeur_equilibree
            )

        return resultats

    @staticmethod
    def moyenne_equilibree(notes):

        valeurs = (
            EquilibreurNotes
            .equilibrer_groupe(notes)
        )

        if len(valeurs) == 0:
            return None

        return sum(valeurs) / len(valeurs)


# ============================================================
# FIN DU PILIER 7
# ============================================================
# ============================================================
# PILIER 8
# CONFIGURATION SCOLAIRE
# ============================================================

class ConfigurationScolaire:

    NIVEAUX = [
        "Sixième",
        "Cinquième",
        "Quatrième",
        "Troisième",
        "Seconde",
        "Première",
        "Terminale",
        "Université",
        "Personnalisé"
    ]

    # Valeurs de départ.
    # Elles sont MODIFIABLES et ne doivent jamais
    # être considérées comme des règles universelles.
    COEFFICIENTS_DEFAUT = {
        "Sixième": {},
        "Cinquième": {},
        "Quatrième": {},
        "Troisième": {},
        "Seconde": {},
        "Première": {},
        "Terminale": {},
        "Université": {},
        "Personnalisé": {}
    }

    @staticmethod
    def niveaux_disponibles():
        return ConfigurationScolaire.NIVEAUX.copy()

    @staticmethod
    def verifier_niveau(niveau):

        if niveau not in ConfigurationScolaire.NIVEAUX:
            raise ValueError(
                "Niveau scolaire inconnu."
            )

        return True

    @staticmethod
    def definir_coefficient(
        niveau,
        matiere,
        coefficient
    ):
        """
        Définit le coefficient d'une matière
        pour un niveau donné.
        """

        ConfigurationScolaire.verifier_niveau(
            niveau
        )

        try:
            coefficient = float(
                coefficient
            )
        except (ValueError, TypeError):
            raise ValueError(
                "Le coefficient doit être un nombre."
            )

        if coefficient <= 0:
            raise ValueError(
                "Le coefficient doit être supérieur à zéro."
            )

        matiere = str(matiere).strip()

        if matiere == "":
            raise ValueError(
                "Le nom de la matière est obligatoire."
            )

        ConfigurationScolaire.COEFFICIENTS_DEFAUT[
            niveau
        ][matiere] = coefficient

    @staticmethod
    def obtenir_coefficient(
        niveau,
        matiere,
        valeur_personnalisee=None
    ):
        """
        Si l'utilisateur fournit un coefficient,
        celui-ci devient prioritaire.

        Sinon, le moteur cherche celui du niveau.
        """

        ConfigurationScolaire.verifier_niveau(
            niveau
        )

        if valeur_personnalisee is not None:

            coefficient = float(
                valeur_personnalisee
            )

            if coefficient <= 0:
                raise ValueError(
                    "Coefficient invalide."
                )

            return coefficient

        coefficient = (
            ConfigurationScolaire
            .COEFFICIENTS_DEFAUT
            .get(niveau, {})
            .get(matiere)
        )

        return coefficient

    @staticmethod
    def supprimer_coefficient(
        niveau,
        matiere
    ):
        """
        Supprime seulement la configuration
        de cette matière pour ce niveau.
        """

        ConfigurationScolaire.verifier_niveau(
            niveau
        )

        ConfigurationScolaire.COEFFICIENTS_DEFAUT[
            niveau
        ].pop(
            matiere,
            None
        )


# ============================================================
# PARAMÈTRES D'UNE ANNÉE SCOLAIRE
# ============================================================

class ParametresAnnee:

    def __init__(
        self,
        niveau="Sixième"
    ):

        ConfigurationScolaire.verifier_niveau(
            niveau
        )

        self.niveau = niveau

        # Nombre de semestres.
        # Deux par défaut selon notre modèle actuel.
        self.nombre_semestres = 2

        # Poids du premier semestre.
        self.poids_premier_semestre = 2

        # Poids du deuxième semestre.
        self.poids_deuxieme_semestre = 1

    def modifier_niveau(
        self,
        niveau
    ):

        ConfigurationScolaire.verifier_niveau(
            niveau
        )

        self.niveau = niveau

    def modifier_nombre_semestres(
        self,
        nombre
    ):

        nombre = int(nombre)

        if nombre <= 0:
            raise ValueError(
                "Le nombre de semestres doit être supérieur à zéro."
            )

        self.nombre_semestres = nombre

    def modifier_poids_semestres(
        self,
        poids1,
        poids2
    ):

        poids1 = float(poids1)
        poids2 = float(poids2)

        if poids1 < 0 or poids2 < 0:
            raise ValueError(
                "Les poids ne peuvent pas être négatifs."
            )

        if poids1 + poids2 == 0:
            raise ValueError(
                "Au moins un poids doit être supérieur à zéro."
            )

        self.poids_premier_semestre = poids1
        self.poids_deuxieme_semestre = poids2


# ============================================================
# FIN DU PILIER 8
# ============================================================
# ============================================================
# PILIER 9
# COLONNES DYNAMIQUES
# ============================================================

class GestionColonnes:

    # --------------------------------------------------------
    # INTERROGATIONS
    # --------------------------------------------------------

    @staticmethod
    def ajouter_interrogation(
        matiere,
        valeur=None,
        bareme=20
    ):
        """
        Ajoute une nouvelle colonne d'interrogation.

        Une colonne nouvellement créée peut rester vide.
        """

        note = GestionSaisie.lire_note(
            valeur,
            bareme
        )

        matiere.interrogations.append(
            note
        )

        return note

    @staticmethod
    def supprimer_interrogation(
        matiere,
        position
    ):
        """
        Supprime uniquement l'interrogation
        sélectionnée.
        """

        if not (
            0 <= position
            < len(matiere.interrogations)
        ):
            raise IndexError(
                "Cette interrogation n'existe pas."
            )

        return matiere.interrogations.pop(
            position
        )

    @staticmethod
    def nombre_interrogations(
        matiere
    ):

        return len(
            matiere.interrogations
        )

    # --------------------------------------------------------
    # DEVOIRS
    # --------------------------------------------------------

    @staticmethod
    def ajouter_devoir(
        matiere,
        valeur=None,
        bareme=20
    ):
        """
        Ajoute une nouvelle colonne de devoir.
        """

        note = GestionSaisie.lire_note(
            valeur,
            bareme
        )

        matiere.devoirs.append(
            note
        )

        return note

    @staticmethod
    def supprimer_devoir(
        matiere,
        position
    ):
        """
        Supprime uniquement le devoir
        sélectionné.
        """

        if not (
            0 <= position
            < len(matiere.devoirs)
        ):
            raise IndexError(
                "Ce devoir n'existe pas."
            )

        return matiere.devoirs.pop(
            position
        )

    @staticmethod
    def nombre_devoirs(
        matiere
    ):

        return len(
            matiere.devoirs
        )

    # --------------------------------------------------------
    # MODIFICATION D'UNE COLONNE
    # --------------------------------------------------------

    @staticmethod
    def modifier_interrogation(
        matiere,
        position,
        valeur,
        bareme=None
    ):

        GestionSaisie.remplacer_note(
            matiere.interrogations,
            position,
            valeur,
            bareme
        )

    @staticmethod
    def modifier_devoir(
        matiere,
        position,
        valeur,
        bareme=None
    ):

        GestionSaisie.remplacer_note(
            matiere.devoirs,
            position,
            valeur,
            bareme
        )


# ============================================================
# GESTION DE L'ÉTAT DES COLONNES
# ============================================================

class EtatColonnes:

    @staticmethod
    def colonne_vide(note):

        return note.valeur is None

    @staticmethod
    def colonne_remplie(note):

        return note.valeur is not None

    @staticmethod
    def compter_notes_presentes(
        notes
    ):

        compteur = 0

        for note in notes:

            if note.valeur is not None:
                compteur += 1

        return compteur

    @staticmethod
    def compter_cases_vides(
        notes
    ):

        compteur = 0

        for note in notes:

            if note.valeur is None:
                compteur += 1

        return compteur


# ============================================================
# RÉSUMÉ DES COLONNES D'UNE MATIÈRE
# ============================================================

def afficher_etat_colonnes(
    matiere
):

    print()
    print("=" * 60)
    print(
        "ÉTAT DES COLONNES :",
        matiere.nom
    )
    print("=" * 60)

    print()
    print("INTERROGATIONS")

    for numero, note in enumerate(
        matiere.interrogations,
        start=1
    ):

        if note.valeur is None:

            print(
                "I" + str(numero),
                "-> vide"
            )

        else:

            print(
                "I" + str(numero),
                "->",
                note.valeur,
                "/",
                note.bareme
            )

    print()
    print("DEVOIRS")

    for numero, note in enumerate(
        matiere.devoirs,
        start=1
    ):

        if note.valeur is None:

            print(
                "D" + str(numero),
                "-> vide"
            )

        else:

            print(
                "D" + str(numero),
                "->",
                note.valeur,
                "/",
                note.bareme
            )

    print()
    print(
        "Interrogations présentes :",
        EtatColonnes.compter_notes_presentes(
            matiere.interrogations
        )
    )

    print(
        "Interrogations vides :",
        EtatColonnes.compter_cases_vides(
            matiere.interrogations
        )
    )

    print(
        "Devoirs présents :",
        EtatColonnes.compter_notes_presentes(
            matiere.devoirs
        )
    )

    print(
        "Devoirs vides :",
        EtatColonnes.compter_cases_vides(
            matiere.devoirs
        )
    )

    print("=" * 60)


# ============================================================
# FIN DU PILIER 9
# ============================================================
# ============================================================
# PILIER 10
# VALIDATION GÉNÉRALE AVANT CALCUL
# ============================================================

class ValidationMoteur:

    @staticmethod
    def verifier_note(note):

        # Une case vide reste une case vide.
        if note.valeur is None:
            return True

        # Le zéro est une vraie note.
        if note.valeur == 0:
            return True

        if note.valeur < 0:
            return False

        if note.valeur > note.bareme:
            return False

        return True

    @staticmethod
    def verifier_notes(notes):

        erreurs = []

        for position, note in enumerate(
            notes,
            start=1
        ):

            if not ValidationMoteur.verifier_note(
                note
            ):

                erreurs.append(
                    position
                )

        return erreurs

    @staticmethod
    def verifier_matiere(matiere):

        erreurs = []

        erreurs_interrogations = (
            ValidationMoteur.verifier_notes(
                matiere.interrogations
            )
        )

        erreurs_devoirs = (
            ValidationMoteur.verifier_notes(
                matiere.devoirs
            )
        )

        if erreurs_interrogations:
            erreurs.append({
                "type": "interrogation",
                "positions":
                    erreurs_interrogations
            })

        if erreurs_devoirs:
            erreurs.append({
                "type": "devoir",
                "positions":
                    erreurs_devoirs
            })

        if matiere.coefficient <= 0:

            erreurs.append({
                "type": "coefficient",
                "message":
                    "Coefficient invalide."
            })

        return erreurs

    @staticmethod
    def verifier_semestre(semestre):

        erreurs = []

        for matiere in semestre.matieres:

            erreurs_matiere = (
                ValidationMoteur.verifier_matiere(
                    matiere
                )
            )

            if erreurs_matiere:

                erreurs.append({
                    "matiere": matiere.nom,
                    "erreurs":
                        erreurs_matiere
                })

        return erreurs

    @staticmethod
    def verifier_annee(annee):

        erreurs = []

        erreurs_s1 = (
            ValidationMoteur.verifier_semestre(
                annee.premier_semestre
            )
        )

        erreurs_s2 = (
            ValidationMoteur.verifier_semestre(
                annee.deuxieme_semestre
            )
        )

        if erreurs_s1:

            erreurs.append({
                "semestre": 1,
                "erreurs": erreurs_s1
            })

        if erreurs_s2:

            erreurs.append({
                "semestre": 2,
                "erreurs": erreurs_s2
            })

        return erreurs

    @staticmethod
    def peut_calculer(annee):

        erreurs = (
            ValidationMoteur.verifier_annee(
                annee
            )
        )

        return len(erreurs) == 0

    @staticmethod
    def rapport(annee):

        erreurs = (
            ValidationMoteur.verifier_annee(
                annee
            )
        )

        print()
        print("=" * 60)
        print("VALIDATION DU CARNET")
        print("=" * 60)

        if not erreurs:

            print(
                "VALIDATION : OK"
            )

            print(
                "Le moteur peut effectuer le calcul."
            )

        else:

            print(
                "VALIDATION : ERREUR"
            )

            print(
                "Le calcul est bloqué."
            )

            print()
            print(
                "Erreurs détectées :"
            )

            for erreur in erreurs:

                print(
                    erreur
                )

        print("=" * 60)

        return erreurs


# ============================================================
# FIN DU PILIER 10
# ============================================================
# ============================================================
# PILIER 11
# MÉMOIRE DES RÉSULTATS
# ============================================================

class MemoireResultats:

    def __init__(self):
        self.annees = {}

    def enregistrer(
        self,
        annee_nom,
        resultat
    ):
        """
        Enregistre le résultat d'une année.
        """

        if not annee_nom:
            raise ValueError(
                "Le nom de l'année est obligatoire."
            )

        self.annees[str(annee_nom)] = (
            resultat
        )

    def existe(
        self,
        annee_nom
    ):

        return (
            str(annee_nom)
            in self.annees
        )

    def recuperer(
        self,
        annee_nom
    ):

        return self.annees.get(
            str(annee_nom)
        )

    def supprimer(
        self,
        annee_nom
    ):

        self.annees.pop(
            str(annee_nom),
            None
        )

    def liste_annees(self):

        return list(
            self.annees.keys()
        )


# ============================================================
# MÉMOIRE DES MATIÈRES
# ============================================================

class MemoireMatieres:

    def __init__(self):
        self.historique = {}

    def enregistrer(
        self,
        annee,
        matiere,
        moyenne
    ):

        annee = str(annee)
        matiere = str(matiere)

        if annee not in self.historique:
            self.historique[annee] = {}

        self.historique[annee][matiere] = (
            moyenne
        )

    def recuperer(
        self,
        annee,
        matiere
    ):

        return (
            self.historique
            .get(str(annee), {})
            .get(str(matiere))
        )

    def recuperer_annee(
        self,
        annee
    ):

        return self.historique.get(
            str(annee),
            {}
        )


# ============================================================
# COMPARAISON DE DEUX ANNÉES
# ============================================================

class ComparaisonAnnees:

    @staticmethod
    def comparer(
        memoire,
        annee1,
        annee2
    ):

        anciennes = (
            memoire.recuperer_annee(
                annee1
            )
        )

        nouvelles = (
            memoire.recuperer_annee(
                annee2
            )
        )

        matieres = set(
            anciennes.keys()
        ) | set(
            nouvelles.keys()
        )

        resultat = {}

        for matiere in matieres:

            ancienne = anciennes.get(
                matiere
            )

            nouvelle = nouvelles.get(
                matiere
            )

            difference = None

            if (
                ancienne is not None
                and nouvelle is not None
            ):

                difference = (
                    nouvelle - ancienne
                )

            resultat[matiere] = {
                "ancienne": ancienne,
                "nouvelle": nouvelle,
                "difference": difference
            }

        return resultat


# ============================================================
# AFFICHAGE DE LA COMPARAISON
# ============================================================

def afficher_comparaison(
    comparaison
):

    print()
    print("=" * 60)
    print("COMPARAISON DES PERFORMANCES")
    print("=" * 60)

    for matiere, donnees in (
        comparaison.items()
    ):

        ancienne = donnees["ancienne"]
        nouvelle = donnees["nouvelle"]
        difference = donnees["difference"]

        print()
        print(matiere)

        print(
            "Année précédente :",
            ancienne
            if ancienne is not None
            else "-"
        )

        print(
            "Année actuelle :",
            nouvelle
            if nouvelle is not None
            else "-"
        )

        if difference is not None:

            if difference > 0:

                print(
                    "Évolution : +",
                    difference
                )

            elif difference < 0:

                print(
                    "Évolution :",
                    difference
                )

            else:

                print(
                    "Évolution : stable"
                )

    print()
    print("=" * 60)


# ============================================================
# FIN DU PILIER 11
# ============================================================
# ============================================================
# PILIER 12
# CORBEILLE ET RÉCUPÉRATION
# ============================================================

from datetime import datetime, timedelta


class Corbeille:

    DUREE_RECUPERATION_JOURS = 30

    def __init__(self):
        self.elements = []

    def placer(self, matiere):

        element = {
            "matiere": matiere,
            "date_suppression": datetime.now()
        }

        self.elements.append(element)

    def nettoyer(self):

        maintenant = datetime.now()

        nouveaux_elements = []

        for element in self.elements:

            date_suppression = (
                element["date_suppression"]
            )

            limite = (
                date_suppression
                + timedelta(
                    days=self.DUREE_RECUPERATION_JOURS
                )
            )

            if maintenant <= limite:
                nouveaux_elements.append(
                    element
                )

        self.elements = nouveaux_elements

    def afficher(self):

        self.nettoyer()

        print()
        print("=" * 60)
        print("CORBEILLE")
        print("=" * 60)

        if not self.elements:

            print("La corbeille est vide.")

        else:

            for numero, element in enumerate(
                self.elements,
                start=1
            ):

                matiere = element["matiere"]

                print(
                    numero,
                    "-",
                    matiere.nom
                )

                print(
                    "Supprimée le :",
                    element[
                        "date_suppression"
                    ].strftime(
                        "%d/%m/%Y %H:%M"
                    )
                )

        print("=" * 60)

    def recuperer(self, position):

        self.nettoyer()

        if not (
            0 <= position
            < len(self.elements)
        ):
            raise IndexError(
                "Élément introuvable dans la corbeille."
            )

        element = self.elements.pop(
            position
        )

        return element["matiere"]

    def vider(self):

        self.elements.clear()


# ============================================================
# SUPPRESSION SÉCURISÉE AVEC CORBEILLE
# ============================================================

class SuppressionSecurisee:

    @staticmethod
    def supprimer_matiere(
        semestre,
        corbeille,
        nom,
        confirmation=False
    ):

        matiere = (
            GestionMatieres.trouver(
                semestre,
                nom
            )
        )

        if matiere is None:

            raise ValueError(
                "Matière introuvable."
            )

        if confirmation is not True:

            raise PermissionError(
                "Confirmation obligatoire "
                "avant suppression."
            )

        # On retire la matière du semestre.
        semestre.matieres.remove(
            matiere
        )

        # Mais elle n'est pas immédiatement détruite.
        corbeille.placer(
            matiere
        )

        return matiere

    @staticmethod
    def restaurer_matiere(
        semestre,
        corbeille,
        position
    ):

        matiere = corbeille.recuperer(
            position
        )

        # Évite de créer deux matières
        # portant le même nom.
        existante = (
            GestionMatieres.trouver(
                semestre,
                matiere.nom
            )
        )

        if existante is not None:

            raise ValueError(
                "Cette matière existe déjà."
            )

        semestre.matieres.append(
            matiere
        )

        return matiere


# ============================================================
# FIN DU PILIER 12
# ============================================================
# ============================================================
# PILIER 13
# NOTIFICATIONS DISCRÈTES
# ============================================================

class Notification:

    def __init__(
        self,
        titre,
        message,
        niveau="information"
    ):

        self.titre = str(titre)
        self.message = str(message)
        self.niveau = str(niveau)

        self.lue = False
        self.date = datetime.now()


class GestionNotifications:

    def __init__(self):

        self.notifications = []

    def ajouter(
        self,
        titre,
        message,
        niveau="information"
    ):

        notification = Notification(
            titre,
            message,
            niveau
        )

        self.notifications.append(
            notification
        )

        return notification

    def non_lues(self):

        return [
            notification
            for notification
            in self.notifications
            if not notification.lue
        ]

    def nombre_non_lues(self):

        return len(
            self.non_lues()
        )

    def presence_point_rouge(self):

        return (
            self.nombre_non_lues()
            > 0
        )

    def lire(self, position):

        if not (
            0 <= position
            < len(self.notifications)
        ):

            raise IndexError(
                "Notification introuvable."
            )

        self.notifications[
            position
        ].lue = True

        return self.notifications[
            position
        ]

    def supprimer(self, position):

        if not (
            0 <= position
            < len(self.notifications)
        ):

            raise IndexError(
                "Notification introuvable."
            )

        return self.notifications.pop(
            position
        )

    def tout_marquer_comme_lu(self):

        for notification in (
            self.notifications
        ):

            notification.lue = True


# ============================================================
# ALERTES DU CARNET
# ============================================================

class AlertesCarnet:

    @staticmethod
    def signaler_erreur(
        notifications,
        matiere,
        type_erreur
    ):

        notifications.ajouter(
            "Erreur détectée",
            (
                "Une erreur a été détectée "
                "dans la matière "
                + str(matiere)
                + " : "
                + str(type_erreur)
            ),
            "erreur"
        )

    @staticmethod
    def signaler_baisse(
        notifications,
        matiere,
        moyenne
    ):

        notifications.ajouter(
            "Évolution de la moyenne",
            (
                "La moyenne de "
                + str(matiere)
                + " est actuellement de "
                + str(moyenne)
                + "."
            ),
            "attention"
        )


# ============================================================
# AFFICHAGE DES NOTIFICATIONS
# ============================================================

def afficher_notifications(
    notifications
):

    print()
    print("=" * 60)
    print("NOTIFICATIONS")
    print("=" * 60)

    if not notifications:

        print("Aucune notification.")

    else:

        for numero, notification in enumerate(
            notifications,
            start=1
        ):

            etat = (
                "LU"
                if notification.lue
                else "NON LUE"
            )

            print()
            print(
                numero,
                "-",
                notification.titre
            )

            print(
                notification.message
            )

            print(
                "Type :",
                notification.niveau
            )

            print(
                "État :",
                etat
            )

    print("=" * 60)


# ============================================================
# INDICATEUR POUR L'INTERFACE
# ============================================================

def obtenir_indicateur_notification(
    gestion_notifications
):

    if (
        gestion_notifications
        .presence_point_rouge()
    ):

        return "●"

    return ""


# ============================================================
# FIN DU PILIER 13
# ============================================================
# ============================================================
# PILIER 14
# CALCUL MANUEL FINAL
# ============================================================

class CalculManuel:

    @staticmethod
    def calculer_matiere(matiere):
        """
        Calcule uniquement lorsque l'utilisateur
        demande explicitement le calcul.
        """

        erreurs = ValidationMoteur.verifier_matiere(
            matiere
        )

        if erreurs:
            raise ValueError(
                "Calcul impossible : données invalides."
            )

        moyenne_interrogations = (
            EquilibreurNotes.moyenne_equilibree(
                matiere.interrogations
            )
        )

        moyenne_devoirs = (
            EquilibreurNotes.moyenne_equilibree(
                matiere.devoirs
            )
        )

        valeurs = []

        if moyenne_interrogations is not None:
            valeurs.append(
                Decimal(str(moyenne_interrogations))
            )

        if moyenne_devoirs is not None:
            valeurs.append(
                Decimal(str(moyenne_devoirs))
            )

        # Aucune note dans la matière.
        if not valeurs:
            return None

        moyenne = sum(valeurs, Decimal("0")) / Decimal(len(valeurs))

        # Application du coefficient de la matière.
        resultat_coefficiente = (
            moyenne * matiere.coefficient
        )

        return {
            "moyenne": moyenne,
            "coefficient": matiere.coefficient,
            "resultat_coefficiente":
                resultat_coefficiente
        }

    @staticmethod
    def calculer_semestre(semestre):
        """
        Calcule toutes les matières du semestre.
        """

        resultats = []

        total_points = Decimal("0")
        total_coefficients = Decimal("0")

        for matiere in semestre.matieres:

            resultat = (
                CalculManuel.calculer_matiere(
                    matiere
                )
            )

            if resultat is None:
                continue

            resultats.append({
                "matiere": matiere.nom,
                "moyenne":
                    resultat["moyenne"],
                "coefficient":
                    resultat["coefficient"],
                "resultat_coefficiente":
                    resultat[
                        "resultat_coefficiente"
                    ]
            })

            total_points += (
                resultat[
                    "resultat_coefficiente"
                ]
            )

            total_coefficients += (
                resultat["coefficient"]
            )

        if total_coefficients == 0:
            moyenne_generale = None
        else:
            moyenne_generale = (
                total_points
                / total_coefficients
            )

        return {
            "matieres": resultats,
            "total_points": total_points,
            "total_coefficients":
                total_coefficients,
            "moyenne":
                moyenne_generale
        }

    @staticmethod
    def calculer_annee(annee):
        """
        Calcul complet de l'année.

        Cette fonction ne doit être appelée
        que lorsque l'utilisateur appuie
        sur le bouton Calculer.
        """

        erreurs = (
            ValidationMoteur.verifier_annee(
                annee
            )
        )

        if erreurs:
            raise ValueError(
                "Calcul impossible : "
                "des erreurs existent dans le carnet."
            )

        premier = (
            CalculManuel.calculer_semestre(
                annee.premier_semestre
            )
        )

        deuxieme = (
            CalculManuel.calculer_semestre(
                annee.deuxieme_semestre
            )
        )

        s1 = premier["moyenne"]
        s2 = deuxieme["moyenne"]

        if s1 is None and s2 is None:

            annuelle = None

        elif s1 is not None and s2 is None:

            annuelle = s1

        elif s1 is None and s2 is not None:

            annuelle = s2

        else:

            # Règle actuelle :
            # (S1 × 2 + S2) / 3

            annuelle = (
                (s1 * 2) + s2
            ) / 3

        return {
            "premier_semestre": premier,
            "deuxieme_semestre": deuxieme,
            "moyenne_annuelle": annuelle
        }


# ============================================================
# BOUTON CALCULER
# ============================================================

class BoutonCalculer:

    @staticmethod
    def executer(annee):
        """
        Point d'entrée officiel du calcul.

        Rien n'est calculé automatiquement pendant
        la saisie. Le calcul commence ici.
        """

        return CalculManuel.calculer_annee(
            annee
        )


# ============================================================
# FIN DU PILIER 14
# ============================================================
# ============================================================
# PILIER 15
# AFFICHAGE DES RÉSULTATS ET PRÉCISION
# ============================================================

class AffichageResultats:

    @staticmethod
    def valeur_reelle(valeur):
        """
        Retourne la valeur complète conservée
        par le moteur.
        """

        if valeur is None:
            return None

        return float(valeur)

    @staticmethod
    def afficher_decimal(
        valeur,
        decimales=2
    ):
        """
        Formate uniquement l'affichage.
        La valeur interne n'est jamais modifiée.
        """

        if valeur is None:
            return "-"

        return f"{float(valeur):.{decimales}f}"

    @staticmethod
    def afficher_avec_suite(
        valeur,
        decimales=2
    ):
        """
        Affichage indicatif d'une valeur qui
        possède davantage de décimales.

        Exemple :
        13.666666... -> 13.67...
        """

        if valeur is None:
            return "-"

        valeur = float(valeur)

        texte = f"{valeur:.{decimales}f}"

        return texte + "..."


# ============================================================
# MÉTHODES DE PRÉCISION
# ============================================================

class PrecisionCalcul:

    COMPLET = "complet"
    DEUX_DECIMALES = "deux_decimales"
    ARRONDI = "arrondi"

    METHODES = [
        COMPLET,
        DEUX_DECIMALES,
        ARRONDI
    ]

    @staticmethod
    def verifier_methode(
        methode
    ):

        if methode not in (
            PrecisionCalcul.METHODES
        ):

            raise ValueError(
                "Méthode de précision inconnue."
            )

        return True

    @staticmethod
    def afficher(
        valeur,
        methode
    ):

        PrecisionCalcul.verifier_methode(
            methode
        )

        if valeur is None:
            return "-"

        valeur = float(valeur)

        if methode == (
            PrecisionCalcul.COMPLET
        ):

            return str(valeur)

        if methode == (
            PrecisionCalcul.DEUX_DECIMALES
        ):

            return (
                f"{valeur:.2f}"
            )

        if methode == (
            PrecisionCalcul.ARRONDI
        ):

            return str(
                round(valeur)
            )


# ============================================================
# RÉSULTAT COMPLET DU CARNET
# ============================================================

def afficher_resultat_complet(
    resultat,
    methode=PrecisionCalcul.DEUX_DECIMALES
):

    print()
    print("=" * 60)
    print("RÉSULTATS DU CARNET")
    print("=" * 60)

    premier = resultat[
        "premier_semestre"
    ]

    deuxieme = resultat[
        "deuxieme_semestre"
    ]

    annuelle = resultat[
        "moyenne_annuelle"
    ]

    print()
    print("PREMIER SEMESTRE")

    for matiere in premier["matieres"]:

        print(
            matiere["matiere"],
            ":",
            PrecisionCalcul.afficher(
                matiere["moyenne"],
                methode
            ),
            "/20",
            " | Coef.",
            matiere["coefficient"]
        )

    print(
        "Moyenne générale :",
        PrecisionCalcul.afficher(
            premier["moyenne"],
            methode
        ),
        "/20"
    )

    print()
    print("DEUXIÈME SEMESTRE")

    for matiere in deuxieme["matieres"]:

        print(
            matiere["matiere"],
            ":",
            PrecisionCalcul.afficher(
                matiere["moyenne"],
                methode
            ),
            "/20",
            " | Coef.",
            matiere["coefficient"]
        )

    print(
        "Moyenne générale :",
        PrecisionCalcul.afficher(
            deuxieme["moyenne"],
            methode
        ),
        "/20"
    )

    print()
    print("MOYENNE ANNUELLE")

    print(
        PrecisionCalcul.afficher(
            annuelle,
            methode
        ),
        "/20"
    )

    print("=" * 60)


# ============================================================
# FIN DU PILIER 15
# ============================================================
# ============================================================
# PILIER 16
# SAUVEGARDE ET CHARGEMENT
# ============================================================

import json
import os


class SauvegardeCarnet:

    VERSION = 1

    def __init__(
        self,
        fichier="carnet_donnees.json"
    ):
        self.fichier = fichier

    # --------------------------------------------------------
    # CONVERSION D'UNE NOTE
    # --------------------------------------------------------

    @staticmethod
    def note_vers_dict(note):

        return {
            "valeur": None if note.valeur is None else str(note.valeur),
            "bareme": str(note.bareme)
        }

    # --------------------------------------------------------
    # CONVERSION D'UNE MATIÈRE
    # --------------------------------------------------------

    @staticmethod
    def matiere_vers_dict(matiere):

        return {
            "nom": matiere.nom,
            "coefficient": str(matiere.coefficient),

            "interrogations": [
                SauvegardeCarnet.note_vers_dict(note)
                for note in matiere.interrogations
            ],

            "devoirs": [
                SauvegardeCarnet.note_vers_dict(note)
                for note in matiere.devoirs
            ]
        }

    # --------------------------------------------------------
    # CONVERSION D'UN SEMESTRE
    # --------------------------------------------------------

    @staticmethod
    def semestre_vers_dict(semestre):

        return {
            "nom": semestre.nom,
            "matieres": [
                SauvegardeCarnet.matiere_vers_dict(
                    matiere
                )
                for matiere in semestre.matieres
            ]
        }

    # --------------------------------------------------------
    # SAUVEGARDE
    # --------------------------------------------------------

    def sauvegarder(self, annee):

        donnees = {
            "version": self.VERSION,

            "premier_semestre":
                SauvegardeCarnet.semestre_vers_dict(
                    annee.premier_semestre
                ),

            "deuxieme_semestre":
                SauvegardeCarnet.semestre_vers_dict(
                    annee.deuxieme_semestre
                )
        }

        dossier = os.path.dirname(
            os.path.abspath(
                self.fichier
            )
        )

        if dossier:
            os.makedirs(
                dossier,
                exist_ok=True
            )

        fichier_temporaire = (
            self.fichier + ".tmp"
        )

        with open(
            fichier_temporaire,
            "w",
            encoding="utf-8"
        ) as fichier:

            json.dump(
                donnees,
                fichier,
                ensure_ascii=False,
                indent=4
            )

        # Le fichier temporaire devient
        # le fichier officiel seulement
        # lorsque l'écriture est terminée.
        os.replace(
            fichier_temporaire,
            self.fichier
        )

        return True

    # --------------------------------------------------------
    # RECONSTRUCTION D'UNE NOTE
    # --------------------------------------------------------

    @staticmethod
    def dict_vers_note(donnees):

        valeur = donnees.get(
            "valeur"
        )

        bareme = donnees.get(
            "bareme",
            20
        )

        return Note(
            valeur,
            bareme
        )

    # --------------------------------------------------------
    # RECONSTRUCTION D'UNE MATIÈRE
    # --------------------------------------------------------

    @staticmethod
    def dict_vers_matiere(
        donnees
    ):

        matiere = Matiere(
            donnees["nom"],
            donnees["coefficient"]
        )

        matiere.interrogations = [
            SauvegardeCarnet.dict_vers_note(note)
            for note in donnees.get(
                "interrogations",
                []
            )
        ]

        matiere.devoirs = [
            SauvegardeCarnet.dict_vers_note(note)
            for note in donnees.get(
                "devoirs",
                []
            )
        ]

        return matiere

    # --------------------------------------------------------
    # RECONSTRUCTION D'UN SEMESTRE
    # --------------------------------------------------------

    @staticmethod
    def dict_vers_semestre(
        donnees,
        nom="Semestre"
    ):

        semestre = Semestre(donnees.get("nom", nom))

        semestre.matieres = [
            SauvegardeCarnet.dict_vers_matiere(
                matiere
            )
            for matiere in donnees.get(
                "matieres",
                []
            )
        ]

        return semestre

    # --------------------------------------------------------
    # CHARGEMENT
    # --------------------------------------------------------

    def charger(self):

        if not os.path.exists(
            self.fichier
        ):
            return None

        with open(
            self.fichier,
            "r",
            encoding="utf-8"
        ) as fichier:

            donnees = json.load(
                fichier
            )

        version = donnees.get(
            "version",
            1
        )

        if version != self.VERSION:

            raise ValueError(
                "Version des données incompatible."
            )

        annee = AnneeScolaire()

        annee.premier_semestre = (
            SauvegardeCarnet.dict_vers_semestre(
                donnees.get(
                    "premier_semestre",
                    {}
                ),
                "Premier semestre"
            )
        )

        annee.deuxieme_semestre = (
            SauvegardeCarnet.dict_vers_semestre(
                donnees.get(
                    "deuxieme_semestre",
                    {}
                ),
                "Deuxième semestre"
            )
        )

        return annee


# ============================================================
# VÉRIFICATION DE LA SAUVEGARDE
# ============================================================

def sauvegarde_existe(
    fichier="carnet_donnees.json"
):

    return os.path.exists(
        fichier
    )


# ============================================================
# FIN DU PILIER 16
# ============================================================
# ============================================================
# PILIER 17
# PERSONNALISATION ET PARAMÈTRES UTILISATEUR
# ============================================================

class ParametresUtilisateur:

    def __init__(self):

        # Niveau scolaire
        self.niveau = "Sixième"

        # Méthode d'affichage des résultats
        self.methode_precision = (
            PrecisionCalcul.DEUX_DECIMALES
        )

        # Colonnes créées par défaut
        self.interrogations_defaut = 3
        self.devoirs_defaut = 2

        # Barème utilisé par défaut
        self.bareme_defaut = 20

        # Nombre de semestres
        self.nombre_semestres = 2

        # Règle actuelle des semestres
        self.poids_semestre_1 = 2
        self.poids_semestre_2 = 1

    # --------------------------------------------------------
    # NIVEAU
    # --------------------------------------------------------

    def definir_niveau(self, niveau):

        ConfigurationScolaire.verifier_niveau(
            niveau
        )

        self.niveau = niveau

    # --------------------------------------------------------
    # PRÉCISION
    # --------------------------------------------------------

    def definir_precision(self, methode):

        PrecisionCalcul.verifier_methode(
            methode
        )

        self.methode_precision = methode

    # --------------------------------------------------------
    # COLONNES PAR DÉFAUT
    # --------------------------------------------------------

    def definir_nombre_interrogations(
        self,
        nombre
    ):

        nombre = int(nombre)

        if nombre < 0:
            raise ValueError(
                "Le nombre d'interrogations "
                "ne peut pas être négatif."
            )

        self.interrogations_defaut = nombre

    def definir_nombre_devoirs(
        self,
        nombre
    ):

        nombre = int(nombre)

        if nombre < 0:
            raise ValueError(
                "Le nombre de devoirs "
                "ne peut pas être négatif."
            )

        self.devoirs_defaut = nombre

    # --------------------------------------------------------
    # BARÈME PAR DÉFAUT
    # --------------------------------------------------------

    def definir_bareme_defaut(
        self,
        bareme
    ):

        bareme = float(bareme)

        if bareme <= 0:
            raise ValueError(
                "Le barème doit être supérieur à zéro."
            )

        self.bareme_defaut = bareme

    # --------------------------------------------------------
    # SEMESTRES
    # --------------------------------------------------------

    def definir_semestres(
        self,
        nombre
    ):

        nombre = int(nombre)

        if nombre <= 0:
            raise ValueError(
                "Le nombre de semestres "
                "doit être supérieur à zéro."
            )

        self.nombre_semestres = nombre

    def definir_poids_semestres(
        self,
        poids1,
        poids2
    ):

        poids1 = float(poids1)
        poids2 = float(poids2)

        if poids1 < 0 or poids2 < 0:
            raise ValueError(
                "Les poids ne peuvent pas "
                "être négatifs."
            )

        if poids1 + poids2 == 0:
            raise ValueError(
                "Les deux poids ne peuvent "
                "pas être nuls."
            )

        self.poids_semestre_1 = poids1
        self.poids_semestre_2 = poids2

    # --------------------------------------------------------
    # RÉINITIALISATION
    # --------------------------------------------------------

    def reinitialiser(self):

        self.__init__()

    # --------------------------------------------------------
    # AFFICHAGE DES PARAMÈTRES
    # --------------------------------------------------------

    def afficher(self):

        print()
        print("=" * 60)
        print("PARAMÈTRES DU CARNET")
        print("=" * 60)

        print(
            "Niveau :",
            self.niveau
        )

        print(
            "Précision :",
            self.methode_precision
        )

        print(
            "Interrogations par défaut :",
            self.interrogations_defaut
        )

        print(
            "Devoirs par défaut :",
            self.devoirs_defaut
        )

        print(
            "Barème par défaut :",
            self.bareme_defaut
        )

        print(
            "Nombre de semestres :",
            self.nombre_semestres
        )

        print(
            "Poids semestre 1 :",
            self.poids_semestre_1
        )

        print(
            "Poids semestre 2 :",
            self.poids_semestre_2
        )

        print("=" * 60)


# ============================================================
# FIN DU PILIER 17
# ============================================================
# ============================================================
# PILIER 18
# CONTRÔLEUR GÉNÉRAL DU MOTEUR
# ============================================================

class MoteurCarnet:

    VERSION = "1.0.0"

    def __init__(
        self,
        fichier_sauvegarde="carnet_donnees.json"
    ):

        self.parametres = (
            ParametresUtilisateur()
        )

        self.notifications = (
            GestionNotifications()
        )

        self.sauvegarde = (
            SauvegardeCarnet(
                fichier_sauvegarde
            )
        )

        self.annee = None

        self.dernier_resultat = None

    # --------------------------------------------------------
    # CRÉER UN NOUVEAU CARNET
    # --------------------------------------------------------

    def nouveau_carnet(self):

        self.annee = AnneeScolaire()

        self.dernier_resultat = None

        return self.annee

    # --------------------------------------------------------
    # CHARGER LE CARNET
    # --------------------------------------------------------

    def charger(self):

        donnees = self.sauvegarde.charger()

        if donnees is None:

            self.nouveau_carnet()

            return False

        self.annee = donnees

        self.dernier_resultat = None

        return True

    # --------------------------------------------------------
    # SAUVEGARDER LE CARNET
    # --------------------------------------------------------

    def sauvegarder(self):

        if self.annee is None:

            raise RuntimeError(
                "Aucun carnet à sauvegarder."
            )

        return self.sauvegarde.sauvegarder(
            self.annee
        )

    # --------------------------------------------------------
    # CALCUL MANUEL
    # --------------------------------------------------------

    def calculer(self):

        if self.annee is None:

            raise RuntimeError(
                "Aucun carnet à calculer."
            )

        try:

            resultat = (
                BoutonCalculer.executer(
                    self.annee
                )
            )

        except ValueError as erreur:

            self.notifications.ajouter(
                "Calcul impossible",
                str(erreur),
                "erreur"
            )

            raise

        self.dernier_resultat = resultat

        return resultat

    # --------------------------------------------------------
    # AFFICHER LE DERNIER CALCUL
    # --------------------------------------------------------

    def afficher_resultat(self):

        if self.dernier_resultat is None:

            print(
                "Aucun calcul disponible."
            )

            return

        afficher_resultat_complet(
            self.dernier_resultat,
            self.parametres.methode_precision
        )

    # --------------------------------------------------------
    # NOTIFICATIONS
    # --------------------------------------------------------

    def afficher_notifications(self):

        afficher_notifications(
            self.notifications.notifications
        )

    def indicateur_notification(self):

        return obtenir_indicateur_notification(
            self.notifications
        )

    # --------------------------------------------------------
    # PARAMÈTRES
    # --------------------------------------------------------

    def afficher_parametres(self):

        self.parametres.afficher()

    # --------------------------------------------------------
    # ÉTAT DU MOTEUR
    # --------------------------------------------------------

    def etat(self):

        return {
            "version": self.VERSION,
            "carnet_charge":
                self.annee is not None,
            "resultat_disponible":
                self.dernier_resultat is not None,
            "notifications_non_lues":
                self.notifications.nombre_non_lues(),
            "point_notification":
                self.indicateur_notification()
        }


# ============================================================
# POINT DE DÉMARRAGE DU MOTEUR
# ============================================================

def demarrer_moteur():

    moteur = MoteurCarnet()

    charge = moteur.charger()

    if charge:

        print(
            "Carnet chargé avec succès."
        )

    else:

        print(
            "Nouveau carnet créé."
        )

    print(
        "Moteur du carnet prêt."
    )

    print(
        "Version :",
        moteur.VERSION
    )

    return moteur


# ============================================================
# FIN DES 18 PILIERS
# ============================================================
