#!/usr/bin/env python3
"""Execution check of the paper's nRQL idioms on a live RacerPro 2.0 server.

Reproduces, against a real reasoner, the two SHACL-vs-nRQL card examples and the
property-graph (data-substrate) session of Figure 1 / section 11.

Setup:
  1. Get the RacerPro 2.0 binaries: github.com/lambdamikel/RacerPorter
     -> racer_binaries/<platform>/RacerPro-2-0/acl-mlisp
  2. Start the server (it listens on TCP 8088):
       LD_LIBRARY_PATH=. ./RacerPro
  3. python3 racer_queries.py

Protocol: connect to 127.0.0.1:8088, send "<command>\\n", read one frame
terminated by CR. Replies look like:  :answer <id> "<result>" "<stdout>"
"""
import socket

HOST, PORT = "127.0.0.1", 8088

def _read_frame(s):
    buf = b""
    while True:
        ch = s.recv(1)
        if not ch:
            break
        if ch == b"\r":
            if buf:
                break
            continue
        if ch == b"\n":
            continue
        buf += ch
    return buf.decode("latin-1")

def run(title, cmds):
    print("=" * 70 + f"\n{title}\n" + "=" * 70)
    s = socket.create_connection((HOST, PORT), timeout=10)
    s.settimeout(25)
    for c in cmds:
        s.sendall((c + "\n").encode())
        print(f">>> {c}\n    {_read_frame(s)}")
    s.close()
    print()

# --- Example 1: sh:minCount 1 -- Persons with no known firstName -------------
run("Example 1  --  minCount violation query", [
    "(full-reset)",
    "(in-tbox family)",
    "(in-abox family family)",
    "(instance alice Person)",
    "(instance bob Person)",
    "(instance carol Person)",            # carol has NO firstName
    "(related alice alice-fn has-firstname)",
    "(related bob bob-fn has-firstname)",
    "(retrieve (?x) (and (?x Person) (neg (project-to (?x) (?x ?y has-firstname)))))",
    # expected: (((?x carol)))
])

# --- Example 2: sh:class -- every hasChild value must be a Person -------------
# Uses DL entailment: a child asserted only as MalePerson (subclass) must PASS.
run("Example 2  --  value-type with DL entailment", [
    "(full-reset)",
    "(in-tbox fam2)",
    "(implies MalePerson Person)",        # MalePerson is-a Person
    "(disjoint Animal Person)",           # Animal is NOT a Person
    "(in-abox fam2 fam2)",
    "(instance p1 Parent)",
    "(instance c1 MalePerson)",           # inferred Person
    "(related p1 c1 has-child)",
    "(instance p2 Parent)",
    "(instance c2 Animal)",               # not a Person
    "(related p2 c2 has-child)",
    "(realize-abox)",
    "(individual-instance? c1 Person)",   # expected: t   (inferred!)
    "(individual-instance? c2 Person)",   # expected: nil
    "(retrieve (?x) (and (?x Parent) (?x ?y has-child) (neg (?y Person))))",
    # expected: (((?x p2)))   -- p1 PASSES because c1 is an inferred Person
])

# --- Property graph (Figure 1 / section 11): fintech data substrate ----------
run("Property graph  --  fintech data substrate (Figure 1)", [
    "(full-reset)",
    "(in-tbox fintech)",
    "(implies account financial-concept)",
    "(implies transaction financial-relation)",
    "(implies-role withdrawal transaction)",
    "(implies-role deposit transaction)",
    "(inverse withdrawal deposit)",
    "(in-data-box bank1)",
    "(data-node acc1 ((:amount 1000.00) (:currency $) (:number 10039)) account)",
    "(data-node acc2 ((:amount 19000.00) (:currency $) (:number 2090)) account)",
    "(data-edge acc1 acc2 ((:amount 9900.00) (:currency $)) deposit)",  # edge property map
    "(data-node acc3 ((:number 10039) (:currency $)) account)",
    "(retrieve (?x) (and (?x account) (?*x ((:currency $) (:amount (:predicate (> 10000)))))))",
    # suspicious withdrawal: predicate on the EDGE's amount + DL role inverse
    "(retrieve (?x ?y) (and (?x account) (?*x ((:currency $) (:amount (:predicate (> 10000))))) (?x ?y withdrawal) (?*y ?*x ((:currency $) (:amount (:predicate (> 5000)))))))",
    "(node-label acc2)",
    "(node-label acc1)",
    "(retrieve (?*x) (and (?*x ((:number 10039))) (neg (same-as ?*x *acc1))))",
])
