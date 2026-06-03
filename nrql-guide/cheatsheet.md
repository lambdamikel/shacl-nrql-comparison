# nRQL Cheat Sheet

A compact reference for **nRQL**, the new RacerPro Query Language. Grounded in the
*RacerPro User's Guide 2.0* (§4.1) and **verified live on RacerPro 2.0** (see
[`../verification/`](../verification/)). Page numbers are the printed pages of the
User's Guide.

> **Mental model.** A positive atom `(?x C)` binds `?x` only to objects for which
> the KB *entails* the atom (open world, DL reasoning). `neg` is **negation as
> failure** over the *known* objects (closed world). There is **no unique-name
> assumption**. So nRQL = DL entailment for positive atoms + local closed-world
> failure for `neg` — the combination that makes closed-world validation over an
> open-world OWL KB possible.

---

## Server & socket protocol

```sh
LD_LIBRARY_PATH="$PWD" ./RacerPro      # listens on TCP 8088 (HTTP 8080, control 8089)
```
Send `"<command>\n"`; read one **CR-terminated** frame:
```
:answer <id> "<result>" "<stdout>"     :ok <id> "<stdout>"     :error <id> <msg> "<stdout>"
```

## Knowledge base setup

| Command | Meaning |
|---|---|
| `(full-reset)` | wipe all TBoxes/ABoxes/queries |
| `(in-tbox NAME)` | create/select current TBox |
| `(in-abox NAME [TBOX])` | create/select current ABox (assoc. with TBox) |
| `(in-data-box NAME)` | create/select a data substrate |
| `(in-mirror-data-box NAME)` | data substrate that auto-mirrors the ABox / OWL KB |
| `(get-racer-version)` | → `"2.0"` |

## TBox: concepts, roles, concrete domains

```lisp
(implies     Dog Animal)                 ; Dog ⊑ Animal  (primitive)
(equivalent  Mother (and Woman (some has-child Human)))   ; defined concept
(disjoint    Man Woman)
(define-primitive-role has-child :parent is-relative :transitive nil
                                 :inverse has-parent :domain Human :range Human)
(define-primitive-role ancestor :transitive t)
(inverse     withdrawal deposit)         ; role inverse axiom
(implies-role deposit transaction)       ; role hierarchy
(define-concrete-domain-attribute age  :type integer)
(define-concrete-domain-attribute name :type string)
```

**Concept expressions:** `(and …)`, `(or …)`, `(not C)`, `(some R C)`, `(all R C)`,
`(at-least n R [C])`, `(at-most n R [C])`, `(exactly n R [C])`, `(one-of i …)`,
`top`, `bottom`; `(an attr)` / `(a attr)` = "has some concrete-domain value".

## ABox: assertions

```lisp
(instance    alice Woman)                ; alice : Woman
(related     alice junior has-child)     ; (alice,junior) : has-child
(constrained alice a-age age)            ; a-age is alice's age object
(constraints (equal a-age 50) (string= a-name "Alice"))   ; integer→equal, real→ = / > , string→string=
(same-as     alice ?someone)             ; force equality
(different-from k1 k2)                    ; assert distinctness (no UNA by default!)
```

---

## nRQL queries

```lisp
(retrieve  <head> <body>)                ; the answers
(retrieve1 <body> <head>)                ; body first, then head (enables :reject filters)
(tbox-retrieve <head> <body>)            ; query the TBox taxonomy as an "ABox"
(defquery NAME (vars) <body> [:tbox T])  ; named, reusable query
```

**Variables**

| Form | Meaning |
|---|---|
| `?x` | ABox variable, **non-injective** (two `?`-vars may bind the *same* individual) |
| `$?x` | ABox variable, **injective** (distinct `$?`-vars ⇒ distinct individuals) |
| `?*x` / `$?*x` | substrate-node variable (non-injective / injective) |
| `*ind` | substrate **individual** (a named node) |

> ⚠️ **Heads up:** this is the **reverse** of the *User's Guide* (which says `?`
> injective, `$?` non-injective). The shipping RacerPro 2.0 was changed: `$?`/`$?*`
> are the injective ones (verified live). To be safe, force distinctness
> *explicitly* — see Gotchas.

**Body atoms**

```lisp
(?x C)                       ; concept atom (entailment-aware)
(?x ?y R)                    ; role atom
(?x ?y (inv R))              ; inverse role
(?x (has-known-successor R)) ; has a KNOWN R-successor (sugar for a projected role atom)
(TOP ?x) / (BOTTOM ?x)       ; every / no individual
(same-as ?x ?y)|(= ?x ?y)|(equal ?x ?y) ; equality (3 synonyms)
;; inequality: (neg (same-as ?x ?y)) / (neg (= ?x ?y)) -- NO <> atom for individuals
```

**Body constructors**

```lisp
(and B …)  (union B …)  (neg B)        ; conjunction / disjunction / NAF
(project-to (?x …) B)                   ; existentially hide the other vars (∃)
(inv B)  (substitute (NAME args…))      ; invert; splice a defquery
```

**Head projection** (what answers report)

```lisp
(retrieve (?x) …)                        ; just the bindings
(retrieve (?x (told-value (age ?x))) …)  ; report a told concrete value
(retrieve (?x (annotation (label ?x))) …); report an annotation filler
;; aggregation/format via MiniLisp lambdas in the head — see below
```

---

## The killer idioms (all verified live)

```lisp
;; "missing required value" = NOT EXISTS / anti-(semi-)join   [SHACL sh:minCount 1]
(retrieve (?x) (and (?x Person)
                    (neg (project-to (?x) (?x ?y firstName)))))
;; equivalently:
(retrieve (?x) (and (?x Person) (neg (?x (has-known-successor firstName)))))

;; "every value satisfies C"  = no counterexample           [sh:class on a path]
(retrieve (?x) (and (?x Parent) (?x ?y has-child) (neg (?y Person))))   ; violators

;; "at most one value" (no UNA — over-reports unless distinctness is forced)  [sh:maxCount 1]
(retrieve (?x) (and (?x Person) (?x $?y1 fn) (?x $?y2 fn) (neg (same-as $?y1 $?y2))))

;; "≥2 distinct values satisfying shape Q"  (defquery Q first)   [sh:qualifiedMinCount 2]
(retrieve (?x) (project-to (?x)
                 (and (?x $?a r) (substitute (Q $?a))
                      (?x $?b r) (substitute (Q $?b))
                      (neg (same-as $?a $?b)))))            ; those WITH ≥2; wrap in (neg (project-to …)) for violators

;; "two paths share a value"  = sh:disjoint violation
(retrieve (?x) (and (?x ?v likes) (?x ?v dislikes)))
```

---

## Data substrate / property graphs

```lisp
(in-data-box bank)
(data-node acc1 ((:amount 1000.0) (:currency $) (:number 10039)) account)  ; node + property map + type
(data-edge acc1 acc2 ((:amount 9900.0) (:currency $)) deposit)             ; EDGE with its own property map
(node-label acc1)                ; → ((:amount 1000.0) (:currency $) (:number 10039))
(edge-label acc1 acc2)
;; query node/edge property maps:
(retrieve (?*x) (?*x ((:currency $) (:amount (:predicate (> 10000))))))     ; node-property predicate
(retrieve (?*x ?*y) (?*x ?*y (:predicate (equalp deposit))))                ; edge by label
(retrieve (?*x) (?*x (:predicate (search "Joh"))))                          ; substring search
(retrieve (?*x ?*y) (?*x ?*y (:satisfies (:predicate <))))                  ; binary predicate, no edge needed
```
`:predicate` ops: `(equalp v)`, `(< n)`/`(> n)`, `(search "s")` (substring), … .
Hybrid queries mix `?x` (ABox/DL) and `?*x` (substrate) atoms in one body.

## Rules

```lisp
(defquery mother-of (?x ?y) (and (?x Woman) (?x ?y has-child)))
(firerule (and (?x ?y has-child) (?y ?z has-child))           ; antecedent = a query body (may use neg!)
          ((related ?x ?z has-grandchild)))                   ; consequent = generalized ABox assertions
(firerule (and (?x Mother) (neg (?x (has-known-successor has-child))))
          ((instance (new-ind first-child-of ?x) Human)       ; create a fresh individual
           (related  (new-ind first-child-of ?x) ?x has-mother)))
```

## Reasoning services (what a validator can't do)

```lisp
(classify-tbox) (taxonomy)                  ; classify; dump the inferred hierarchy
(concept-subsumes? C D)                      ; D ⊑ C ?            (inferred)
(concept-satisfiable? C)                     ; is C coherent?
(realize-abox)                               ; compute most-specific types of all individuals
(individual-instance? i C)                   ; i : C entailed?    (open world)
(individual-types i)  (individual-direct-types i)
(concept-instances C)                        ; all i with i : C
(abox-consistent?)                           ; is the ABox logically consistent?
```

## Query reasoning (the exotic part)

```lisp
(prepare-abox-query (?x) (?x Mother))   ; → (:query-1 :ready-to-run)
(query-consistent-p :query-1)            ; can it ever have answers?  (nil ⇒ always empty)
(query-entails-p :query-1 :query-2)      ; every answer of q1 is an answer of q2 in every model? (subsumption)
(query-equivalent-p :query-1 :query-2)   ; mutual entailment
(execute-query :query-1)
```

## OWL

```lisp
(owl-read-file "/path/to/onto.owl")      ; parse RDF/XML OWL → TBox + ABox
(owl-read-document "http://…/onto.owl")  ; same, from a URL
;; refer to entities in the default namespace with the #!: reader macro:
(concept-instances #!:DogOwner)          ; → inferred instances
(individual-instance? #!:john #!:DogOwner)
```

## Lambda hatch — MiniLisp (termination-safe, NOT Turing-complete)

```lisp
(evaluate (+ 1 2))                       ; a restricted, side-effect-free interpreter
(retrieve1 (?x Person)                   ; retrieve1 = body first; head lambda + :reject = a filter
  ( ((:lambda (x) (if (search "Joh" (told-value (name x))) `(?x ,x) :reject)) ?x) ))
```
**Has:** arithmetic, `format`, `search`/`subseq`/`elt`/`length`, `reduce`, `some`,
`dotimes`, KB callbacks (`retrieve`, `told-value`). **Lacks** (by design — recursion
is aborted to guarantee termination): `loop`, `funcall`, `require`, `excl:*`, **regex**.
Extensible per deployment via `add-server-hook-function`. (UG §4.1.8, pp. 146–148.)

## Modes & settings

```lisp
(set-nrql-mode N)                ; N = 0..4: trade completeness for speed (see UG p. 165)
(enable-data-substrate-mirroring) (enable-smart-abox-mirroring)
(report-inconsistent-queries) (dont-report-inconsistent-queries)
(set-unique-name-assumption t)   ; turn UNA on (off by default!)
```

---

### Gotchas

- **No UNA by default** — `(at-most 1 R)` with two named fillers is *consistent*
  until you `(different-from …)`; counting queries over-report similarly.
- **`(neg (?x ?y R))` ≠ `(neg (project-to (?x) (?x ?y R)))`** — the first negates a
  *pair* atom (almost never what you want); the second is the safe "no R-successor".
- **`neg` is failure over *known* objects**, not classical negation, and not
  "triple absent" — fix your reasoning mode / materialization before trusting it.
- **`has-known-successor`** asks for a *named* successor; an OWL existential gives
  an *entailed* (possibly anonymous) one that `neg`/`has-known-successor` won't see.
- **Variable (in)equality** — force two vars distinct with `(neg (same-as ?x ?y))`
  or `(neg (= ?x ?y))`. There is **no `<>`** atom for individuals, and
  `(different-from i j)` is an *ABox assertion*, not a query atom. The `?`/`$?`
  injective default is the **reverse of the manual** in RacerPro 2.0 (`$?` is the
  injective one), so don't rely on it — be explicit. (UNA toggling does *not*
  change variable-distinctness in queries.)
