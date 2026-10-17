# Spec Delta — platform

## Purpose

Socle technique : integrite du schema portee par la base, contrat OpenAPI verifie en CI, couverture des exigences par des tests, observabilite minimale.

## ADDED Requirements

### Requirement: [REQ-PLT-01] Intégrité du schéma
Le système SHALL faire respecter les contraintes d'unicité et de vérification au niveau
base de données, et non uniquement dans la couche applicative.

#### Scenario: Double swipe concurrent
- **WHEN** deux requêtes `POST /discovery/swipes` pour le même couple arrivent en parallèle
- **THEN** une seule insertion réussit
- **AND** l'autre renvoie `409 CONFLICT` avec l'état courant du swipe

#### Scenario: Match dupliqué
- **WHEN** deux likes réciproques déclenchent la création du match simultanément
- **THEN** une seule ligne `matches` est créée (contrainte d'unicité + `ON CONFLICT DO NOTHING`)
- **AND** les deux réponses renvoient le même `match_id`

---


### Requirement: [REQ-PLT-02] Aucun échec silencieux
Toute action utilisateur SHALL produire un retour visible en cas d'échec.

#### Scenario: Envoi refusé
- **WHEN** l'envoi d'un message renvoie `409 match.closed`
- **THEN** la bulle passe en état « non envoyé » avec la raison affichée
- **AND** le texte reste dans la zone de saisie

#### Scenario: Traduction en échec
- **WHEN** la traduction renvoie `503`
- **THEN** un bandeau non bloquant « Traduction indisponible, réessayer » apparaît
- **AND** le message original reste affiché


### Requirement: [REQ-PLT-03] Navigation clavier du discovery
Le système SHALL permettre de traiter les cartes sans souris.

#### Scenario: Like au clavier
- **WHEN** l'utilisateur appuie sur `→` avec le focus sur la pile
- **THEN** la carte courante est likée et la suivante s'affiche


### Requirement: [REQ-PLT-04] Accessibilité des états
Le système SHALL exposer les états dynamiques via des régions `aria-live` et des libellés
explicites.

#### Scenario: Nouveau message
- **WHEN** un message arrive pendant que le fil est ouvert
- **THEN** une région `aria-live="polite"` annonce « Nouveau message de <prénom> »

---


### Requirement: [REQ-PLT-05] Contrat OpenAPI versionné
Le backend SHALL publier `/api/v1/openapi.json` et le frontend SHALL générer ses types
depuis ce contrat.

#### Scenario: Dérive de contrat
- **WHEN** un schéma de réponse change sans régénération des types front
- **THEN** la CI échoue sur l'étape de vérification de génération


### Requirement: [REQ-PLT-06] Tests obligatoires par exigence
Chaque exigence SHALL être couverte par au moins un test automatisé référençant son
identifiant (`REQ-*`) en docstring ou en nom de test.

#### Scenario: Scénario orphelin
- **WHEN** la matrice de couverture est générée
- **THEN** tout scénario sans test apparaît explicitement
- **AND** la CI signale les exigences non couvertes sans les déclarer couvertes à tort


### Requirement: [REQ-PLT-07] Observabilité minimale
Le système SHALL exposer `/healthz`, `/readyz` et des logs JSON corrélés par `X-Request-Id`.

#### Scenario: Sonde de disponibilité
- **WHEN** `GET /readyz` est appelé et que la base répond
- **THEN** la réponse est `200` avec `{db:"ok", version:"..."}`
