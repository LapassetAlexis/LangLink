# Design — principe-ia-humain

## Decisions

### D-1 — La frontière est « qui parle », pas « quel algorithme »

L'invariant vérifiable : dans la table `messages`, chaque ligne porte un `sender_id` humain
authentifié. Aucune ligne ne peut être produite par un service. C'est testable en base, alors
que « pas d'IA » ne l'est pas.

### D-2 — Assistance : déterministe uniquement (décision du 18/10/2026)

**Aucun LLM, à aucun niveau.** L'assistance se limite à trois moteurs déterministes :

| Outil | Usage | Nature |
|---|---|---|
| LibreTranslate (auto-hébergé) | traduction à la demande | déterministe, local |
| Wiktionnaire (API MediaWiki) | sens multiples d'un mot | dictionnaire existant |
| fugashi + pykakasi | lecture et romaji du japonais | analyse morphologique locale |

Le « petit bot en bas » évoqué par Alexis est un **tiroir d'assistance à la traduction**, pas
un agent : il ne comprend pas, il ne répond pas, il traduit et il affiche des définitions.
Conséquence directe : le garde-fou `no_llm_guard.py` **reste un interdit global**, sans
exception. Aucun répertoire d'assistance n'est ouvert aux clients de modèle.

### D-3 — Le garde-fou doit changer de forme, pas disparaître

`no_llm_guard.py` interdit aujourd'hui `import openai` n'importe où. Sous la nouvelle
formulation, la règle devient :

- **interdit** : tout client de modèle importé depuis `app/services/messaging.py`,
  `app/api/v1/messaging/`, ou toute fonction qui écrit dans `messages` ;
- **autorisé sous conditions** : modules d'assistance (`app/services/language.py`,
  `app/services/lexicon.py`), à condition d'afficher la source.

Un garde-fou par liste blanche de répertoires est plus fragile qu'un interdit global. Le
compromis retenu : interdiction globale maintenue pour l'instant, avec la liste des
répertoires d'assistance documentée comme exception possible — à n'ouvrir qu'au moment où
l'assistance générative sera réellement décidée.

### D-4 — Ce que la reformulation débloque vraiment

Rien d'immédiat. Aucune ligne de code ne change aujourd'hui : LibreTranslate, le Wiktionnaire
et fugashi sont déjà déterministes. Ce qui change, c'est la **justification** : on n'exclut
plus une technologie par principe, on interdit un usage précis.
