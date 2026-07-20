# Règles de preuve

## Preuve substantielle

Une preuve substantielle contient une affirmation, une description de mécanisme, une procédure, une contrainte, un résultat ou une relation explicitement exprimée par la source.

## Éléments insuffisants seuls

Les éléments suivants ne suffisent jamais seuls :

- titre ou sous-titre;
- ligne vide;
- séparateur Markdown;
- début ou fin de tableau sans contenu;
- nom de dossier;
- simple nom de technologie;
- identifiant sans explication;
- phrase tronquée;
- métadonnée ajoutée pendant l’ingestion.

## Correspondance mécanisme-preuve

La preuve doit soutenir le mécanisme exact du patron. Une ligne mentionnant « validation » ne prouve pas automatiquement :

- une interface de validation;
- un Reviewer indépendant;
- une validation humaine;
- une validation automatique complète.

## Portée

L’application LinuxIA ne doit pas dépasser la portée de la source. Une source biologique peut inspirer une expérience, mais elle ne démontre pas automatiquement une architecture logicielle.

## Contamination du pipeline

Sont considérés comme contamination lorsqu’ils sont attribués à la source :

- SHA-256 calculé localement;
- date d’ingestion;
- chemin local;
- annotation LinuxIA;
- garde-fou ajouté par le Worker;
- classe ou risque produit par un fallback;
- texte généré dans le dossier d’analyse.

## Provenance

Chaque conclusion doit conserver :

- `source_id`;
- `source_line_ids`;
- empreinte SHA-256 de la source;
- identifiant du patron;
- identifiant du Reviewer;
- date UTC;
- version du protocole.

## Risque

Le champ `risk_assessment` doit être spécifique au patron. Une formule générique répétée ne constitue pas une analyse.

## Règle conservatrice

Lorsque la preuve est partielle ou ambiguë, ne pas compléter avec des connaissances externes. Classer `INSUFFICIENT_EVIDENCE` ou `ANALOGY_ONLY` selon la nature du problème.
