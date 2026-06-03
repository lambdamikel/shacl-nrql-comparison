#!/usr/bin/env python3
"""Self-checking harness: runs the key nRQL/RacerPro queries behind every claim
in the report and ASSERTS the expected result. One green run = the paper's
execution-verified claims reproduce on your machine.

Start a RacerPro 2.0 server on TCP 8088 (see README.md), then:
    python3 run_all.py
Exit code 0 iff every check passes.
"""
import os, socket, sys

def _rf(s):
    b = b""
    while True:
        c = s.recv(1)
        if not c: break
        if c == b"\r" and b: break
        if c in (b"\r", b"\n"): continue
        b += c
    return b.decode("latin-1")

def send(s, cmd):
    s.sendall((cmd + "\n").encode())
    return _rf(s)

def has(*subs):     return lambda r: all(x in r for x in subs)
def lacks(*subs):   return lambda r: all(x not in r for x in subs)
def both(*preds):   return lambda r: all(p(r) for p in preds)

OWL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pets.owl")

# (name, [setup cmds], [(check cmd, predicate, expectation text)])
TESTS = [
 ("minCount: missing firstName -> carol",
  ["(full-reset)","(in-tbox t)","(in-abox t t)","(instance alice Person)","(instance bob Person)",
   "(instance carol Person)","(related alice an firstName)","(related bob bn firstName)"],
  [("(retrieve (?x) (and (?x Person) (neg (project-to (?x) (?x ?y firstName)))))",
    both(has("carol"), lacks("alice","bob")), "carol only")]),

 ("sh:class with DL entailment -> only p2 (p1 passes via inferred Person)",
  ["(full-reset)","(in-tbox t)","(implies MalePerson Person)","(disjoint Animal Person)","(in-abox t t)",
   "(instance p1 Parent)","(instance c1 MalePerson)","(related p1 c1 has-child)",
   "(instance p2 Parent)","(instance c2 Animal)","(related p2 c2 has-child)","(realize-abox)"],
  [("(individual-instance? c1 Person)", has("t"), "c1 inferred Person = t"),
   ("(retrieve (?x) (and (?x Parent) (?x ?y has-child) (neg (?y Person))))",
    both(has("p2"), lacks("p1")), "p2 only")]),

 ("property graph: edge-amount predicate -> (acc2 acc1)",
  ["(full-reset)","(in-tbox t)","(implies-role withdrawal transaction)","(implies-role deposit transaction)",
   "(inverse withdrawal deposit)","(in-data-box bank)",
   "(data-node acc1 ((:amount 1000.00) (:currency $)) account)",
   "(data-node acc2 ((:amount 19000.00) (:currency $)) account)",
   "(data-edge acc1 acc2 ((:amount 9900.00) (:currency $)) deposit)"],
  [("(retrieve (?x ?y) (and (?x account) (?*x ((:amount (:predicate (> 10000))))) (?x ?y withdrawal) (?*y ?*x ((:amount (:predicate (> 5000)))))))",
    both(has("acc2","acc1")), "(acc2 acc1)")]),

 ("maxCount: two firstNames -> alice",
  ["(full-reset)","(in-tbox t)","(in-abox t t)","(instance alice Person)",
   "(related alice f1 firstName)","(related alice f2 firstName)","(instance bob Person)","(related bob f3 firstName)"],
  [("(retrieve (?x) (and (?x Person) (?x $?y1 firstName) (?x $?y2 firstName) (neg (same-as $?y1 $?y2))))",
    both(has("alice"), lacks("bob")), "alice")]),

 ("sh:disjoint: shared value -> x",
  ["(full-reset)","(in-tbox t)","(in-abox t t)","(instance x thing)","(related x a likes)","(related x a dislikes)",
   "(instance y thing)","(related y b likes)","(related y d dislikes)"],
  [("(retrieve (?x) (and (?x ?v likes) (?x ?v dislikes)))", both(has("x"), lacks("y")), "x")]),

 ("sec 6.3 open vs closed world: entailed child but flagged by minCount",
  ["(full-reset)","(in-tbox t)","(implies parent (some has-child top))","(in-abox t t)",
   "(instance alice parent)","(instance bob parent)","(related bob junior has-child)"],
  [("(individual-instance? alice (some has-child top))", has("t"), "alice entailed child = t"),
   ("(retrieve (?x) (?x (has-known-successor has-child)))", both(has("bob"), lacks("alice")), "bob has known child"),
   ("(retrieve (?x) (and (?x parent) (neg (?x (has-known-successor has-child)))))",
    both(has("alice"), lacks("bob")), "alice flagged by minCount")]),

 ("transitive role -> closure a,b,c",
  ["(full-reset)","(in-tbox t)","(define-primitive-role ancestor :transitive t)","(in-abox t t)",
   "(related a b ancestor)","(related b c ancestor)","(related c d ancestor)"],
  [("(retrieve (?x) (?x d ancestor))", has("a","b","c"), "a,b,c")]),

 ("classification: betty inferred mother",
  ["(full-reset)","(in-tbox t)","(equivalent mother (and woman (some has-child human)))","(in-abox t t)",
   "(instance betty woman)","(related betty j has-child)","(instance j human)","(realize-abox)"],
  [("(individual-instance? betty mother)", has("t"), "t")]),

 ("inconsistency: man+woman disjoint -> nil",
  ["(full-reset)","(in-tbox t)","(disjoint man woman)","(in-abox t t)","(instance r man)","(instance r woman)"],
  [("(abox-consistent?)", has("nil"), "nil")]),

 ("inferred subsumption: dog-owner < animal-owner",
  ["(full-reset)","(in-tbox t)","(implies dog animal)","(equivalent dog-owner (some owns dog))",
   "(equivalent animal-owner (some owns animal))"],
  [("(concept-subsumes? animal-owner dog-owner)", has("t"), "t"),
   ("(concept-subsumes? dog-owner animal-owner)", has("nil"), "nil")]),

 ("firerule: derive has-grandchild -> (a c)",
  ["(full-reset)","(in-tbox t)","(in-abox t t)","(related a b has-child)","(related b c has-child)",
   "(firerule (and (?x ?y has-child) (?y ?z has-child)) ((related ?x ?z has-grandchild)))"],
  [("(retrieve (?x ?z) (?x ?z has-grandchild))", has("(?x a)","(?z c)"), "(a c)")]),

 ("cardinality + no-UNA: consistent until different-from",
  ["(full-reset)","(in-tbox t)","(equivalent scp (at-most 1 has-child))","(in-abox t t)",
   "(instance p scp)","(related p k1 has-child)","(related p k2 has-child)"],
  [("(abox-consistent?)", has("t"), "t (k1 may = k2)"),
   ("(different-from k1 k2)", lambda r: True, "assert distinct"),
   ("(abox-consistent?)", has("nil"), "nil (now > 1)")]),

 ("query consistency: unsatisfiable query -> nil",
  ["(full-reset)","(in-tbox t)","(disjoint man woman)","(in-abox t t)",
   "(prepare-abox-query (?x) (?x (and man woman)))"],
  [("(query-consistent-p :query-1)", has("nil"), "nil")]),

 ("query subsumption: mother-query entails woman-query -> t",
  ["(full-reset)","(in-tbox t)","(implies mother woman)","(in-abox t t)",
   "(prepare-abox-query (?x) (?x mother))","(prepare-abox-query (?x) (?x woman))"],
  [("(query-entails-p :query-1 :query-2)", has("t"), "t"),
   ("(query-entails-p :query-2 :query-1)", has("nil"), "nil")]),

 ("substring sh:pattern via substrate -> Johann",
  ["(full-reset)","(in-tbox t)","(define-concrete-domain-attribute fname :type string)","(in-abox t t)",
   "(in-mirror-data-box t)","(instance alice Person)","(constrained alice af fname)",
   '(constraints (string= af "Johann"))',"(instance bob Person)","(constrained bob bf fname)",
   '(constraints (string= bf "Maria"))'],
  [('(retrieve (?*x) (?*x (:predicate (search "Joh"))))', both(has("Johann"), lacks("Maria")), "Johann")]),

 ("OWL load + classification: john -> DogOwner, DogOwner < PetOwner",
  ["(full-reset)", f'(owl-read-file "{OWL}")'],
  [("(concept-instances #!:DogOwner)", has("john"), "john"),
   ("(concept-subsumes? #!:PetOwner #!:DogOwner)", has("t"), "t"),
   ("(concept-subsumes? #!:DogOwner #!:PetOwner)", has("nil"), "nil")]),
]

def main():
    s = socket.create_connection(("127.0.0.1", 8088), timeout=10); s.settimeout(40)
    npass = nfail = 0
    for name, setup, checks in TESTS:
        for c in setup:
            send(s, c)
        ok = True
        details = []
        for cmd, pred, exp in checks:
            r = send(s, cmd)
            # result field of  :answer <id> "<result>" "<out>"  /  :ok ...
            res = r
            p = pred(res)
            ok = ok and p
            details.append(("  ok " if p else "  XX ") + f"{exp}: {res[:70]}")
        print(("PASS  " if ok else "FAIL  ") + name)
        if not ok:
            print("\n".join(details))
        npass += ok; nfail += (not ok)
    s.close()
    print(f"\n{npass}/{npass+nfail} checks passed" + ("" if nfail == 0 else f"  ({nfail} FAILED)"))
    sys.exit(0 if nfail == 0 else 1)

if __name__ == "__main__":
    main()
