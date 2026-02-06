# UVSQ-celcat
Scripts en lien avec edt.uvsq.fr

## Scripts
- Générer un fichier .ics à partir de celcat  
Pour exporter son emploi du temps.
- Récupérer des listes de salles  
Sélectionner VER pour les étudiant.e.s en Licence/Master d'Informatique.
- Vérifier la disponibilité d'une liste de salles le matin et le soir  
Le script affiche 𖤓/☾ pour matin/soir en rouge/vert pour occupé/disponible.
- Trouver des salles disponibles à un moment donné  
Ce dernier script affiche quelles salles sont disponible et jusqu'à quelle heure.

## Pourquoi ?
Dans mon cas, trouver une salle quand on est affecté à une salle sans prises alors qu'on en a besoin (:

## Divers
Formatté avec `ruff`.  
Les listes de salles sont dans le `.gitignore` pour ne pas laisser une trace de toutes les salles sur internet.  
La nomenclature des salles est terrible : certaines salles sont en double, d'autres ont des espaces additionnels obligatoires pour être reconnues par celcat.  
