# Matrice de couverture — mvp-v1

- Exigences : **44**
- Couvertes par au moins un test : **6**
- Scénarios : **71**
- Orphelines : **38**

| Exigence | Capacité | Scénarios | Tests |
|---|---|---|---|
| `REQ-COR-01` — Suggestion localisée | corrections | 3 | — **orpheline** |
| `REQ-COR-02` — Décision de l'auteur | corrections | 3 | — **orpheline** |
| `REQ-COR-03` — Traçabilité de la correction | corrections | 1 | — **orpheline** |
| `REQ-DSC-01` — Réciprocité stricte du feed | discovery | 2 | — **orpheline** |
| `REQ-DSC-02` — Exclusions du feed | discovery | 2 | — **orpheline** |
| `REQ-DSC-03` — Quota quotidien de découverte | discovery | 1 | — **orpheline** |
| `REQ-DSC-04` — Rewind borné | discovery | 1 | — **orpheline** |
| `REQ-ICE-01` — Trois questions issues des intérêts communs | icebreakers | 3 | — **orpheline** |
| `REQ-IDN-01` — Inscription par email | identity | 3 | `backend/tests/test_identity.py` |
| `REQ-IDN-02` — Sessions et rotation des jetons | identity | 2 | — **orpheline** |
| `REQ-IDN-03` — Connexion OAuth | identity | 2 | — **orpheline** |
| `REQ-LNG-01` — Traduction à la demande | language-tools | 3 | — **orpheline** |
| `REQ-LNG-02` — Aide à la lecture déterministe | language-tools | 2 | — **orpheline** |
| `REQ-LNG-03` — Aucune dépendance réseau pour l'aide à la lecture | language-tools | 1 | — **orpheline** |
| `REQ-LNG-04` — Exactitude des offsets | language-tools | 1 | — **orpheline** |
| `REQ-MAT-01` — Score d'affinité explicable | matching | 2 | — **orpheline** |
| `REQ-MAT-02` — Création du match sur like mutuel | matching | 2 | `backend/tests/test_matching.py` |
| `REQ-MAT-03` — Dématch | matching | 1 | — **orpheline** |
| `REQ-MAT-04` — Déterminisme du classement | matching | 1 | — **orpheline** |
| `REQ-MSG-01` — Accès restreint au fil | messaging | 1 | — **orpheline** |
| `REQ-MSG-02` — Envoi de message | messaging | 3 | — **orpheline** |
| `REQ-MSG-03` — Statut de lecture | messaging | 2 | — **orpheline** |
| `REQ-MSG-04` — Marquage de lecture naturel | messaging | 1 | — **orpheline** |
| `REQ-MSG-05` — Asynchronisme assumé | messaging | 1 | — **orpheline** |
| `REQ-MSG-06` — Pas de contenu généré | messaging | 1 | — **orpheline** |
| `REQ-ONB-01` — Onboarding actionnable en moins de 3 minutes | onboarding | 2 | `backend/tests/test_onboarding.py` |
| `REQ-ONB-02` — Validation de l'étape 1 | onboarding | 2 | — **orpheline** |
| `REQ-ONB-03` — Seuil d'intérêts | onboarding | 2 | — **orpheline** |
| `REQ-ONB-04` — Finalisation de l'onboarding | onboarding | 1 | — **orpheline** |
| `REQ-ONB-05` — Barre de progression fiable | onboarding | 1 | — **orpheline** |
| `REQ-ONB-06` — Étape 3 sautable | onboarding | 1 | — **orpheline** |
| `REQ-ONB-07` — Robustesse de la photo | onboarding | 2 | — **orpheline** |
| `REQ-ONB-08` — Intérêts stables et traduisibles | onboarding | 2 | — **orpheline** |
| `REQ-PLT-01` — Intégrité du schéma | platform | 2 | `backend/tests/test_schema_integrity.py` |
| `REQ-PLT-02` — Aucun échec silencieux | platform | 2 | `backend/tests/test_errors.py` |
| `REQ-PLT-03` — Navigation clavier du discovery | platform | 1 | — **orpheline** |
| `REQ-PLT-04` — Accessibilité des états | platform | 1 | — **orpheline** |
| `REQ-PLT-05` — Contrat OpenAPI versionné | platform | 1 | — **orpheline** |
| `REQ-PLT-06` — Tests obligatoires par exigence | platform | 1 | — **orpheline** |
| `REQ-PLT-07` — Observabilité minimale | platform | 1 | `backend/tests/test_health.py`, `backend/tests/test_request_id.py` |
| `REQ-SAF-01` — Effet immédiat du blocage | safety | 1 | — **orpheline** |
| `REQ-SAF-02` — Signalement conservant la preuve | safety | 1 | — **orpheline** |
| `REQ-SAF-03` — Protection contre l'énumération de comptes | safety | 1 | — **orpheline** |
| `REQ-SAF-04` — Suppression de compte effective | safety | 1 | — **orpheline** |

## Scénarios orphelins

- `REQ-COR-01` — Plage invalide
- `REQ-COR-01` — Auto-correction interdite
- `REQ-COR-01` — Chevauchement de suggestions
- `REQ-COR-02` — Acceptation
- `REQ-COR-02` — Correction devenue obsolète
- `REQ-COR-02` — Décision par un tiers
- `REQ-COR-03` — Vue auteur après acceptation
- `REQ-DSC-01` — Candidat non réciproque
- `REQ-DSC-01` — Paires réciproques multiples
- `REQ-DSC-02` — Profil déjà passé
- `REQ-DSC-02` — Blocage croisé
- `REQ-DSC-03` — Quota atteint
- `REQ-DSC-04` — Second rewind
- `REQ-ICE-01` — Intérêts communs suffisants
- `REQ-ICE-01` — Un seul intérêt commun
- `REQ-ICE-01` — Stabilité dans le temps
- `REQ-IDN-02` — Refresh valide
- `REQ-IDN-02` — Réutilisation d'un refresh révoqué
- `REQ-IDN-03` — Premier login OAuth
- `REQ-IDN-03` — Rapprochement de compte
- `REQ-LNG-01` — Traduction d'un message
- `REQ-LNG-01` — Provider indisponible
- `REQ-LNG-01` — Langue non supportée
- `REQ-LNG-02` — Phrase japonaise
- `REQ-LNG-02` — Langue sans aide disponible
- `REQ-LNG-03` — Serveur sans accès externe
- `REQ-LNG-04` — Texte mixte
- `REQ-MAT-01` — Trois intérêts communs sur cinq
- `REQ-MAT-01` — Aucun intérêt commun
- `REQ-MAT-03` — Dématch unilatéral
- `REQ-MAT-04` — Deux appels successifs
- `REQ-MSG-01` — Intrusion
- `REQ-MSG-02` — Message valide
- `REQ-MSG-02` — Message vide ou trop long
- `REQ-MSG-02` — Match fermé
- `REQ-MSG-03` — Marquage en lot
- `REQ-MSG-03` — L'auteur ne compte pas
- `REQ-MSG-04` — Fil ouvert
- `REQ-MSG-05` — Perte de connexion pendant la rédaction
- `REQ-MSG-06` — Audit du produit
- `REQ-ONB-02` — Langues identiques
- `REQ-ONB-02` — Langue non supportée
- `REQ-ONB-03` — Deux intérêts seulement
- `REQ-ONB-03` — Intérêt inconnu ou inactif
- `REQ-ONB-04` — Finalisation incomplète
- `REQ-ONB-05` — Retour à l'étape précédente
- `REQ-ONB-06` — Saut de l'étape 3
- `REQ-ONB-07` — Fichier trop volumineux
- `REQ-ONB-07` — Format non supporté
- `REQ-ONB-08` — Chargement du catalogue
- `REQ-ONB-08` — Retrait d'un intérêt
- `REQ-PLT-03` — Like au clavier
- `REQ-PLT-04` — Nouveau message
- `REQ-PLT-05` — Dérive de contrat
- `REQ-PLT-06` — Scénario orphelin
- `REQ-SAF-01` — Blocage pendant une conversation
- `REQ-SAF-02` — Signalement d'un message
- `REQ-SAF-03` — Login avec email inconnu
- `REQ-SAF-04` — Suppression demandée
