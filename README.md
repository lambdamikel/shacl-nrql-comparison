# SHACL and Racer nRQL: What Was Conceptually New?

A semantic comparison of [SHACL](https://www.w3.org/TR/shacl/) validation with
RacerPro's **nRQL** query language, the OWL/Data Mirroring Substrate, the
substrate representation layer, and hybrid nRQL queries.

## Summary

This report asks a deliberately narrow, conceptual question: what did SHACL make
expressible as a constraint language that was *not* already expressible, in
principle, in RacerPro via nRQL plus its substrate and mirroring machinery?

The main conclusion is that for OWL-centric integrity constraints over finite,
explicitly represented data, very little in SHACL is fundamentally new at the
level of constraint expressivity. nRQL already provided closed-world violation
queries over an open-world OWL knowledge base by combining DL-aware positive
atoms with negation as failure, projection, aggregation, rules,
concrete-domain/datatype predicates, complex TBox queries, and hybrid substrate
atoms.

The genuinely new or partially new contributions of SHACL are mostly:

1. a first-class shape-conformance relation over RDF graphs;
2. RDF term and graph structure as the primitive validation universe;
3. built-in regular property-path evaluation over the raw RDF graph; and
4. (when SHACL-SPARQL is admitted) the imported SPARQL algebra and vocabulary.

## Contents

| File | Description |
| --- | --- |
| `nrql_shacl_report_ai_declaration.pdf` | The compiled report (PDF). |
| `nrql_shacl_report_ai_declaration.tex` | LaTeX source for the report. |

## Authorship

The report was authored by a generative AI system (OpenAI GPT-5.5 Pro) from the
RacerPro manuals and the SHACL specifications. It includes a Generative AI
authorship and independence declaration; see the report for details.
