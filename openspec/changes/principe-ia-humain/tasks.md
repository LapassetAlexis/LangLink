# Tasks — principe-ia-humain

- [ ] 1.1 Reformuler P2 dans `openspec/specs/core.spec.md` (« aucune IA comme interlocuteur ») — **vérif** : le texte ne dit plus « aucune IA générative » mais précise que l'interlocuteur est humain.
- [ ] 1.2 Mettre à jour le docstring et les messages de `scripts/no_llm_guard.py` pour refléter l'invariant réel — **vérif** : le script explique la séparation interlocution / assistance ; comportement inchangé, tests verts.
- [ ] 1.3 Reformuler la promesse dans `README.md` (« discussion 100 % humaine », pas « zéro IA ») — **vérif** : la phrase apparaît dans les 10 premières lignes.
- [ ] 1.4 Documenter la décision D-2 (assistance générative non tranchée) dans `design.md` du MVP — **vérif** : la ligne « générative : non tranché » est présente.
- [x] 1.5 Acter l'absence de LLM dans le design (D-2) — **vérif** : ✅ D-2 liste les trois moteurs déterministes et conclut au maintien de l'interdit global du garde-fou.
