# UVSQ-celcat
Scripts en lien avec edt.uvsq.fr

## Scripts
- Générer un fichier .ics à partir de celcat
- Récupérer des listes des salles
- Vérifier la disponibilité d'une liste de salles

## Pourquoi ?
Trouver une salle avec prise quand on est affecté à une salle sans prise alors qu'on en a besoin (:

## Divers
Formatté avec `ruff`.
Les listes de salles sont dans le `.gitignore` pour ne pas laisser une trace de toutes les salles sur internet.
L'API de celcat est terrible.
Certaines salles sont en doubles, d'autres ont des espaces additionnels obligatoires pour être reconnues par celcat.
Le script de disponibilité affiche 𖤓/☾ pour matin/soir en rouge/vert pour occupé/disponible.