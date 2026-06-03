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
3. Run the scripts:
   ```sh
   python3 racer_queries.py     # the two card examples + the property-graph session
   python3 minilisp_probe.py    # characterizes the lambda/:reject "MiniLisp" hatch
   ```

The socket protocol is line-based: send `"<command>\n"`, read one CR-terminated
frame `:answer <id> "<result>" "<stdout>"`.

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
