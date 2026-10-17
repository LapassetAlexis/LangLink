# Design — ui-refinements

## Context

Cinq manques constatés à l'usage réel, tous côté présentation sauf le point 5 qui touche à
une capacité produit nouvelle. Le socle technique existe déjà : `/language/translate` accepte
du texte libre (`{text, source_lang, target_lang}`), ce qui permet de traduire une question
ou un mot sans nouvel endpoint.

## Goals / Non-Goals

**Goals** : corriger les cinq frictions sans toucher au modèle de données ni aux contrats
d'API existants.

**Non-Goals** : notifications, refonte du wizard, dictionnaire complet hors-ligne.

## Decisions

### D-1 — Icebreakers : traduction à la demande, pas de stockage

Le catalogue ne contient que FR et EN. Stocker 60 questions × 13 langues serait ingérable et
figerait des traductions non relues. On traduit **à la demande**, via `/language/translate`,
avec le cache `translations` déjà en place (clé = hash du texte + langues + provider). La
bascule FR/JP ne déclenche donc qu'un appel la première fois.

Alternative écartée : pré-traduire à la création du match — coût réseau au moment du match,
et 3 appels dont on ne sait pas s'ils serviront.

### D-2 — « Langue du correspondant » = langue visée du lecteur

Par construction de la réciprocité (P1), la langue maternelle du correspondant est exactement
la langue que le lecteur apprend. On utilise `detail.other.native_language` côté API, déjà
renvoyé par `GET /matches/{id}` : aucune donnée supplémentaire n'est nécessaire.

### D-3 — Statut de fil dérivé, jamais stocké côté client

Le statut affiché (`active`, `unmatched`, `blocked`) vient du champ `status` renvoyé par
`GET /matches`. L'interface ne le déduit pas d'un compteur ni d'une date : une déduction
finirait par mentir après un dématch.

### D-4 — ⚠️ Réserve technique sur le point 5 (aide au mot)

Alexis demande « un système à la Duolingo » : cliquer un mot et voir **les significations
possibles**. C'est irréalisable avec le moteur actuel : **LibreTranslate renvoie une seule
traduction**, pas un dictionnaire. Un mot polysémique (« marché » : lieu / transaction /
participe de « marcher ») sortira avec un seul sens, souvent faux dans le contexte.

Trois voies, à trancher :

| Voie | Ce qu'on obtient | Coût |
|---|---|---|
| **A. Traduction du mot** | 1 sens, parfois faux | immédiat (endpoint existant) |
| **B. Wiktionnaire (API REST)** | plusieurs sens + nature grammaticale | moyen, dépendance réseau externe |
| **C. JMdict / dictionnaire local** | plusieurs sens, hors ligne, fiable pour le japonais | lourd (dictionnaire ~50 Mo) |

Le présent change **spécifie** l'exigence (REQ-LEX-02 : plusieurs sens) et **implémente la
voie A** comme repli assumé, en attendant l'arbitrage. L'interface annonce clairement
« traduction automatique, sens unique » pour ne pas mentir sur la nature de l'aide.

### D-5 — Menu de compte dans l'en-tête, route `/settings`

Un menu discret (avatar + initiale) dans toutes les vues authentifiées, menant à
`/settings`. L'écran réutilise les endpoints existants (`GET /me/profile`, `PUT
/me/languages`, `PUT /me/interests`, `GET /me/blocks`, `POST /auth/logout`, `DELETE /me`) :
aucun contrat nouveau.

## Risks / Trade-offs

| Risque | Impact | Mitigation |
|---|---|---|
| Traduction d'icebreaker médiocre | Question incompréhensible | Bascule FR toujours disponible |
| Appel réseau à l'ouverture du fil | Latence perçue | Traduction déclenchée par la bascule, pas à l'affichage initial |
| Aide au mot à sens unique | Fausse impression de dictionnaire | Mention explicite dans l'interface (D-4) |
| `/settings` incomplet | Frustration | Les 5 blocs sont livrés ensemble, pas par moitié |
