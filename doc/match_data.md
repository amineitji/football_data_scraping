# Documentation des Données de Match - WhoScored

Ce document détaille la structure des données d'un match de football récupérées depuis WhoScored.

## matchId
- **Valeur** : `1783954`
- **Description** : Identifiant unique pour ce match spécifique.

## matchCentreData
Contient des données détaillées sur les joueurs, les périodes, et les statistiques du match.

### playerIdNameDictionary
- **Type** : Dictionnaire
- **Description** : Associe les identifiants des joueurs à leurs noms.
- **Exemple** : `"345560": "Patson Daka"`

### periodMinuteLimits
- **Type** : Dictionnaire
- **Description** : Délimite les minutes pour chaque période du match (par exemple, première mi-temps, deuxième mi-temps).

### timeStamp
- **Type** : Chaîne de caractères
- **Description** : Horodatage indiquant quand les données ont été capturées.
- **Exemple** : `"2024-01-25 08:56:31"`

### attendance
- **Type** : Entier
- **Description** : Nombre de spectateurs présents au match.
- **Exemple** : `15231`

### venueName
- **Type** : Chaîne de caractères
- **Description** : Nom du stade où le match a eu lieu.
- **Exemple** : `"Stade Laurent Pokou"`

### referee
- **Type** : Objet
- **Description** : Informations sur l'arbitre du match.
- **Attributs** :
  - `officialId` : Identifiant de l'arbitre.
  - `firstName` : Prénom de l'arbitre.
  - `lastName` : Nom de l'arbitre.
  - `name` : Nom complet de l'arbitre.
  
### elapsed
- **Type** : Chaîne de caractères
- **Description** : Statut du match (par exemple, "FIN" pour terminé).

### startTime et startDate
- **Type** : Chaîne de caractères
- **Description** : Date et heure de début du match.
- **Exemples** :
  - `startTime` : `"2024-01-24T21:00:00"`
  - `startDate` : `"2024-01-24T00:00:00"`

### score
- **Type** : Chaîne de caractères
- **Description** : Score final du match.
- **Exemple** : `"0 : 1"`

### htScore, ftScore, etScore, pkScore
- **Type** : Chaîne de caractères
- **Description** : Score à la mi-temps, score final, score en prolongation, et score lors des tirs au but respectivement.
- **Exemples** :
  - `htScore` : `"0 : 1"`
  - `ftScore` : `"0 : 1"`
  - `etScore` : `""` (vide si non applicable)
  - `pkScore` : `""` (vide si non applicable)

### statusCode
- **Type** : Entier
- **Description** : Code de statut indiquant l'état actuel du match.

### periodCode
- **Type** : Entier
- **Description** : Code représentant la période du match.

## home et away
Représentent les deux équipes jouant le match.

### teamId
- **Type** : Entier
- **Description** : Identifiant unique de l'équipe.

### formations
- **Type** : Tableau d'objets
- **Description** : Liste des formations utilisées par l'équipe pendant le match.
- **Attributs des objets** :
  - `formationId` : Identifiant de la formation.
  - `formationName` : Nom de la formation (ex. : "4231").
  - `captainPlayerId` : ID du capitaine de l'équipe.
  - `period` : Période pendant laquelle la formation a été utilisée.
  - `startMinuteExpanded`, `endMinuteExpanded` : Période pendant laquelle la formation était active.
  - `jerseyNumbers` : Liste des numéros de maillot des joueurs dans cette formation.
  - `formationSlots` : Positions des joueurs dans la formation.
  - `playerIds` : IDs des joueurs dans la formation.
  - `formationPositions` : Positions des joueurs sur le terrain, représentées par des coordonnées.

## stats
Contient les statistiques détaillées du match pour l'équipe, minute par minute.

### ratings
- **Type** : Dictionnaire
- **Description** : Évaluations des joueurs au fil du temps.

### Autres Statistiques :
- `shotsTotal`, `shotsOnTarget`, `shotsOffTarget` : Statistiques liées aux tirs.
- `clearances`, `interceptions` : Actions défensives.
- `possession` : Statistiques de possession du ballon.
- `touches` : Nombre de fois où les joueurs ont touché le ballon.
- `passesTotal`, `passesAccurate`, `passSuccess` : Statistiques de passes.
- `aerialsTotal`, `aerialsWon` : Statistiques des duels aériens.
- `cornersTotal`, `cornersAccurate` : Statistiques des corners.
- `throwInsTotal`, `throwInsAccurate` : Statistiques des touches.
- `offsidesCaught` : Nombre de fois où les joueurs ont été pris en hors-jeu.
- `foulsCommited` : Nombre de fautes commises.
- `tacklesTotal`, `tackleSuccessful`, `dribbledPast` : Statistiques des tacles.

## incidentEvents
Liste des événements significatifs du match, tels que les remplacements, buts, fautes, etc.

### Attributs des événements :
- `id` : Identifiant unique de l'événement.
- `eventId` : Type d'événement (ex. : remplacement, but).
- `minute`, `second` : Moment où l'événement s'est produit.
- `teamId` : Identifiant de l'équipe associée à l'événement.
- `playerId` : Identifiant du joueur impliqué.
- `relatedEventId`, `relatedPlayerId` : Événements et joueurs associés, si applicable.
- `x`, `y` : Coordonnées de l'événement sur le terrain.
- `expandedMinute` : Minute étendue au temps de jeu réel.
- `period` : Période durant laquelle l'événement a eu lieu.
- `type` : Type d'événement (ex. : remplacement).
- `outcomeType` : Résultat de l'événement (ex. : réussi).
- `qualifiers` : Qualificateurs supplémentaires liés à l'événement.

## shotZones
Décompose les statistiques de tir en différentes zones sur le terrain (ex. : "missHighLeft", "onTargetLowCentre").

- **Type** : Objet
- **Description** : Chaque zone contient son propre objet de statistiques.

## players
Liste détaillée de tous les joueurs impliqués dans le match, incluant leurs informations personnelles, position, et statistiques de match.

### Attributs des joueurs :
- `playerId` : Identifiant unique du joueur.
- `shirtNo` : Numéro de maillot du joueur.
- `name` : Nom du joueur.
- `position` : Position du joueur sur le terrain.
- `height`, `weight`, `age` : Attributs physiques du joueur.
- `isFirstEleven` : Indique si le joueur faisait partie du onze de départ.
- `isManOfTheMatch` : Indique si le joueur a été élu Homme du Match.
- `field` : Indique si le joueur appartient à l'équipe à domicile ou à l'extérieur.
- `stats` : Statistiques détaillées du joueur pendant le match.
