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
| `shacl_nrql_comparison_revised.pdf` | **Revised edition** of the comparison (PDF) — recommended. |
| `shacl_nrql_comparison_revised.tex` | LaTeX source for the revised edition. |
| `nrql_shacl_report_ai_declaration.pdf` | Original report (PDF). |
| `nrql_shacl_report_ai_declaration.tex` | LaTeX source for the original report. |

## Revised edition

The revised edition (`shacl_nrql_comparison_revised.*`) sharpens and corrects the
original in four ways:

1. **Priority grounded in the literature, not the vendor manual alone.** The
   epistemic / minimal-knowledge query idea was formalized by Donini et al.
   (1998) and crystallized as "effective first-order querying" by EQL-Lite
   (2007); nRQL (2004–2005) sits between them as, defensibly, the first
   *practical* engine combining negation as failure with projection over OWL.
   Contemporaries are named and contrasted (RQL 2002; RDQL Jan 2004, which had
   only "safe" negation).
2. **The vacuous "informal theorem" becomes an explicit reduction lemma** whose
   stated hypotheses *are* the boundary of what SHACL added.
3. **Two genuine novelties, with proof/citations, not one:** recursive shape
   conformance (a non-stratified fixpoint object with NP-hard validation and
   undecidable satisfiability/containment) and unbounded regular paths (provably
   outside the nonrecursive NAF+projection fragment, since transitive closure is
   not first-order definable).
4. **Honest calibration:** the unsupported "80%" figure and the property-graph
   priority claim are withdrawn; a new section covers three translation traps
   (epistemic-mode mismatch, counting without a unique-name assumption, and the
   active-domain-vs-anonymous-witness gap).

## Authorship

The original report was drafted by a generative AI system; the revised edition was
drafted by Claude (Opus 4.8) and substantiated against cited publications in the
description-logic and RDF-validation literature. Each report includes a Generative
AI authorship and independence declaration; see the reports for details.
