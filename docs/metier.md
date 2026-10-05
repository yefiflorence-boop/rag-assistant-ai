# Documentation Métier — ONEAD Assistant RAG

> Assistant IA documentaire interne basé sur le RAG (Retrieval-Augmented Generation).
> Répond aux questions RH à partir des documents internes de l'ONEAD, avec sources citées.

## 1. Contexte et objectif

L'Office National de l'Eau et de l'Assainissement (ONEAD, Djibouti) dispose de
manuels RH volumineux et dispersés (procédures, GPEC, carrières, formation,
hygiène/sécurité). Les agents et la DRH perdent du temps à y chercher l'information.

**Objectif du produit :** permettre à un agent de poser une question en langage
naturel et d'obtenir une réponse courte, fiable et traçable — ou un refus
explicite avec un recours vers la DRH si l'information n'est pas dans le corpus.

Projet réalisé dans le cadre de la formation **AI Engineering — Groupe 1**
(MVP à usage interne / pédagogique).

## 2. Utilisateurs et cas d'usage

| Acteur | Besoin | Exemple de question |
|---|---|---|
| Agent ONEAD | Comprendre une procédure RH | « Comment fonctionne la gestion des absences ? », « Congés ? » |
| Nouvel arrivant | Se repérer dans les règles internes | « Quels actes pour un début de carrière ? » |
| DRH | Réduire les questions répétitives, repérer les manques du corpus | Revue de `data/feedback/unanswered.jsonl` |
| Mainteneur corpus | Savoir quelle base est en ligne | Sidebar « Base documentaire » (date, nb docs/chunks) |

**Hors périmètre volontaire :** tout ce qui n'est pas dans le corpus RH
(montants de primes non documentés, recettes de cuisine, actualités, données
personnelles comme un numéro privé) → refus contrôlé (voir §5).

## 3. Corpus de référence (5 documents)

Source de vérité unique : les PDF de `data/raw/` (voir `data/manifest.json` —
indexation du 2026-10-05, 5282 chunks, embedding `text-embedding-3-large`) :

| Document | Contenu couvert | Poids |
|---|---|---|
| `1543744461-Manuel_de_proc_dures_RH_de_lONEAD.pdf` | GPEC, prévention des risques / CHS, SIRH, évaluation annuelle, absences, congés, formation | 216 chunks |
| `MANUEL DE PROCEDURE DRH PME.pdf` | Missions DRH, service courrier, carrières, formation | 153 chunks |
| `MANUEL DE PROCEDURES EN RESSOURCES HUMAINES.pdf` | Harmonisation des procédures, actes de début de carrière | 157 chunks |
| `ORGANISATION INTERNATIONALE DU TRAVAIL.pdf` | Référentiel OIT (formation, normes) | 3170 chunks |
| `pub-2020001249601F-mca-human-resources-f.pdf` | Recrutement, code de conduite, évaluation MCA | 1586 chunks |

Règle : **si ce n'est pas dans ces 5 documents, l'assistant ne doit pas répondre.**

## 4. Contrat de réponse (règles métier)

Défini dans `chat_context.py:build_prompt` et `src/config.py` :

- Répond **uniquement** à partir du contexte récupéré (top-5 passages ChromaDB).
- Langue : **français uniquement**.
- Longueur : **50–150 mots max**.
- Ton : professionnel, direct, empathique. Listes à puces si plusieurs éléments.
- **Ne cite pas les sources dans le texte** : c'est `app.py:source_links`
  qui affiche sous la réponse `📄 [nom.pdf — page N](lien)`.
- Première interaction de la session : bonjour ; jamais ensuite.
- Zéro politesse excessive, zéro répétition.

## 5. Refus contrôlé + recours DRH

Quand aucun passage pertinent n'est récupéré (filtre par seuil, voir doc
Développement) ou que le modèle émet le message de refus, le système
(`app.py:180-193`, `chat_context.py:is_refusal`) :

1. Affiche le message unique (`src/config.py:36-39`) :
   > « Je n'ai pas trouvé cette information dans les documents disponibles.
   > Veuillez consulter la DRH ou le manuel de procédures correspondant. »
2. Affiche la carte **Recours DRH** (`src/config.py:41-46`) :
   Direction des Ressources Humaines — ONEAD, `drh@onead.dj`,
   `+253 21 35 00 00`, Dim–Jeu 8h–17h (surchageable via `DRH_EMAIL` / `DRH_TEL`).
3. Journalise la question dans `data/feedback/unanswered.jsonl`
   (`chat_context.py:log_unanswered`) pour revue DRH.

Ce fichier est le **capteur d'amélioration continue** : questions fréquentes
sans réponse = documents à ajouter ou à clarifier.

## 6. Traçabilité et confiance

- **Sidebar « Base documentaire »** (`app.py:86-95`) : date d'indexation,
  nb documents, nb chunks, modèle d'embedding — lus depuis
  `data/manifest.json` (généré par `src/indexation.py:109-125`, avec SHA-256
  par fichier).
- **Sources cliquables** avec ancre `#page=N` vers le PDF d'origine.
- **Évaluation** : `tests/20_questions.csv` couvre 4 scénarios —
  `nominal` (12 Q, réponse ancrée), `hors_corpus` (4 Q, refus attendu),
  `ambigu` (2 Q, prudence/clarification), `multi_doc` (2 Q, synthèse).
  Dernier `tests/rapport_fiabilite.md` : **16 PASS / 4 PARTIEL / 0 FAIL**.

## 7. Limites connues (à communiquer aux utilisateurs)

- Corpus RH uniquement, 5 documents — pas de temps réel, pas de données paie individuelles.
- Réponses limitées à 150 mots : pour le détail, ouvrir le PDF source cité.
- OCR des pages scannées imparfait (voir doc Développement) : une page mal
  scannée peut être introuvable.
- Seuil de pertinence strict par défaut : en cas de refus abusif, c'est un
  réglage (`SIMILARITY_THRESHOLD`), pas une faute de l'utilisateur — contacter la DRH.
