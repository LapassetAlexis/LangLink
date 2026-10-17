# Spec Delta — language-tools

## Purpose

Outils d'assistance linguistique deterministes : traduction a la demande avec cache et bascule de fournisseur, aide a la lecture japonaise hors ligne (furigana et romaji).

## ADDED Requirements

### Requirement: [REQ-LNG-01] Traduction à la demande
Le système SHALL ne traduire qu'à la demande explicite, mettre en cache le résultat et ne
jamais envoyer de trafic utilisateur à un service tiers sans action de l'utilisateur.

#### Scenario: Traduction d'un message
- **WHEN** B demande la traduction d'un message de A (`fr` → `ja`)
- **THEN** l'API renvoie `{translated, provider, cached:false}`
- **AND** une seconde demande identique renvoie `cached:true` sans appel externe

#### Scenario: Provider indisponible
- **WHEN** LibreTranslate ne répond pas dans les 5 secondes
- **THEN** l'API bascule sur le provider secondaire configuré
- **AND** si les deux échouent, renvoie `503 language.provider_unavailable`
- **AND** aucune erreur 500 n'est exposée à l'utilisateur

#### Scenario: Langue non supportée
- **WHEN** la paire demandée n'est pas dans `capabilities`
- **THEN** l'API renvoie `422 language.unsupported` et l'UI masque l'action


### Requirement: [REQ-LNG-02] Aide à la lecture déterministe
Le système SHALL produire, pour le japonais, une annotation tokenisée `{surface, reading,
romaji, start, end}` via un tokenizer et un dictionnaire locaux, sans appel réseau.

#### Scenario: Phrase japonaise
- **WHEN** l'utilisateur demande l'aide à la lecture pour `"私は学生です"`
- **THEN** la réponse contient 4 à 6 tokens avec `reading` en kana et `romaji`
- **AND** les offsets reconstituent exactement le texte d'origine

#### Scenario: Langue sans aide disponible
- **WHEN** la langue demandée n'a pas de moteur configuré
- **THEN** l'API renvoie `422 language.unsupported`
- **AND** le bouton n'est pas rendu côté client


### Requirement: [REQ-LNG-03] Aucune dépendance réseau pour l'aide à la lecture
Le système SHALL exécuter la tokenisation localement, y compris hors connexion Internet.

#### Scenario: Serveur sans accès externe
- **WHEN** l'API n'a pas d'accès Internet
- **THEN** `POST /language/reading-aid` répond `200` avec les annotations
- **AND** aucune requête sortante n'est émise


### Requirement: [REQ-LNG-04] Exactitude des offsets
Le système SHALL garantir que la concaténation des `surface` reconstitue le texte d'entrée
à l'octet près (UTF-8).

#### Scenario: Texte mixte
- **WHEN** le texte contient kanji, kana, latin et ponctuation
- **THEN** `"".join(t.surface) == text`
- **AND** chaque `start` égale la somme des longueurs précédentes

---
