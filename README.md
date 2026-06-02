# SHACL, Racer nRQL, and Property Graphs: What Was Conceptually New — and What Came First?

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

## Two investigations

This repository hosts two related historical-semantic threads:

**1. What was conceptually new in SHACL?** (the report above) — comparing SHACL
validation against what RacerPro's nRQL, negation-as-failure, rules, and the
data/mirror substrate could already express by ~2005.

**2. Where does the property-graph (PG) data model actually come from?** — a
second thread, prompted by the observation that RacerPro's **data substrate**
(2005) is *itself* a property graph: `data-node` / `data-edge` give **both** nodes
and edges first-class, queryable key-value property maps, and the substrate is
distinctively *coupled to a description-logic reasoner* (node types are OWL
concepts, edge labels are roles with inverses). Was this an early, forgotten PG —
and when did the PG model first appear in recognizable, *graphs-not-tables* form?

**Calibrated verdict** (paper §11, with `pgraph-example.jpeg` as a worked RacerPro
2.0 session): the attributed-graph *model* long predates Racer — Kuper–Vardi's
Logical Data Model (1984), the GOOD and hypernode models (1990), Güting's GraphDB
(1994) — while the *term* "property graph" was coined in 2010 (Rodriguez &
Neubauer) and the standards (ISO GQL, SQL/PGQ) arrived in 2023–24. So Racer's
substrate is **not** the first PG and shows **no** documented influence on
Neo4j/Cypher/GQL — convergent evolution, not lineage. What *is* genuinely early,
and as far as we can find without prior or contemporary peer, is the combination:
a queryable **property graph fused with a tableau DL/OWL reasoner**. Both threads
use the same discipline — separating *prior art* and *conceptual convergence* from
*documented influence*, crediting only what the sources support.

## Contents

| File | Description |
| --- | --- |
| `shacl_nrql_comparison_revised.pdf` | **Revised edition** of the comparison (PDF) — recommended. |
| `shacl_nrql_comparison_revised.tex` | LaTeX source for the revised edition. |
| `code_shacl_test_suite.py` | Reproducible coding of the W3C SHACL test suite against the paper's Table 1. |
| `shacl_test_suite_coding.csv` | Per-file audit trail for the coding (95 SHACL Core tests). |
| `pgraph-example.jpeg` | A property graph (bank accounts + a `deposit` edge with `:amount`/`:currency`) built and queried in RacerPro 2.0 — evidence for investigation 2. |
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
4. **Honest calibration:** the unsupported "80%" figure is withdrawn (replaced by
   a measured band); a new section covers three translation traps (epistemic-mode
   mismatch, counting without a unique-name assumption, and the
   active-domain-vs-anonymous-witness gap).

The revised edition also **corrects** an earlier wrong call on property graphs.
The RacerPro **data substrate** is a genuine property graph — `data-node` /
`data-edge` give *both* nodes and edges first-class, queryable key-value property
maps (see `pgraph-example.jpeg`, a live RacerPro 2.0 session modeling bank
accounts and a `deposit` edge with `:amount`/`:currency`, queried by nRQL on edge
properties). Distinctively, it is a property graph *coupled to a DL reasoner*
(node types = OWL concepts, edge labels = roles with inverses). Calibrated
verdict: real, early (2005), reasoning-coupled prior art — but **not** the first
attributed-graph model (those go back to Kuper–Vardi 1984, GOOD/hypernode 1990,
Güting's GraphDB 1994) and with **no** documented influence on Neo4j/Cypher/GQL.
Convergent evolution, not lineage. See the paper's §11.

## Empirical result

**Headline (reframed from the old "80%"):** roughly **73–84% of SHACL Core
constraint features have a direct nRQL counterpart** (≈92% once the substrate
mirror is granted), while the **provably-native residual is only ~5% — entirely
unbounded or recursive property paths** (best single estimate ~8% once you add
`sh:pattern` regexes, which RacerPro can't do *declaratively* — see the tier
caveat below). The width of the band is set by
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
**3 are `sh:pattern` tests needing real regex** (RacerPro's *declarative* fragment
has only `string=` / `string<>` and substrate substring `search`, no regex engine).

**Important tier caveat.** Those numbers describe the *declarative* fragment. nRQL
also has a **lambda + `:reject` escape hatch** — arbitrary server-side Common Lisp
filter predicates (User's Guide pp. 146–148) — which is the exact analogue of
**SHACL-SPARQL** and **SHACL-JS**. A lambda calling a CL regex library implements
full `sh:pattern`; via a hand-coded traversal it can even compute unbounded paths.
So relative to *full* nRQL the 3 regex tests vanish and only the 4 paths resist —
and even those only *declaratively*. Both languages carry a Turing-complete escape
hatch, so at that tier the expressivity residual collapses to **zero**; what
genuinely survives is SHACL's recursive **conformance semantics** and **report
model**, not expressivity. (See the paper's §5.5.)

Reproduce with `python3 code_shacl_test_suite.py` after cloning `w3c/data-shapes`.
Caveat: this measures feature *coverage*, not real-world deployment *frequency* —
the complementary study is a corpus of deployed shapes graphs.

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
| `nodeKind-001` | focus node `sh:nodeKind sh:IRI` | **No native declarative primitive** for RDF term kind — encode it as a substrate label and test with `(:predicate (equalp …))`, or use a `lambda`/`:reject` filter that inspects the term (the SHACL-SPARQL-style hatch) | **C** |
| `closed-001` | `sh:closed true`, only `ex:someProperty` allowed | `(retrieve (?*x ?*y) (and (?*x ?*y `_‹any-edge›_`) (neg (?*x ?*y (:predicate (equalp someProperty))))))` — `:predicate (equalp …)` is real (p. 137); needs the mirror to expose predicate labels on edges | **C** |
| `qualifiedValueShape-001` | `ex:related` `sh:qualifiedMinCount 3` of shape `Q` | `(retrieve (?x) (neg (project-to (?x) (and (?x $?a related) (substitute (Q $?a)) (?x $?b related) (substitute (Q $?b)) (?x $?c related) (substitute (Q $?c)) (neg (same-as $?a $?b)) (neg (same-as $?a $?c)) (neg (same-as $?b $?c))))))` — `Q` is a `defquery`; the 3-distinct idiom is verbatim from p. 100 | **E** |
| `path-zeroOrMore-001` | `[ sh:zeroOrMorePath ex:child ]` `sh:minCount 2` | **No nonrecursive nRQL query exists** — the EBNF `<query-body>` (pp. 152–153) has *no* transitive-closure / regular-path operator. Recover via a transitive role, a recursive `firerule`, or precomputed substrate closure | **N** |

¹ For the string-valued `firstName`, distinctness is over told datatype fillers, not ABox individuals; `same-as` ranges over `<abox-query-object>`s (grammar, p. 153).
² RacerPro datatype attributes carry a declared type, so datatype conformance is enforced by the concrete domain; the exact predicate depends on the mirror encoding.
³ RacerPro's *declarative* concrete domain offers only `string=` / `string<>` (pp. 63–64) and the substrate substring `search` (p. 137) — no regex. But nRQL's **lambda + `:reject`** facility (pp. 146–148) defines arbitrary server-side Common Lisp filter predicates, so a lambda calling a CL regex library *does* implement full `sh:pattern` — the analogue of a SHACL-SPARQL `FILTER regex(…)`. So regex is a *declarative-core* gap, closed by the escape hatch (paper §5.5).

**The grammar settles the one hard *declarative* case.** The EBNF for `<query-body>`
and `<abox-query-atom>` (User's Guide pp. 152–153) provides conjunction,
disjunction, `neg`, `project-to`, `same-as`, `has-known-successor`, and
concrete-domain/substrate `:predicate`s — but **no transitive-closure or
regular-path operator**. So the **N** path rows are not an artifact of the coding
scheme: unbounded reachability is absent from the *declarative* nRQL language *by
construction* — exactly Proposition 1, confirmed from the language definition.
(The lambda hatch can still *compute* reachability imperatively; what SHACL Core
uniquely offers is regular paths as a *declarative* primitive.)

## Authorship

The original report was drafted by a generative AI system; the revised edition was
drafted by Claude (Opus 4.8) and substantiated against cited publications in the
description-logic and RDF-validation literature. Each report includes a Generative
AI authorship and independence declaration; see the reports for details.
