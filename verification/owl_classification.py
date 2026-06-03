#!/usr/bin/env python3
"""Load a real OWL ontology and let RacerPro 2.0 classify it -- the full pipeline
(parse -> classify TBox -> realize ABox) that SHACL does not provide.

pets.owl defines  DogOwner = Person and (owns some Dog)  and  PetOwner likewise
with Pet; Dog and Cat are subclasses of Pet. The individual `john` is asserted
only as a Person who owns `fido` (a Dog). The reasoner then INFERS:
  - DogOwner <= PetOwner          (from Dog <= Pet; never asserted)
  - john is a DogOwner AND PetOwner (classification, never asserted)

Start a RacerPro 2.0 server on TCP 8088 (see README.md), then:
    python3 owl_classification.py
"""
import os, socket

def rf(s):
    b = b""
    while True:
        c = s.recv(1)
        if not c: break
        if c == b"\r" and b: break
        if c in (b"\r", b"\n"): continue
        b += c
    return b.decode("latin-1")

owl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pets.owl")
s = socket.create_connection(("127.0.0.1", 8088), timeout=10); s.settimeout(40)
for c in [
    "(full-reset)",
    f'(owl-read-file "{owl}")',
    "(taxonomy)",                                  # the classified concept taxonomy
    "(concept-instances #!:DogOwner)",             # => (john)   -- INFERRED
    "(concept-instances #!:PetOwner)",             # => (john)   -- Dog <= Pet
    "(individual-instance? #!:john #!:DogOwner)",   # => t
    "(concept-subsumes? #!:PetOwner #!:DogOwner)",  # => t   (never asserted)
    "(concept-subsumes? #!:DogOwner #!:PetOwner)",  # => nil
]:
    s.sendall((c + "\n").encode()); print(f">>> {c}\n    {rf(s)}")
s.close()
