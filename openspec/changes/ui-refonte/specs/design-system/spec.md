# Spec Delta — design-system

## Purpose

Fournir une identité visuelle et un socle de composants partagés pour l'application web
LangLink, afin que chaque écran hérite d'une apparence cohérente, accessible et
reconnaissable — sans dupliquer de styles ad hoc.

## ADDED Requirements

### Requirement: [REQ-UIX-01] Tokens de design centralisés

Le système SHALL exprimer couleurs, typographie, rayons et ombres sous forme de variables
CSS et de tokens Tailwind, et aucun écran SHALL définir une couleur littérale en dehors des
tokens.

#### Scenario: Changement global d'accent
- **WHEN** on modifie la valeur d'un token d'accent
- **THEN** tous les composants qui l'utilisent changent sans modification écran par écran

#### Scenario: Aucune couleur en dur dans un écran
- **WHEN** on inspecte les composants d'écran
- **THEN** les couleurs proviennent des classes de token (`brand-*`, `surface`, `field`…)
- **AND** aucune valeur hexadécimale n'apparaît dans un fichier `.tsx`

### Requirement: [REQ-UIX-02] Typographie éditoriale à deux familles

Le système SHALL combiner une serif d'affichage pour les titres et une sans-serif lisible
pour le texte courant, avec des tailles et interlignes cohérents.

#### Scenario: Titre de section
- **WHEN** un écran affiche un titre principal
- **THEN** il utilise la classe `.display` (serif, tracking négatif)
- **AND** le texte courant reste en sans-serif avec un interligne d'au moins 1.5

#### Scenario: Repli sans réseau
- **WHEN** les polices distantes ne se chargent pas
- **THEN** le rendu utilise les piles de repli déclarées (`Georgia`, `system-ui`)
- **AND** la mise en page ne se décale pas au point de casser la lecture

### Requirement: [REQ-UIX-03] Primitives de composants partagées

Le système SHALL fournir les primitives `.surface`, `.btn-primary`, `.btn-ghost`, `.field`,
`.chip`, `.chip-on` et `.bubble-them`, et les écrans SHALL les réutiliser plutôt que
redéfinir leurs styles.

#### Scenario: Bouton d'action principal
- **WHEN** un écran propose une action principale
- **THEN** il utilise `.btn-primary`
- **AND** l'état désactivé réduit l'opacité et bloque le curseur

#### Scenario: Champ de formulaire
- **WHEN** un formulaire affiche une saisie
- **THEN** il utilise `.field`, avec bordure visible et focus contrasté

### Requirement: [REQ-UIX-04] Accessibilité visuelle

Le système SHALL garantir un focus visible sur tout élément interactif, un contraste
suffisant sur le texte principal, et le respect de la préférence « mouvement réduit ».

#### Scenario: Navigation au clavier
- **WHEN** l'utilisateur tabule dans un écran
- **THEN** chaque élément interactif affiche un anneau de focus visible
- **AND** l'anneau n'est jamais masqué par `outline: none`

#### Scenario: Mouvement réduit
- **WHEN** le système exprime `prefers-reduced-motion: reduce`
- **THEN** les animations d'apparition sont désactivées
- **AND** le contenu reste intégralement lisible

#### Scenario: Contraste du texte principal
- **WHEN** on mesure le contraste du texte courant sur le fond encre
- **THEN** le ratio atteint au moins 4.5:1

### Requirement: [REQ-UIX-05] États explicites et cohérents

Le système SHALL définir un rendu commun pour les états chargement, vide et erreur, et aucun
écran SHALL afficher un état vide sans texte explicatif.

#### Scenario: Liste vide
- **WHEN** une liste ne contient aucun élément
- **THEN** un message explicatif et une action de sortie sont affichés
- **AND** l'écran n'affiche pas un conteneur vide sans explication

#### Scenario: Erreur d'action
- **WHEN** une action échoue
- **THEN** l'erreur apparaît dans une zone `role="alert"` lisible
- **AND** la saisie de l'utilisateur n'est pas perdue

### Requirement: [REQ-UIX-06] Mise en page mobile-first

Le système SHALL concevoir les écrans pour une largeur de 360 px et les enrichir au-delà,
sans apparition de défilement horizontal.

#### Scenario: Écran étroit
- **WHEN** la fenêtre fait 360 px de large
- **THEN** les blocs s'empilent verticalement
- **AND** aucun contenu ne dépasse horizontalement

#### Scenario: Écran large
- **WHEN** la fenêtre dépasse 1024 px
- **THEN** les pages à deux colonnes (accueil, authentification) affichent leurs deux
  colonnes
- **AND** la largeur de lecture reste bornée pour ne pas étirer les lignes de texte
