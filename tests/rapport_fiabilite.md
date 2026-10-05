# Rapport de fiabilité — ONEAD Assistant RAG

Questions testées : **20** — PASS : **16** / PARTIEL : **4** / FAIL : **0**

## Traçabilité de la base (reco #2)

- Date d'indexation : 2026-10-05
- Documents : 5 | Chunks : 5282
- Modèle d'embedding : text-embedding-3-large (à confirmer via indexation.py)

## Résultats par scénario (reco #4)

| ID | Catégorie | Statut | Détail | Passages |
|----|-----------|--------|--------|----------|
| Q01 | nominal | PARTIEL | sources trouvées : ['organisation internationale du travail.pdf', 'pub-202000124 | 5 |
| Q02 | nominal | PASS | source attendue retrouvée (1543744461-Manuel_de_proc_dures_RH_de_lONEAD.pdf) | 5 |
| Q03 | nominal | PARTIEL | sources trouvées : ['organisation internationale du travail.pdf', 'pub-202000124 | 5 |
| Q04 | nominal | PASS | source attendue retrouvée (1543744461-Manuel_de_proc_dures_RH_de_lONEAD.pdf) | 5 |
| Q05 | nominal | PASS | source attendue retrouvée (MANUEL DE PROCEDURE DRH PME.pdf) | 5 |
| Q06 | nominal | PASS | source attendue retrouvée (MANUEL DE PROCEDURE DRH PME.pdf) | 5 |
| Q07 | nominal | PASS | source attendue retrouvée (MANUEL DE PROCEDURE DRH PME.pdf) | 5 |
| Q08 | nominal | PARTIEL | sources trouvées : ['1543744461-manuel_de_proc_dures_rh_de_lonead.pdf', 'manuel  | 5 |
| Q09 | nominal | PASS | source attendue retrouvée (MANUEL DE PROCEDURES EN RESSOURCES HUMAINES.pdf) | 5 |
| Q10 | nominal | PASS | source attendue retrouvée (MANUEL DE PROCEDURES EN RESSOURCES HUMAINES.pdf) | 5 |
| Q11 | nominal | PASS | source attendue retrouvée (pub-2020001249601F-mca-human-resources-f.pdf) | 5 |
| Q12 | nominal | PASS | source attendue retrouvée (pub-2020001249601F-mca-human-resources-f.pdf) | 5 |
| Q13 | hors_corpus | PASS | refus contrôlé malgré 5 match(s) faible(s) — renvoi DRH | 5 |
| Q14 | hors_corpus | PASS | refus contrôlé malgré 5 match(s) faible(s) — renvoi DRH | 5 |
| Q15 | hors_corpus | PASS | refus contrôlé malgré 5 match(s) faible(s) — renvoi DRH | 5 |
| Q16 | hors_corpus | PASS | refus contrôlé malgré 5 match(s) faible(s) — renvoi DRH | 5 |
| Q17 | ambigu | PASS | 5 passage(s) — clarification attendue sans hallucination | 5 |
| Q18 | ambigu | PASS | 5 passage(s) — clarification attendue sans hallucination | 5 |
| Q19 | multi_doc | PARTIEL | 1 source(s) distincte(s) : ['ORGANISATION INTERNATIONALE DU TRAVAIL.pdf'] | 5 |
| Q20 | multi_doc | PASS | 2 source(s) distincte(s) : ['ORGANISATION INTERNATIONALE DU TRAVAIL.pdf', 'pub-2 | 5 |

## Validation des réponses (reco #1)

- Refus contrôlé détecté via `is_refusal()` sur le message unique de `src/config.py`.
- Audit `validate_response()` : réponse valide seulement si passages + sources traçables.

## Recours DRH (reco #3)

- Message de refus unique + carte contact DRH dans `app.py`.
- Journalisation `data/feedback/unanswered.jsonl` via `log_unanswered()`.

_Rapport généré en mode offline (retrieval lexical). Relancez avec `--with-llm` pour le test ChromaDB + Azure._