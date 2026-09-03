import os
import sys
import tempfile
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from moteur import MoteurCarnet

class TestMoteur(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.tmp.close()
        self.moteur = MoteurCarnet(self.tmp.name)
        self.moteur.nouveau_carnet()

    def tearDown(self):
        try: os.remove(self.tmp.name)
        except FileNotFoundError: pass

    def test_cases_vides_ignorees_et_zero_conserve(self):
        m = self.moteur.annee.premier_semestre.ajouter_matiere('Maths', 3)
        m.ajouter_interrogation(0, 20)
        m.ajouter_interrogation(None, 20)
        self.assertEqual(m.moyenne_interrogations(), Decimal('0'))

    def test_baremes_equilibres(self):
        m = self.moteur.annee.premier_semestre.ajouter_matiere('Physique', 1)
        m.ajouter_interrogation(8, 10)
        self.assertEqual(m.moyenne_interrogations(), Decimal('16'))

    def test_points_coefficient(self):
        m = self.moteur.annee.premier_semestre.ajouter_matiere('Maths', 3)
        m.ajouter_interrogation(16, 20)
        self.assertEqual(m.points(), Decimal('48'))

    def test_annee_ponderee(self):
        s1 = self.moteur.annee.premier_semestre
        s2 = self.moteur.annee.deuxieme_semestre
        a = s1.ajouter_matiere('Maths', 1)
        b = s2.ajouter_matiere('Maths', 1)
        a.ajouter_interrogation(12, 20)
        b.ajouter_interrogation(15, 20)
        resultat = self.moteur.annee.calculer()
        self.assertEqual(resultat['moyenne_annuelle'], Decimal('13'))

    def test_hors_bareme_refuse_par_moteur(self):
        m = self.moteur.annee.premier_semestre.ajouter_matiere('Maths', 1)
        # The interface can display an out-of-range value; the strict engine rejects it on calculation.
        m.ajouter_interrogation(None, 20)
        m.interrogations[0].valeur = Decimal('21')
        with self.assertRaises(ValueError): self.moteur.calculer()

    def test_sauvegarde_rechargement(self):
        s = self.moteur.annee.premier_semestre
        m = s.ajouter_matiere('Français', 2)
        m.ajouter_interrogation(14, 20)
        self.moteur.sauvegarder()
        autre = MoteurCarnet(self.tmp.name)
        self.assertTrue(autre.charger())
        self.assertEqual(autre.annee.premier_semestre.matieres[0].nom, 'Français')

if __name__ == '__main__': unittest.main()
