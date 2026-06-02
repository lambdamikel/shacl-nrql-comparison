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

**Headline (reframed from the old "80%"):** roughly **73–84% of SHACL Core
constraint features have a direct nRQL counterpart** (≈92% once the substrate
mirror is granted), while the **provably-native residual is only ~5% — entirely
unbounded or recursive property paths** (best single estimate ~8% once you add
`sh:pattern` regexes, which RacerPro can't do). The width of the band is set by
how much RDF-term/lexical structure you assume mirrored; that dependence on
assumptions is the honest replacement for a single number. The old "80%" sits
inside the direct-expressible band as a plausible midpoint — which is why it felt
right but was the wrong *kind* of statement (a point estimate instead of a band).

This comes from coding the official W3C SHACL test suite (the 2017
`data-shapes-test-suite`) against the paper's Table 1. Of the 83 SHACL **Core
constraint** tests:

| Bucket | Meaning | Share |
| --- | --- | --- |
| **E** | direct nRQL counterpart | 73.5% |
| **C** | conditional on mirroring, or with a documented caveat | 18.1% |
| **N** | genuinely native to SHACL | 8.4% |

Of the 7 **N** tests, **4 are unbounded/recursive property paths** — provably
native (Proposition 1: transitive closure is not first-order definable) — and
**3 are `sh:pattern` tests needing real regex** (RacerPro has only `string=` /
`string<>` and substrate substring `search`, no regex engine). Reproduce with
`python3 code_shacl_test_suite.py` after cloning `w3c/data-shapes`. Caveat: this
measures feature *coverage*, not real-world deployment *frequency* — the
complementary study is a corpus of deployed shapes graphs.

## Illustrative SHACL → nRQL translations

Each row pairs an **actual W3C test case** with a faithful nRQL *violation* query
(one that returns the non-conforming focus nodes — nRQL's natural way to express a
constraint is "a query whose answers are the violations"). Queries assume a fixed
entailment regime and, where noted, the substrate mirror. **All nRQL syntax below
is verified against the RacerPro _User's Guide 2.0_ — §4.1.9 "Formal Syntax of
nRQL" (printed pp. 150–153) and the mirror-substrate section (pp. 137–143).**
Grammar conventions: `?x` is an _injective_ ABox variable, `$?x` non-injective,
`?*x` a substrate variable; `(:predicate …)` and `:satisfies` are substrate
predicate forms; `:owl-datatype-value` / `:owl-datatype-role` are real mirror
markers (p. 141). Buckets are **E** (direct), **C** (conditional/lossy), **N**
(native to SHACL).

| W3C test case | SHACL constraint | nRQL violation query | Bucket |
| --- | --- | --- | --- |
| `minCount-001` | `ex:firstName` `sh:minCount 1` on class `ex:Person` | `(retrieve (?x) (and (?x Person) (neg (project-to (?x) (?x ?y firstName)))))` — equivalently the manual's `(neg (?x (has-known-successor firstName)))` (p. 100) | **E** |
| `class-001` | focus node must be `sh:class ex:Person` | `(retrieve (?x) (neg (?x Person)))` — `(?x Person)` is entailment-aware: a `MalePerson ⊑ Person` conforms, an `Animal` is returned as a violation | **E** |
| `maxCount-001` | `ex:firstName` `sh:maxCount 1` | `(retrieve (?x) (and (?x Person) (?x $?y1 firstName) (?x $?y2 firstName) (neg (same-as $?y1 $?y2))))` — `same-as` + non-injective `$?` vars (pp. 85, 153); counts *known individuals*, not RDF terms (no UNA) ¹ | **C** |
| `datatype-002` | `ex:value` `sh:datatype xsd:string` | enforced by concrete-domain typing — `(define-concrete-domain-attribute value :type string)` makes a non-string filler unassertable/queryable; or test the mirrored `:owl-datatype-value` node ² | **E** |
| `pattern-001` | `ex:property` `sh:pattern "Joh"` | `(retrieve (?x) (and (?x ?y property) (neg (?y (:predicate (search "Joh"))))))` — `(:predicate (search …))` is **substring** search (p. 137) ³ | **C** |
| `nodeKind-001` | focus node `sh:nodeKind sh:IRI` | **No native primitive** for RDF term kind. Expressible only by encoding term kind as a substrate label and testing it with `(:predicate (equalp …))` | **C** |
| `closed-001` | `sh:closed true`, only `ex:someProperty` allowed | `(retrieve (?*x ?*y) (and (?*x ?*y `_‹any-edge›_`) (neg (?*x ?*y (:predicate (equalp someProperty))))))` — `:predicate (equalp …)` is real (p. 137); needs the mirror to expose predicate labels on edges | **C** |
| `qualifiedValueShape-001` | `ex:related` `sh:qualifiedMinCount 3` of shape `Q` | `(retrieve (?x) (neg (project-to (?x) (and (?x $?a related) (substitute (Q $?a)) (?x $?b related) (substitute (Q $?b)) (?x $?c related) (substitute (Q $?c)) (neg (same-as $?a $?b)) (neg (same-as $?a $?c)) (neg (same-as $?b $?c))))))` — `Q` is a `defquery`; the 3-distinct idiom is verbatim from p. 100 | **E** |
| `path-zeroOrMore-001` | `[ sh:zeroOrMorePath ex:child ]` `sh:minCount 2` | **No nonrecursive nRQL query exists** — the EBNF `<query-body>` (pp. 152–153) has *no* transitive-closure / regular-path operator. Recover via a transitive role, a recursive `firerule`, or precomputed substrate closure | **N** |

¹ For the string-valued `firstName`, distinctness is over told datatype fillers, not ABox individuals; `same-as` ranges over `<abox-query-object>`s (grammar, p. 153).
² RacerPro datatype attributes carry a declared type, so datatype conformance is enforced by the concrete domain; the exact predicate depends on the mirror encoding.
³ **Correction to the earlier draft:** RacerPro's concrete domain offers only `string=` / `string<>` (pp. 63–64) and the substrate offers substring `search` (p. 137) — **there is no regex**. Full `sh:pattern` regexes are a genuine gap, which is why `pattern` and `nodeKind` sit at the native-leaning (pessimistic) end of the §10.3 band.

**The grammar settles the one hard case.** The EBNF for `<query-body>` and
`<abox-query-atom>` (User's Guide pp. 152–153) provides conjunction, disjunction,
`neg`, `project-to`, `same-as`, `has-known-successor`, and concrete-domain/substrate
`:predicate`s — but **no transitive-closure or regular-path operator**. So the
single **N** row is not an artifact of the coding scheme: unbounded reachability is
absent from the nRQL language *by construction* — which is exactly Proposition 1,
now confirmed from the language definition itself.

## Authorship

The original report was drafted by a generative AI system; the revised edition was
drafted by Claude (Opus 4.8) and substantiated against cited publications in the
description-logic and RDF-validation literature. Each report includes a Generative
AI authorship and independence declaration; see the reports for details.
