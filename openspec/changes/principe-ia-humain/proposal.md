# Proposal — principe-ia-humain : reformuler P2

## Why

Le principe P2 était écrit « aucune IA générative », et le garde-fou `no_llm_guard.py`
interdit tout client de modèle. C'est plus strict que l'intention réelle du produit, énoncée
par Alexis :

> « c'est pas aucune IA pour l'utilisateur, mais aucune discussion avec IA. Discussion 100 %
> humaine. »

Autrement dit : **l'interlocuteur est toujours un humain**. Ce qui est proscrit, c'est qu'une
IA se fasse passer pour le correspondant, rédige les messages, ou simule un échange. Une aide
outil (traduction, dictionnaire, annotation) reste compatible avec cette promesse — le
produit se définit par la nature de l'échange, pas par l'absence d'algorithmes.

## What Changes

- **Reformulation de P2** : « aucune IA comme interlocuteur ; tout message échangé est écrit
  par un humain ».
- **Conséquence sur le garde-fou** : `no_llm_guard.py` doit distinguer deux usages —
  *génération de message* (interdit) et *assistance outil* (autorisé, sous conditions).
- **Nouvelle exigence** : transparence de l'origine de toute aide affichée (dictionnaire,
  traducteur, annotation), pour qu'aucun texte généré ne puisse être confondu avec un message
  du correspondant.

## Hors périmètre

- Autoriser un agent conversationnel : exclu par définition.
- Assistance générative : **écartée** (décision du 18/10/2026) — aucun LLM, aucun niveau.

## Impact

- `openspec/specs/core.spec.md` — formulation de P2
- `scripts/no_llm_guard.py` — règle de séparation assistance / interlocution
- `README.md` — promesse produit reformulée
