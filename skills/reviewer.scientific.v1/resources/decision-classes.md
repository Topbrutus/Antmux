# Classes de décision

## `ACCEPTED`

La source contient une preuve substantielle qui soutient directement le mécanisme décrit. L’application proposée respecte la portée de la source.

Conditions minimales :

- au moins un `source_line_id` valide;
- aucune contamination du pipeline;
- mécanisme explicitement soutenu;
- raison spécifique;
- `evidence_status: SUPPORTED`.

## `ANALOGY_ONLY`

La source décrit un phénomène réel, mais le transfert vers LinuxIA est une analogie ou une hypothèse expérimentale, pas un patron logiciel directement démontré.

États de preuve permis : `SUPPORTED` ou `PARTIAL`.

## `INSUFFICIENT_EVIDENCE`

Les lignes sont trop faibles, hors contexte, structurelles, incomplètes ou ne soutiennent pas l’affirmation.

États de preuve permis : `PARTIAL` ou `UNSUPPORTED`.

## `PIPELINE_METADATA_CONTAMINATION`

Le patron utilise comme preuve une information ajoutée par LinuxIA, le Worker, l’ingestion ou le stockage local, puis l’attribue incorrectement à la source.

État obligatoire : `CONTAMINATED`.

## `LOCAL_GUARDRAIL`

La règle est utile pour LinuxIA, mais elle a été ajoutée localement et ne constitue pas une découverte de la source.

La sortie doit identifier explicitement l’origine locale.

## Priorité en cas de plusieurs problèmes

1. `PIPELINE_METADATA_CONTAMINATION`;
2. `LOCAL_GUARDRAIL`;
3. `INSUFFICIENT_EVIDENCE`;
4. `ANALOGY_ONLY`;
5. `ACCEPTED`.

Cette priorité évite qu’un patron contaminé soit simplement présenté comme une analogie.
