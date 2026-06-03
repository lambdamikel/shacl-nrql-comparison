#!/usr/bin/env python3
"""Execution check of the SHACL -> nRQL translation table (Table 1) and the
section 6 epistemic traps, run live on RacerPro 2.0.

This complements racer_queries.py (which does minCount, sh:class, and the
property graph): here are the remaining translation idioms plus the crucial
open-world/closed-world trap.

Start a RacerPro 2.0 server on TCP 8088 (see README.md), then:
    python3 translation_check.py
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

# A. sh:maxCount 1 -- two firstName fillers not known-equal (the no-UNA "lossy" case)
run("A. maxCount 1 violation", [
    "(full-reset)", "(in-tbox a)", "(in-abox a a)",
    "(instance alice Person)", "(related alice fn1 firstName)", "(related alice fn2 firstName)",
    "(instance bob Person)", "(related bob fn3 firstName)",
    "(retrieve (?x) (and (?x Person) (?x $?y1 firstName) (?x $?y2 firstName) (neg (same-as $?y1 $?y2))))",
    # => alice  (NB: over-reports without UNA -- fn1, fn2 might really be equal)
])

# B. sh:qualifiedMinCount 1 of shape [sh:class Child]
run("B. qualifiedMinCount 1 (a child of class Child)", [
    "(full-reset)", "(in-tbox b)", "(in-abox b b)",
    "(instance p1 Parent)", "(related p1 c1 has-child)", "(instance c1 Child)",
    "(instance p2 Parent)", "(related p2 c2 has-child)", "(instance c2 Adult)",
    "(retrieve (?x) (and (?x Parent) (neg (project-to (?x) (and (?x ?y has-child) (?y Child))))))",
    # => p2  (p1 has a Child child and passes)
])

# C. sh:disjoint -- a value shared by two properties
run("C. sh:disjoint violation (shared value)", [
    "(full-reset)", "(in-tbox c)", "(in-abox c c)",
    "(instance x thing)", "(related x a likes)", "(related x a dislikes)",   # shared value a
    "(instance y thing)", "(related y b likes)", "(related y d dislikes)",
    "(retrieve (?x) (and (?x ?v likes) (?x ?v dislikes)))",
    # => x
])

# D. *** the crux: open-world existential vs closed-world "known successor" (sec 6.3) ***
run("D. Anonymous witness -- entailed child but NO known child (sec 6.3)", [
    "(full-reset)", "(in-tbox e)",
    "(implies parent (some has-child top))",            # every parent has SOME child
    "(in-abox e e)",
    "(instance alice parent)",                          # entailed child, but none named
    "(instance bob parent)", "(related bob junior has-child)",   # bob has a known child
    "(individual-instance? alice (some has-child top))",         # => t   (entailed!)
    "(retrieve (?x) (?x (has-known-successor has-child)))",      # => bob only
    "(retrieve (?x) (and (?x parent) (neg (?x (has-known-successor has-child)))))",  # => alice
    # alice satisfies the OWL axiom yet is flagged by the closed-world minCount query.
])

# E. substring sh:pattern via the mirror data substrate (the conditional/C bucket)
run("E. substring sh:pattern via substrate (:predicate (search ...))", [
    "(full-reset)", "(in-tbox f)",
    "(define-concrete-domain-attribute fname :type string)",
    "(in-abox f f)", "(in-mirror-data-box f)",
    "(instance alice Person)", "(constrained alice af fname)", '(constraints (string= af "Johann"))',
    "(instance bob Person)", "(constrained bob bf fname)", '(constraints (string= bf "Maria"))',
    '(retrieve (?*x) (?*x (:predicate (search "Joh"))))',
    # => "Johann"   (substring match on the mirrored told value; full regex is NOT available)
])
