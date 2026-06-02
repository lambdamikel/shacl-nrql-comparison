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
| `code_shacl_test_suite.py` | Reproducible coding of the W3C SHACL test suite against the paper's Table 1. |
| `shacl_test_suite_coding.csv` | Per-file audit trail for the coding (95 SHACL Core tests). |
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

## Empirical result

**Headline (reframed from the old "80%"):** roughly **74–88% of SHACL Core
constraint features have a direct nRQL counterpart** (≈95% once the substrate
mirror is granted), while the **provably-native residual is only ~5% — and is
entirely unbounded or recursive property paths**. The width of the band is set by
how much RDF-term/lexical structure you assume mirrored; that dependence on
assumptions is the honest replacement for a single number. The old "80%" sits
inside the band as a plausible midpoint — which is why it felt right but was the
wrong *kind* of statement (a point estimate instead of a band).

This comes from coding the official W3C SHACL test suite (the 2017
`data-shapes-test-suite`) against the paper's Table 1. Of the 83 SHACL **Core
constraint** tests:

| Bucket | Meaning | Share |
| --- | --- | --- |
| **E** | direct nRQL counterpart | 73.5% |
| **C** | conditional on mirroring, or with a documented caveat | 21.7% |
| **N** | genuinely native to SHACL (unbounded / recursive paths) | 4.8% |

All four **N** tests are unbounded or recursive property paths — exactly the
category the paper's Proposition 1 isolates analytically (transitive closure is
not first-order definable). Reproduce with `python3 code_shacl_test_suite.py`
after cloning `w3c/data-shapes`. Caveat: this measures feature *coverage*, not
real-world deployment *frequency* — the complementary study is a corpus of
deployed shapes graphs.

## Illustrative SHACL → nRQL translations

Each row pairs an **actual W3C test case** with a faithful nRQL *violation* query
(one that returns the non-conforming focus nodes — nRQL's natural way to express a
constraint is "a query whose answers are the violations"). Queries assume a fixed
entailment regime and, where noted, a faithful substrate mirror; markers like
`:owl-datatype-value` and `:node-kind` are schematic substrate labels. Buckets are
**E** (direct), **C** (conditional/lossy), **N** (native to SHACL).

| W3C test case | SHACL constraint | nRQL violation query | Bucket |
| --- | --- | --- | --- |
| `minCount-001` | `ex:firstName` `sh:minCount 1` on class `ex:Person` | `(retrieve (?x) (and (?x Person) (neg (project-to (?x) (?x ?y firstName)))))` | **E** |
| `class-001` | focus node must be `sh:class ex:Person` | `(retrieve (?x) (neg (?x Person)))` — `(?x Person)` is entailment-aware: a `MalePerson ⊑ Person` conforms, an `Animal` is returned as a violation | **E** |
| `maxCount-001` | `ex:firstName` `sh:maxCount 1` | `(retrieve (?x) (and (?x Person) (?x ?y1 firstName) (?x ?y2 firstName) (neg (same-as ?y1 ?y2))))` — needs explicit distinctness; counts *known individuals*, not RDF terms (no unique-name assumption) | **C** |
| `datatype-002` | `ex:value` `sh:datatype xsd:string` | `(retrieve (?x) (and (?x ?y value) (neg (?y (:owl-datatype-value string)))))` — returns `"A"@en` (an `rdf:langString`) and `42` (an integer) | **E** |
| `pattern-001` | `ex:property` `sh:pattern "Joh"` | `(retrieve (?x) (and (?x ?y property) (neg (substring-search ?y "Joh"))))` — substrate string predicate (the manual documents substring search) | **C** |
| `nodeKind-001` | focus node `sh:nodeKind sh:IRI` | `(retrieve (?*x) (neg (?*x (:node-kind :iri))))` — expressible **only if** term kind is mirrored as substrate data | **C** |
| `closed-001` | `sh:closed true`, only `ex:someProperty` allowed | `(retrieve (?*x ?*y) (and (?*x ?*y (:abox-relationship)) (neg (?*x ?*y (:predicate (equalp ex:someProperty))))))` — needs predicate labels in the substrate | **C** |
| `qualifiedValueShape-001` | `ex:related` `sh:qualifiedMinCount 3` of nested shape `Q` | `(retrieve (?x) (neg (project-to (?x) (and (?x ?a related) (Q ?a) (?x ?b related) (Q ?b) (?x ?c related) (Q ?c) (neg (same-as ?a ?b)) (neg (same-as ?a ?c)) (neg (same-as ?b ?c))))))` — `Q` abbreviates the nested body; requires 3 pairwise-distinct qualified values | **E** |
| `path-zeroOrMore-001` | `[ sh:zeroOrMorePath ex:child ]` `sh:minCount 2` | **No nonrecursive nRQL query exists** (Proposition 1). Recover only by declaring `ex:child` transitive in the TBox, or a recursive rule materializing `child*`, then querying the materialized relation | **N** |

The pattern is visible in the table: the **E**/**C** rows are routine
NAF-over-projection idioms (with the documented caveats), and the single **N** row
is exactly an unbounded path — the one place where no nonrecursive nRQL query can
match SHACL, which is the analytical result the paper proves.

## Authorship

The original report was drafted by a generative AI system; the revised edition was
drafted by Claude (Opus 4.8) and substantiated against cited publications in the
description-logic and RDF-validation literature. Each report includes a Generative
AI authorship and independence declaration; see the reports for details.
