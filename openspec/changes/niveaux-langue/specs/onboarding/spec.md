# Spec Delta — onboarding

## ADDED Requirements

### Requirement: [REQ-ONB-09] Niveau exprimé par un libellé compréhensible

Le système SHALL présenter le niveau d'apprentissage par un libellé en langage courant, et
SHALL conserver le code CEFR comme information secondaire.

#### Scenario: Choix du niveau à l'enrôlement
- **WHEN** l'utilisateur choisit son niveau
- **THEN** les options affichent « Débutant », « Intermédiaire », « Confirmé »,
  « Avancé », « Maîtrise »
- **AND** le code CEFR correspondant est visible en infobulle, jamais comme libellé principal

#### Scenario: Restitution après coup
- **WHEN** l'utilisateur revient sur son profil
- **THEN** son niveau est réaffiché avec le même libellé qu'à la saisie
- **AND** la valeur stockée reste un code CEFR

### Requirement: [REQ-ONB-10] Échelle adaptée à la langue cible

Le système SHALL proposer, lorsque la langue cible dispose d'un référentiel local répandu,
les libellés de ce référentiel à la place des libellés génériques.

#### Scenario: Langue cible = japonais
- **WHEN** l'utilisateur apprend le japonais
- **THEN** les options affichent `N5` à `N1` avec leur équivalent en clair
  (« N5 · Débutant »)
- **AND** la correspondance vers le rang interne 1–6 est documentée

#### Scenario: Langue sans référentiel local
- **WHEN** la langue cible n'a pas de référentiel configuré
- **THEN** les libellés génériques sont utilisés
- **AND** aucun code `N` n'apparaît

### Requirement: [REQ-ONB-11] Compatibilité de niveau inchangée

Le système SHALL continuer de calculer la compatibilité de niveau sur un rang numérique
1–6, indépendamment du libellé affiché.

#### Scenario: Même niveau, libellés différents
- **WHEN** deux profils ont le même rang stocké
- **THEN** la composante « niveau » du score vaut 1.0
- **AND** le libellé affiché n'influence pas le calcul
