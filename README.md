# Canet de notre — APK Android

Projet Android léger construit autour du `moteur.py` existant. Le moteur de calcul est embarqué dans l'application : l'APK n'a pas besoin de lancer Termux pour fonctionner.

## Ce qui est dans ce ZIP

- `main.py` — interface Kivy Android et liaison avec le moteur.
- `moteur.py` — moteur fourni, conservé comme cœur du calcul.
- `buildozer.spec` — configuration de compilation APK.
- `.github/workflows/build.yml` — compilation automatique de l'APK par GitHub Actions.
- `SPECIFICATION.md` — règles fonctionnelles décidées pour l'application.
- `tests/test_moteur.py` — tests de sécurité du moteur.
- `assets/icon.png` — icône sélectionnée à partir de la référence fournie.
- `reference/` — ancienne interface et images de référence, conservées comme documentation et non comme dépendances de l'APK.

## Compilation avec GitHub

1. Créer un dépôt GitHub vide.
2. Décompresser ce ZIP.
3. Envoyer le contenu du dossier à la racine du dépôt.
4. Aller dans **Actions** → **Build Canet de notre APK**.
5. Lancer le workflow ou pousser un commit.
6. Une fois terminé, récupérer l'artefact `canet-de-notre-apk` contenant le fichier APK.

Le workflow est conçu pour construire un APK debug reproductible sans Android Studio.

## Test local du moteur

```bash
python -m py_compile moteur.py main.py
python -m unittest discover -s tests -v
```

Kivy n'est pas nécessaire pour exécuter les tests du moteur. Pour compiler l'APK, GitHub Actions installe les dépendances Android via Buildozer.

## Principe de sécurité

Le moteur original n'est pas réécrit par l'interface. L'interface utilise ses classes (`MoteurCarnet`, `AnneeScolaire`, `Matiere`, `Note`) et conserve la sauvegarde dans le stockage privé de l'application.

Une note hors barème est conservée visuellement afin de pouvoir être signalée en rouge, mais le calcul officiel est laissé au moteur strict : l'interface vérifie le dépassement avant de demander le calcul au moteur.
