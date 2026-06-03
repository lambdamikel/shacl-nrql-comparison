# An nRQL Tutorial

A hands-on introduction to **nRQL**, the query language of the RacerPro description-
logic reasoner. Every command below was run on a live **RacerPro 2.0** server; the
expected answers are shown. For a terse reference, see the [cheat sheet](cheatsheet.md).

nRQL is unusual: it is a *query* language whose atoms are evaluated by *logical
entailment* over an OWL/DL knowledge base, combined with *negation as failure* for
closed-world questions. That combination lets you do closed-world data validation
over an open-world ontology — and a great deal more (classification, consistency,
rules, even reasoning about queries themselves).

## 0. Talking to the server

RacerPro is a server speaking a line protocol on TCP **8088**. Send a command, get
back `:answer <id> "<result>" "<stdout>"`. A 20-line Python client is all you need
(see [`../verification/racer_queries.py`](../verification/racer_queries.py)); in
this tutorial we just show `>` commands and their results.

```lisp
> (get-racer-version)
"2.0"
> (full-reset)
:okay-full-reset
```

## 1. A first knowledge base

A TBox holds the schema (concepts and roles); an ABox holds the data (individuals).

```lisp
> (in-tbox family)
> (implies Woman Person)            ; Woman ⊑ Person
> (implies Man   Person)
> (disjoint Man Woman)
> (define-primitive-role has-child :inverse has-parent)
> (in-abox family family)
> (instance alice Woman)
> (instance bob   Man)
> (related  alice carol has-child)
> (instance carol Woman)
```

## 2. Your first queries

`retrieve` takes a **head** (what to report) and a **body** (the pattern).

```lisp
> (retrieve (?x) (?x Person))                ; everyone known to be a Person
(((?x alice)) ((?x bob)) ((?x carol)))
> (retrieve (?x ?y) (?x ?y has-child))       ; parent/child pairs
(((?x alice) (?y carol)))
> (retrieve (?x ?y) (?y ?x has-parent))      ; same via the inverse role
(((?x alice) (?y carol)))
```

Note `alice` came back as a `Person` even though we only asserted her as a `Woman`:
positive atoms are **entailment-aware** (`Woman ⊑ Person`).

## 3. Open world vs. closed world — the key lesson

Add an axiom saying every parent has *some* child, then ask two different questions.

```lisp
> (full-reset) (in-tbox t) (implies parent (some has-child top)) (in-abox t t)
> (instance alice parent)                    ; alice is a parent — but no named child
> (instance bob   parent) (related bob junior has-child)

> (individual-instance? alice (some has-child top))   ; is she ENTAILED to have a child?
t                                                     ; yes — the open-world axiom

> (retrieve (?x) (?x (has-known-successor has-child))); who has a KNOWN child?
(((?x bob)))                                          ; only bob

> (retrieve (?x) (and (?x parent) (neg (?x (has-known-successor has-child)))))
(((?x alice)))                                        ; alice fails the closed-world check
```

`alice` **satisfies the OWL existential yet fails the closed-world "has a child"
check.** This is the heart of nRQL: `neg` is *negation as failure over known
objects*, not classical negation. `has-known-successor` asks for a *named*
successor — the anonymous witness an existential promises does not count.

> **Pitfall.** Write `(neg (project-to (?x) (?x ?y has-child)))`, **not**
> `(neg (?x ?y has-child))`. The first means "no `has-child` successor exists";
> the second negates a *pair* atom and is almost never what you want.

## 4. Closed-world validation (the "SHACL" pattern)

"Every `Person` must have a known `firstName`" — return the violators:

```lisp
> (full-reset) (in-tbox t) (in-abox t t)
> (instance alice Person) (related alice an firstName)
> (instance bob   Person) (related bob   bn firstName)
> (instance carol Person)                              ; carol has none
> (retrieve (?x) (and (?x Person) (neg (project-to (?x) (?x ?y firstName)))))
(((?x carol)))
```

That `neg`/`project-to` shape is exactly a SQL `NOT EXISTS` / anti-join. nRQL had it
years before SPARQL 1.1 standardized `FILTER NOT EXISTS`.

## 5. Counting, and the missing unique-name assumption

"At most one `firstName`" — return anyone with two distinct ones:

```lisp
> (full-reset) (in-tbox t) (in-abox t t)
> (instance alice Person) (related alice f1 firstName) (related alice f2 firstName)
> (retrieve (?x) (and (?x Person) (?x $?y1 firstName) (?x $?y2 firstName)
                      (neg (same-as $?y1 $?y2))))
(((?x alice)))
```

Two notes on the variables. To force two values distinct, use
`(neg (same-as $?y1 $?y2))` (or `(neg (= …))`); there is no `<>` atom for
individuals. And a live quirk worth knowing: in RacerPro 2.0, `$?`-variables are
**injective** (distinct `$?`-vars never co-refer) while plain `?`-variables are
not — the *reverse* of the User's Guide (the implementation was changed). So
prefer the explicit `(neg (same-as …))` and don't rely on the injective default.

Beware also: OWL has **no unique-name assumption**, so `f1` and `f2` are not
assumed distinct. The query flags `alice` because `f1 = f2` is *not entailed* —
which may over-report. The reasoning side shows the same effect crisply:

```lisp
> (full-reset) (in-tbox t) (equivalent single (at-most 1 has-child)) (in-abox t t)
> (instance p single) (related p k1 has-child) (related p k2 has-child)
> (abox-consistent?)            ; consistent — k1 and k2 MIGHT be the same individual
t
> (different-from k1 k2)        ; now force them apart
> (abox-consistent?)            ; two distinct children violate "at most 1"
nil
```

## 6. Reasoning the data can't state

Define `Mother`, assert nothing about motherhood, and let the reasoner classify:

```lisp
> (full-reset) (in-tbox t)
> (equivalent Mother (and Woman (some has-child Human)))
> (in-abox t t)
> (instance betty Woman) (related betty junior has-child) (instance junior Human)
> (realize-abox)
> (individual-instance? betty Mother)        ; never asserted
t
> (concept-subsumes? Person Mother)          ; Mother ⊑ Person, inferred
t
> (abox-consistent?)                          ; logical consistency check
t
```

## 7. A property graph in the data substrate

The substrate is a node- **and edge**-labelled graph with key–value property maps,
loosely coupled to the reasoner. Edge labels can be DL roles.

```lisp
> (full-reset) (in-tbox bank)
> (implies-role withdrawal transaction) (implies-role deposit transaction)
> (inverse withdrawal deposit)
> (in-data-box b)
> (data-node acc1 ((:amount 1000.0)  (:currency $) (:number 10039)) account)
> (data-node acc2 ((:amount 19000.0) (:currency $) (:number 2090))  account)
> (data-edge acc1 acc2 ((:amount 9900.0) (:currency $)) deposit)     ; edge has its own properties!

> (retrieve (?x) (and (?x account) (?*x ((:currency $) (:amount (:predicate (> 10000)))))))
(((?x acc2)))

;; "a high-balance $-account that received a transfer over 5000" — predicate on the EDGE amount:
> (retrieve (?x ?y) (and (?x account)
                         (?*x ((:amount (:predicate (> 10000)))))
                         (?x ?y withdrawal)
                         (?*y ?*x ((:amount (:predicate (> 5000)))))))
(((?x acc2) (?y acc1)))
```

This is a property graph (attributes on nodes *and* edges, queried directly) fused
with DL role reasoning (`withdrawal` traverses the `deposit` edge via the `inverse`
axiom) — in 2005.

## 8. Rules

A `firerule` has a query body as antecedent (it may use `neg`) and generalized ABox
assertions as consequent. Here, derive a grandparent relation:

```lisp
> (full-reset) (in-tbox t) (in-abox t t)
> (related a b has-child) (related b c has-child)
> (firerule (and (?x ?y has-child) (?y ?z has-child))
            ((related ?x ?z has-grandchild)))
> (retrieve (?x ?z) (?x ?z has-grandchild))
(((?x a) (?z c)))
```

Rules can also `(instance (new-ind …) C)` to *create* fresh individuals, and are
non-monotonic because the antecedent may use `neg`.

## 9. Reasoning about queries

nRQL can analyse queries, not just answer them — *query consistency* (can it ever
return anything?) and *query subsumption / entailment* (does one query's answer set
always contain another's?).

```lisp
> (full-reset) (in-tbox t) (implies Mother Woman) (disjoint Man Woman) (in-abox t t)
> (prepare-abox-query (?x) (?x Mother))            ; :query-1
> (prepare-abox-query (?x) (?x Woman))             ; :query-2
> (prepare-abox-query (?x) (?x (and Man Woman)))   ; :query-3
> (query-entails-p :query-1 :query-2)   ; every Mother is a Woman ⇒ q1 ⊑ q2
t
> (query-entails-p :query-2 :query-1)
nil
> (query-consistent-p :query-3)         ; (and Man Woman) is unsatisfiable
nil                                     ; ⇒ this query is empty on EVERY ABox
```

SHACL shape satisfiability/containment are undecidable research problems; RacerPro
shipped these as routine (deliberately incomplete, hence terminating) services.

## 10. Loading an OWL ontology

```lisp
> (full-reset)
> (owl-read-file "/path/to/pets.owl")   ; DogOwner ≡ Person ⊓ ∃owns.Dog; Dog ⊑ Pet; john owns a Dog
> (concept-subsumes? #!:PetOwner #!:DogOwner)   ; inferred from Dog ⊑ Pet
t
> (concept-instances #!:DogOwner)                ; john, classified by inference
(|http://example.org/pets#john|)
```

Use the `#!:` reader macro for names in the ontology's default namespace.

## 11. The escape hatch — and its limit

A `retrieve1` query (body first) can carry a **lambda + `:reject`** filter in its
head, evaluated in *MiniLisp* — a deliberately **termination-safe** sandbox.

```lisp
> (evaluate (search "Joh" "Johann"))     ; substring search works
0
> (evaluate (require :regexp2))          ; but there is NO regex engine
MiniLisp Error: Function REQUIRE not found
```

MiniLisp has arithmetic, string ops (`search`, `subseq`, …), `reduce`, bounded
`dotimes`, and KB callbacks — but **no recursion** (it is aborted to guarantee
termination) and **no regex**. That is the right trade for a query language attached
to a *decidable* reasoner: a query filter can never make the server diverge.

---

### Where to go next

- The [cheat sheet](cheatsheet.md) for the full operator/atom inventory.
- The runnable demos in [`../verification/`](../verification/) — `run_all.py` checks
  all of the above in one go.
- The *RacerPro User's Guide 2.0*, §4.1, for the formal grammar (pp. 150–153) and
  the complete reasoning/substrate API.
