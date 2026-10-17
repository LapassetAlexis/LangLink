# Spec Delta — identity

## Purpose

Gestion des comptes LangLink : inscription, authentification par email ou OAuth, jetons d'acces courts et refresh rotatif, protection contre l'enumeration de comptes.

## ADDED Requirements

### Requirement: [REQ-IDN-01] Inscription par email
Le système SHALL créer un compte actif dès l'inscription, sans exiger la vérification
d'email pour utiliser le produit, tout en marquant `email_verified_at` à NULL.

#### Scenario: Inscription valide
- **WHEN** un visiteur poste un email inconnu et un mot de passe de 12 caractères
- **THEN** l'API renvoie `201` avec un `access_token` valide 15 minutes
- **AND** un profil vide est créé (`onboarding_step = 1`, `discoverable = false`)

#### Scenario: Email déjà utilisé
- **WHEN** l'email existe déjà, quelle que soit la casse
- **THEN** l'API renvoie `409` de type `auth.email_taken`
- **AND** aucun détail sur l'existence d'un compte OAuth n'est divulgué

#### Scenario: Mot de passe faible
- **WHEN** le mot de passe fait moins de 10 caractères ou figure dans la liste des 10 000 plus courants
- **THEN** l'API renvoie `422` avec `errors[{field:"password"}]`


### Requirement: [REQ-IDN-02] Sessions et rotation des jetons
Le système SHALL émettre un access token court et un refresh token opaque rotatif,
stocké uniquement sous forme de hash.

#### Scenario: Refresh valide
- **WHEN** le client présente un cookie refresh non expiré et non révoqué
- **THEN** l'ancien refresh est révoqué et un nouveau est émis (rotation)
- **AND** un nouvel access token est renvoyé

#### Scenario: Réutilisation d'un refresh révoqué
- **WHEN** un refresh déjà utilisé est présenté
- **THEN** toutes les sessions de l'utilisateur sont révoquées
- **AND** l'API renvoie `401 auth.token_expired`


### Requirement: [REQ-IDN-03] Connexion OAuth
Le système SHALL supporter Google et GitHub via OAuth 2.0 Authorization Code + PKCE.

#### Scenario: Premier login OAuth
- **WHEN** un utilisateur revient du provider avec un email inconnu
- **THEN** un compte est créé avec `email_verified_at` renseigné
- **AND** `onboarding_step = 1`

#### Scenario: Rapprochement de compte
- **WHEN** l'email OAuth correspond à un compte email/mot de passe existant
- **THEN** le provider est rattaché au compte existant sans écraser le mot de passe
- **AND** l'utilisateur est connecté
