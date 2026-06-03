# nRQL guide

A short, practical guide to **nRQL**, the new RacerPro Query Language — written
while building (and live-testing) the SHACL-vs-nRQL comparison in this repo.

- **[tutorial.md](tutorial.md)** — a hands-on walkthrough: from "hello server" through
  closed-world validation, classification, the data substrate / property graphs,
  rules, query reasoning, and loading OWL. Every command shown was run on a live
  RacerPro 2.0 server.
- **[cheatsheet.md](cheatsheet.md)** — a dense one-page reference: setup, TBox/ABox,
  the query grammar, the killer idioms, the substrate, reasoning services, query
  reasoning, OWL, and the MiniLisp lambda hatch.
  Also typeset as a printable card: **[nrql_cheatsheet.pdf](nrql_cheatsheet.pdf)**
  (one landscape page, 3 columns; source `nrql_cheatsheet.tex`).

Grounded in the *RacerPro User's Guide 2.0* (§4.1) and verified against a running
RacerPro 2.0 — the runnable demos are in [`../verification/`](../verification/)
(`run_all.py` checks them all in one go). RacerPro binaries:
[lambdamikel/RacerPorter](https://github.com/lambdamikel/RacerPorter).
