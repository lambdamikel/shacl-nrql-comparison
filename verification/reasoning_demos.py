#!/usr/bin/env python3
"""What SHACL (Core) still cannot do, demonstrated live on RacerPro 2.0.

These are the reasoning services that distinguish nRQL + RacerPro from a graph
validator: entailment-aware classification, logical (un)satisfiability, non-
monotonic rules, unique-name-assumption-sensitive cardinality, role-axiom
reasoning, and -- the exotic one -- query consistency and query subsumption.

Start a RacerPro 2.0 server on TCP 8088 (see README.md), then:
    python3 reasoning_demos.py
"""
import socket

def _rf(s):
    b = b""
    while True:
        c = s.recv(1)
        if not c:
            break
        if c == b"\r" and b:
            break
        if c in (b"\r", b"\n"):
            continue
        b += c
    return b.decode("latin-1")

def run(title, cmds):
    print("=" * 70 + f"\n{title}\n" + "=" * 70)
    s = socket.create_connection(("127.0.0.1", 8088), timeout=10)
    s.settimeout(25)
    for c in cmds:
        s.sendall((c + "\n").encode())
        print(f">>> {c}\n    {_rf(s)}")
    s.close()
    print()

# 1. Role-axiom reasoning: transitivity yields the closure as an *entailment*
run("1. Transitivity reasoning -> closure is entailed (not syntactic)", [
    "(full-reset)", "(in-tbox anc)",
    "(define-primitive-role ancestor :transitive t)",
    "(in-abox anc anc)",
    "(related a b ancestor)", "(related b c ancestor)", "(related c d ancestor)",
    "(retrieve (?x) (?x d ancestor))",            # => a, b, c  (only c->d asserted)
])

# 2. Classification: infer class membership from a concept *definition*
run("2. Classification -> membership inferred from a definition", [
    "(full-reset)", "(in-tbox fam)",
    "(equivalent mother (and woman (some has-child human)))",
    "(in-abox fam fam)",
    "(instance betty woman)", "(related betty junior has-child)", "(instance junior human)",
    "(realize-abox)",
    "(individual-instance? betty mother)",        # => t   (never asserted)
])

# 3. Logical (in)consistency: a contradiction in the data
run("3. Inconsistency detection (disjointness)", [
    "(full-reset)", "(in-tbox d)", "(disjoint man woman)", "(in-abox d d)",
    "(instance robin man)", "(instance robin woman)",
    "(abox-consistent?)",                          # => nil
])

# 4. Non-monotonic rules: derive new assertions (here, a relation)
run("4. firerule -> derive a new relation", [
    "(full-reset)", "(in-tbox g)", "(in-abox g g)",
    "(related a b has-child)", "(related b c has-child)",
    "(firerule (and (?x ?y has-child) (?y ?z has-child)) ((related ?x ?z has-grandchild)))",
    "(retrieve (?x ?z) (?x ?z has-grandchild))",  # => (a c)
])

# 5. Cardinality under the open world / no unique-name assumption
run("5. Cardinality + no-Unique-Name-Assumption", [
    "(full-reset)", "(in-tbox c)",
    "(equivalent single-child-parent (at-most 1 has-child))",
    "(in-abox c c)",
    "(instance p single-child-parent)",
    "(related p k1 has-child)", "(related p k2 has-child)",
    "(abox-consistent?)",                          # => t   (k1 might equal k2)
    "(different-from k1 k2)",
    "(abox-consistent?)",                          # => nil (two distinct children > 1)
])

# 6. Inferred concept subsumption (TBox classification)
run("6. Inferred subsumption", [
    "(full-reset)", "(in-tbox s)",
    "(implies dog animal)",
    "(equivalent dog-owner (some owns dog))",
    "(equivalent animal-owner (some owns animal))",
    "(concept-subsumes? animal-owner dog-owner)",  # => t  (never asserted)
    "(concept-subsumes? dog-owner animal-owner)",  # => nil
])

# 7. + 8. Query reasoning: query consistency and query subsumption (entailment).
#   query ids are assigned sequentially (:query-1, :query-2, ...) after full-reset.
run("7/8. Query consistency and query subsumption", [
    "(full-reset)", "(in-tbox qr)",
    "(implies mother woman)", "(disjoint man woman)",
    "(in-abox qr qr)",
    "(prepare-abox-query (?x) (?x mother))",          # :query-1
    "(prepare-abox-query (?x) (?x woman))",           # :query-2
    "(prepare-abox-query (?x) (?x (and man woman)))", # :query-3 (unsatisfiable body)
    "(query-entails-p :query-1 :query-2)",  # 'mother' query subsumed by 'woman' query => t
    "(query-entails-p :query-2 :query-1)",  # => nil
    "(query-consistent-p :query-3)",        # => nil (must be empty on every ABox)
])
