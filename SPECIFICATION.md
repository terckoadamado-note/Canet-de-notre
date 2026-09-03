# Spécification de Canet de notre — version de base

## 1. Identité

- Nom affiché de l'application : **Canet de notre**.
- Version initiale de l'application : **1.0**.
- Cœur de calcul : `moteur.py`.
- L'APK doit fonctionner sans lancer Termux.
- Construction prévue par GitHub Actions avec Buildozer, sans Android Studio.

## 2. Interface générale

- Palette générale : **bleu et blanc**.
- Barre supérieure bleue.
- À gauche : icône de cahier/livres et bouton hamburger.
- Titre : Canet de notre.
- À droite : notification et menu trois points.
- Le bouton de sauvegarde n'est plus dans la barre supérieure : il est dans la barre du bas.
- Le menu trois points reste en haut.
- En bas : barre de navigation avec Accueil, gros bouton central Statistiques et Sauvegarde.
- Le bouton Statistiques est visuellement plus important que les autres.
- Les statistiques utilisent un **diagramme circulaire complet**.

## 3. Panneau latéral

Le hamburger ouvre un tiroir depuis la gauche. Le panneau **glisse** de la gauche vers l'intérieur au lieu d'apparaître instantanément.

Éléments prévus :

- Accueil
- Notifications
- Barèmes
- Aide
- À propos

## 4. Tableau : règle principale

Structure hiérarchique :

```text
Matière | Coef | INTERROGATIONS | DEVOIRS | Moyenne | 🗑
                I1 I2 I3 ...    D1 D2 ...
```

- Les matières sont des **lignes / axe Y**.
- Les interrogations sont des **colonnes du groupe INTERROGATIONS**.
- Les devoirs sont des **colonnes du groupe DEVOIRS**.
- La moyenne est à droite des notes.
- Une corbeille est disponible à l'extrémité de chaque ligne pour supprimer la matière.
- Ajouter une interrogation ajoute une colonne dans INTERROGATIONS uniquement.
- Ajouter un devoir ajoute une colonne dans DEVOIRS uniquement.
- Une nouvelle interrogation ne doit jamais pousser une colonne de devoirs dans le groupe des interrogations.
- Une nouvelle matière crée une nouvelle ligne complète.

## 5. Notes et cellules

- Les cellules de notes acceptent des nombres uniquement.
- Les décimales sont acceptées.
- Les lettres ne sont pas acceptées dans une cellule de note.
- Une cellule vide n'est jamais transformée en zéro.
- Un zéro réellement saisi est une vraie note.
- Aucun calcul n'est déclenché pendant la saisie.
- Le calcul est déclenché uniquement par le bouton **CALCULER**.

## 6. Barèmes

- Barème par défaut : **20**.
- Le barème n'est pas affiché dans le tableau.
- Aucun `/20`, `/10`, `/30`, etc. ne doit être visible dans le tableau.
- Le barème reste actif dans le moteur.
- Le menu latéral contient **Barèmes**.
- L'utilisateur peut modifier le barème par défaut.
- Un double-appui sur une cellule permet de modifier le barème de cette cellule seulement.
- Le barème individuel peut être décimal.
- Si la note dépasse le barème, la cellule devient rouge.

## 7. Alertes de dépassement

Les alertes de dépassement de barème sont affichées dans la zone inférieure où apparaît aussi le résultat de calcul.

Exemple :

```text
🔴 Attention : une note dépasse son barème.
```

Le barème lui-même reste invisible dans le tableau.

## 8. Calcul

Le moteur conserve sa logique :

- moyenne des interrogations présentes ;
- les devoirs présents sont ensuite pris comme éléments séparés ;
- les cases vides sont ignorées ;
- conversion des notes selon leur barème ;
- points d'une matière = moyenne de la matière × coefficient ;
- moyenne générale = total des points / total des coefficients pris en compte.

Dans la colonne **Moyenne**, l'application affiche les **points pondérés** de la matière (moyenne × coefficient), pas une note avec `/20`.

Après un calcul réussi :

```text
✓ Calcul effectué
```

Le message est vert et disparaît après quelques secondes.

## 9. Résumé inférieur

Sous le tableau :

- nombre de matières ;
- total des coefficients ;
- moyenne totale.

La moyenne n'est jamais affichée avec `/20`.

## 10. Semestres et année

L'accueil permet de consulter :

- Premier semestre ;
- Deuxième semestre ;
- Moyenne annuelle.

La règle annuelle est :

```text
(Premier semestre × 2 + Deuxième semestre) ÷ 3
```

Si un seul semestre est disponible, le moteur existant peut utiliser ce semestre seul, conformément à sa logique actuelle.

La moyenne annuelle n'affiche pas `/20`.

## 11. Notifications de conseils

Les conseils ne doivent pas apparaître directement au milieu du tableau.

- L'icône 🔔 reçoit un **point rouge** lorsqu'il existe des notifications non lues.
- L'utilisateur appuie sur 🔔 pour ouvrir sa page de notifications.
- Les conseils sont générés après un calcul, pas dès la première note.
- Le seuil de déclenchement de l'analyse est environ **2/3 des cellules prévues remplies**.
- Le système peut signaler une moyenne générale ou une matière à surveiller et orienter le travail vers l'objectif de 10.
- Ces notifications sont distinctes des alertes rouges de dépassement de barème.

## 12. Matières courantes

Lors de l'ajout d'une matière, un champ indicatif **Matière** apparaît en gris.

Une liste de matières courantes est proposée, notamment :

- Mathématiques
- Français
- Anglais
- Histoire-Géographie
- SVT
- Physique-Chimie
- PCT
- Informatique
- EPS
- Philosophie
- Économie
- Allemand
- Espagnol
- Éducation Civique et Morale
- Arts Plastiques
- Musique
- Technologie

Une matière personnalisée peut également être écrite.

## 13. Sauvegarde

La sauvegarde est accessible depuis la barre inférieure. Les données sont enregistrées dans le stockage privé de l'application afin que l'APK puisse fonctionner seul.

## 14. À propos

Le contenu de référence fourni comprend :

- Cahier de notes
- Version 1.0
- Auteur : Jacques Adamado 🤣
- message de bienvenue
- texte de suggestion/problème
- Facebook : Fin de l'histoire
- Téléphone : +299 01 48 25 66 62
- Merci pour votre confiance

La couleur de l'ancien écran À propos n'est pas considérée comme définitive.

## 15. Références visuelles

Les images fournies pendant la conception sont conservées dans `reference/` : icône choisie, maquette générale, en-tête du tableau manuscrit, maquette manuscrite de l'accueil et écran À propos.
