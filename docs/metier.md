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

Interface actuelle : **application web React (Vite) + API FastAPI**.
L'ancienne maquette Streamlit a été retirée : tout le parcours ci-dessous décrit le frontend React.

## 2. Utilisateurs et cas d'usage

| Acteur | Besoin | Exemple de question |
|---|---|---|
| Agent ONEAD | Comprendre une procédure RH | « Comment fonctionne la gestion des absences ? », « Congés ? » |
| Nouvel arrivant | Se repérer dans les règles internes | « Quels actes pour un début de carrière ? » |
| DRH | Réduire les questions répétitives, repérer les manques du corpus | Revue de `data/feedback/unanswered.jsonl` |
| Mainteneur corpus | Savoir quelle base est en ligne | Sidebar « Base à jour · N docs » + date d'indexation (lue depuis `GET /api/manifest`) |

Parcours type :
accueil premium (`HomeHero.tsx` : logo ONEAD vectoriel + 4 cartes suggestions) →
question dans `Composer.tsx` → réponse streamée dans `ChatThread.tsx` avec
sources en lignes texte simples collées à la réponse →
clic sur une source = visionneuse PDF intégrée (`DocViewer.tsx`) à la page citée
ou ouverture blob dans un nouvel onglet (lecture garantie, sans téléchargement).

**Hors périmètre volontaire :** tout ce qui n'est pas dans le corpus RH
(montants de primes non documentés, recettes de cuisine, actualités, données
personnelles comme un numéro privé) → refus contrôlé (voir §5).

## 3. Corpus de référence (5 documents)

Source de vérité unique : les PDF de `data/raw/` (voir `data/manifest.json` —
indexation du **2026-10-08, 3201 chunks paginés**, embedding `text-embedding-3-large`) :

| Document | Contenu couvert | Poids (nouvelle indexation paginée) |
|---|---|---|
| `1543744461-Manuel_de_proc_dures_RH_de_lONEAD.pdf` | GPEC, prévention des risques / CHS, SIRH, évaluation annuelle, absences, congés, formation | 142 chunks |
| `MANUEL DE PROCEDURE DRH PME.pdf` | Missions DRH, service courrier, carrières, formation | 102 chunks |
| `MANUEL DE PROCEDURES EN RESSOURCES HUMAINES.pdf` | Harmonisation des procédures, actes de début de carrière | 102 chunks |
| `ORGANISATION INTERNATIONALE DU TRAVAIL.pdf` | Référentiel OIT (formation, normes) | 1890 chunks |
| `pub-2020001249601F-mca-human-resources-f.pdf` | Recrutement, code de conduite, évaluation MCA | 965 chunks |

Total : **3201 chunks** (remplace l'ancien comptage 5282 chunks non paginés du 2026-10-05 —
si un document métier cite encore 5282, le mettre à jour vers 3201).

Règle : **si ce n'est pas dans ces 5 documents, l'assistant ne doit pas répondre.**

## 4. Contrat de réponse (règles métier)

Défini dans `chat_context.py:build_prompt` et `src/config.py` :

- Répond **uniquement** à partir du contexte récupéré (top-5 passages ChromaDB, `TOP_K=5`).
- Langue : **français uniquement**.
- Longueur : **50–150 mots max**.
- Ton : professionnel, direct, empathique. Listes à puces si plusieurs éléments.
- **Ne cite pas les sources dans le texte** : c'est le frontend qui affiche sous chaque
  réponse des lignes `Source : <nom.pdf> — p. N` (`frontend/src/components/ChatThread.tsx:104-119`,
  capées à `MAX_SOURCES=3`, dédoublonnées par couple document/page, avec extrait de 280 car.
  visible dans la visionneuse `DocViewer.tsx:139-144`).
- Première interaction : message de bienvenue unique ; jamais de re-bonjour ensuite.
- Zéro politesse excessive, zéro répétition, zéro emoji (SVG monochromes uniquement).

## 5. Refus contrôlé + recours DRH

Quand aucun passage pertinent n'est récupéré (filtre par seuil, voir doc
Développement) ou que le modèle émet le message de refus, le système
(`api.py:_answer_sync` + `chat_stream`, `chat_context.py:is_refusal`, `frontend/src/App.tsx:164` + `ChatThread.tsx:126-140`) :

1. Affiche le message unique (`src/config.py:36-39`) :
   > « Je n'ai pas trouvé cette information dans les documents disponibles.
   > Veuillez consulter la DRH ou le manuel de procédures correspondant. »
2. Affiche la carte **Recours DRH** (`src/config.py:41-46`, `GET /api/drh`) :
   Direction des Ressources Humaines — ONEAD, `drh@onead.dj`,
   `+253 21 35 00 00`, Dim–Jeu 8h–17h (surchageable via `DRH_EMAIL` / `DRH_TEL`).
3. Journalise la question dans `data/feedback/unanswered.jsonl`
   (`chat_context.py:log_unanswered`) pour revue DRH et affiche côté frontend
   la notification « Question transmise pour revue DRH. ».

Ce fichier est le **capteur d'amélioration continue** : questions fréquentes
sans réponse = documents à ajouter ou à clarifier.

## 6. Traçabilité et confiance

- **Sidebar « Base documentaire »** (React `Sidebar.tsx:58-78`, alimentée par
  `GET /api/manifest` + `GET /api/documents`) : mention `Base à jour · N docs`,
  date d'indexation, nb documents/chunks, modèle d'embedding — lus depuis
  `data/manifest.json` (généré par `src/indexation.py:109-126`, avec SHA-256
  16 hex par fichier, chemin `db_dir` relatif et portable).
- **Sources cliquables** : boutons `Source : nom — p. N` → modale `DocViewer.tsx`
  (pdfjs-dist, badge `Page N`, extrait cité, navigation pages/zoom, `Échap`/flèches,
  bouton `Page citée`) + ouverture blob `…#page=N` dans un nouvel onglet
  (`ChatThread.tsx:openDoc`, jamais de téléchargement forcé, repli navigation directe).
  URLs servies par le backend : `GET /files/docs/{nom}` depuis `data/raw/` (`inline`, RFC 5987).
- **Thèmes et lisibilité** : logo ONEAD 100 % vectoriel sans fond ni cadre
  (`OneadLogo.tsx`, lisible sombre/clair), `HomeHero` sans sous-titre redondant,
  animation d'écriture limitée à la réponse en cours (`streamingId`), historique
  sans préfixes `●`/`○`.
- **Évaluation** : `tests/20_questions.csv` couvre 4 scénarios —
  `nominal` (12 Q, réponse ancrée), `hors_corpus` (4 Q, refus attendu),
  `ambigu` (2 Q, prudence/clarification), `multi_doc` (2 Q, synthèse).
  Dernier `tests/rapport_fiabilite.md` archivé : **15 PASS / 5 PARTIEL / 0 FAIL**,
  régénéré sur la base courante du 2026-10-08 (3201 chunks, `text-embedding-3-large`).
  Les 5 PARTIEL concernent des questions nominales dont le document attendu n'apparaît
  pas dans les passages récupérés (critère lexical de l'éval offline).

## 7. Limites connues (à communiquer aux utilisateurs)

- Corpus RH uniquement, 5 documents — pas de temps réel, pas de données paie individuelles.
- Réponses limitées à 150 mots : pour le détail, ouvrir le PDF source cité (visionneuse intégrée).
- OCR des pages scannées imparfait (voir doc Développement) : une page mal
  scannée peut être introuvable.
- Seuil de pertinence strict par défaut (`SIMILARITY_THRESHOLD=1.0`, permissif ; baisser = plus strict) :
  en cas de refus abusif, c'est un réglage, pas une faute de l'utilisateur — contacter la DRH.
- Au premier démarrage du backend, `GET /api/health` peut indiquer `rag_loaded: false`
  le temps du pré-chargement en tâche de fond (`lifespan`) — la première question charge ensuite la base.
