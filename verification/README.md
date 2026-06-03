# Execution check on a live RacerPro 2.0 server

The paper's nRQL idioms were *grammar*-verified against the manual; this folder
takes them one step further and **runs them on a real RacerPro 2.0 reasoner**.

## How to reproduce

1. Get the RacerPro 2.0 binaries from **[lambdamikel/RacerPorter](https://github.com/lambdamikel/RacerPorter)** →
   `racer_binaries/<platform>/RacerPro-2-0/acl-mlisp/` (e.g. `linux64`).
2. Start the server (listens on TCP **8088**, HTTP 8080, control 8089):
   ```sh
   cd .../acl-mlisp && LD_LIBRARY_PATH="$PWD" ./RacerPro
   ```
3. **One command checks everything** — `run_all.py` runs the key query behind
   every claim and *asserts* the expected result (exit 0 iff all pass):
   ```sh
   python3 run_all.py
   # PASS  minCount: missing firstName -> carol
   # ...
   # 16/16 checks passed
   ```
   Or run the individual, fully-commented demos:
   ```sh
   python3 racer_queries.py        # card examples 1 & 2 + the property-graph session
   python3 translation_check.py    # rest of Table 1 + the §6.3 open/closed-world trap
   python3 reasoning_demos.py      # §9: what SHACL can't do (classification, rules, query reasoning)
   python3 owl_classification.py   # load + classify a real OWL file (pets.owl)
   python3 minilisp_probe.py       # characterizes the lambda/:reject "MiniLisp" hatch
   ```

The socket protocol is line-based: send `"<command>\n"`, read one CR-terminated
frame `:answer <id> "<result>" "<stdout>"`.

> **All 16 assertions in `run_all.py` pass** against the RacerPro 2.0 (2013-06-16)
> binary — the report's execution-verified claims reproduce end to end.

## Results (verbatim from RacerPro 2.0, 2013-06-16 build)

### 1. `sh:minCount 1` — missing required value (card Example 1)
```lisp
(retrieve (?x) (and (?x Person) (neg (project-to (?x) (?x ?y has-firstname)))))
=> (((?x carol)))        ; carol is the only Person with no firstName
```

### 2. `sh:class` — every value a Person, **with DL entailment** (card Example 2)
`MalePerson ⊑ Person`; `c1` is asserted only as a `MalePerson`, `c2` as an `Animal`.
```lisp
(individual-instance? c1 Person)  => t      ; INFERRED Person (not told)
(individual-instance? c2 Person)  => nil
(retrieve (?x) (and (?x Parent) (?x ?y has-child) (neg (?y Person))))
=> (((?x p2)))           ; only p2 flagged; p1 PASSES because its child is an inferred Person
```
This is the differentiator over plain graph validation, confirmed by the reasoner.

### 3. Property graph — fintech data substrate (Figure 1 / §11)
Edges carry their own key–value property maps; queries filter on **node and edge**
properties and traverse the `deposit`/`withdrawal` inverse — reproduced exactly:
```lisp
(data-edge acc1 acc2 ((:amount 9900.00) (:currency $)) deposit)   ; edge property map
(retrieve (?x) (and (?x account) (?*x ((:currency $) (:amount (:predicate (> 10000)))))))
=> (((?x acc2)))
(retrieve (?x ?y) (and (?x account) (?*x ((:amount (:predicate (> 10000)))))
                       (?x ?y withdrawal) (?*y ?*x ((:amount (:predicate (> 5000)))))))
=> (((?x acc2) (?y acc1)))     ; suspicious withdrawal: > 5000 predicate on the EDGE amount
(node-label acc2) => ((:amount 19000.0) (:currency $) (:number 2090))
(retrieve (?*x) (and (?*x ((:number 10039))) (neg (same-as ?*x *acc1)))) => (((?*x acc3)))
```

## Translation-table idioms + the §6.3 trap — `translation_check.py`

The rest of Table 1, plus the open-world/closed-world trap, run live:

| SHACL | nRQL violation query | Result |
| --- | --- | --- |
| `sh:maxCount 1` | two `firstName` fillers not known-equal | `alice` (over-reports without UNA) |
| `sh:qualifiedMinCount 1` `[sh:class Child]` | `(neg (project-to (?x) (and (?x ?y has-child) (?y Child))))` | `p2` |
| `sh:disjoint` | `(and (?x ?v likes) (?x ?v dislikes))` (shared value) | `x` |
| `sh:pattern "Joh"` (substring) | `(?*x (:predicate (search "Joh")))` on mirrored told values | `"Johann"` |

**The §6.3 crux — open world vs closed world.** With `parent ⊑ ∃has-child.⊤`,
`alice` is a parent with **no named child**, `bob` a parent with a told child:

```lisp
(individual-instance? alice (some has-child top))  => t     ; alice IS entailed to have a child
(retrieve (?x) (?x (has-known-successor has-child))) => bob  ; but has no KNOWN child
(retrieve (?x) (and (?x parent) (neg (?x (has-known-successor has-child))))) => alice
```

The same individual **satisfies the OWL existential and fails the closed-world
`minCount` check** — exactly the local-closed-world-over-open-world idiom the whole
comparison is about.

## Reasoning demos — `reasoning_demos.py` (what SHACL can't do, §9)

The services that make nRQL + RacerPro *more than a graph validator*, each run
live (verbatim results from RacerPro 2.0):

| Service | nRQL / Racer | Result |
| --- | --- | --- |
| Membership by inference | `betty` asserted only as a `woman` with a child → `(individual-instance? betty mother)` | `t` |
| Inconsistency | `robin` a `man` *and* a `woman` (disjoint) → `(abox-consistent?)` | `nil` |
| Inferred subsumption | `dog ⊑ animal` → `(concept-subsumes? animal-owner dog-owner)` | `t` |
| Role-axiom reasoning | `ancestor` transitive, only `c→d` asserted → ancestors of `d` | `a, b, c` |
| Cardinality w/o UNA | `at-most 1 has-child` + two *named* children | `t`, then `nil` after `(different-from k1 k2)` |
| Non-monotonic rule | `firerule` derives `has-grandchild` | `(a c)` |
| **Query consistency** | `(query-consistent-p Q)` for an unsatisfiable query body | `nil` |
| **Query subsumption** | `(query-entails-p :query-1 :query-2)` (`mother` query ⊑ `woman` query) | `t` |

The last two are the striking ones: SHACL *satisfiability* and *containment* are
undecidable research problems, yet RacerPro shipped `query-consistent-p` /
`query-entails-p` as routine (deliberately incomplete, hence terminating)
services in 2005 — nRQL could reason about its *own queries*.

## OWL classification capstone — `owl_classification.py` + `pets.owl`

The full OWL pipeline (parse → classify TBox → realize ABox) on a real OWL file.
`pets.owl` defines `DogOwner ≡ Person ⊓ ∃owns.Dog`, `PetOwner` likewise with `Pet`,
and `Dog, Cat ⊑ Pet`. `john` is asserted **only** as a `Person` who `owns fido`
(a `Dog`). RacerPro then infers, with nothing else asserted:

```lisp
(owl-read-file ".../pets.owl")
(concept-subsumes? #!:PetOwner #!:DogOwner)  => t     ; DogOwner ⊑ PetOwner (from Dog ⊑ Pet)
(concept-subsumes? #!:DogOwner #!:PetOwner)  => nil
(concept-instances #!:DogOwner)              => (john) ; classified by inference
(concept-instances #!:PetOwner)              => (john)
```

The `(taxonomy)` call returns the classified hierarchy
(`… DogOwner ⊑ PetOwner ⊑ Person …`). SHACL has none of this — no TBox, no
classification, no inferred membership; you would validate a fixed, possibly
pre-materialized graph.

## MiniLisp: the lambda/`:reject` hatch is termination-safe (corrects §5.5)

Probing the `(evaluate …)` / lambda facility shows it is **MiniLisp** — a
deliberately *termination-safe* sandbox, **not** Turing-complete. (The source
`source/expressions.lisp` confirms: `call-function` aborts recursion *"to ensure
termination"*, and `+allowed-cl-functions+` is a curated whitelist.)

| Probe | Result |
| --- | --- |
| `(+ 1 2 3)` | `6` |
| `(search "Joh" "Johann")` / `(search "Joh" "Maria")` | `0` / `nil` (substring search works) |
| `(subseq "Johann" 0 3)`, `(elt …)`, `(length …)`, `(format …)`, `(reduce + …)`, `(dotimes …)` | work |
| `(require :regexp2)` | **not found** (no module loading) |
| `(excl:match-re …)` | **not found** (no regex engine) |
| `(loop …)`, `(funcall …)`, `(mapcar …)` | **not found** |

**Conclusion:** the hatch ships substring `search` but no regex, and forbids
recursion — so it can express neither a general `sh:pattern` regex nor transitive
closure. The 7 native (**N**) test cases (4 unbounded/recursive paths + 3 real
regexes) are therefore robust to the escape-hatch objection. That termination
guarantee is the principled choice for a *decidable* DL query language; it is
SHACL's own hatches (SPARQL, and Turing-complete SHACL-JS) that are the powerful
ones. (The whitelist is extensible via `add-server-hook-function`, so a deployment
*could* register a native regex primitive — but that is adding a CL primitive, the
analogue of a custom SHACL-JS function, not a property of the shipped language.)
