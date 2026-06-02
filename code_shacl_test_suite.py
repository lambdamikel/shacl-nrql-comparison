#!/usr/bin/env python3
"""Empirically code the W3C SHACL (2017) test suite against Table 1 of the
revised SHACL-vs-nRQL comparison.

Each *main* test file (excluding manifests and -data/-shapes includes) is assigned:
  - a feature-under-test (from the conformance suite's filename convention), and
  - a bucket:
      E = Expressible: direct nRQL/Racer counterpart under a fixed entailment
          regime + faithful substrate mirror.
      C = Conditional/lossy: expressible only if specific RDF-term structure is
          mirrored, or with a documented semantic caveat (cardinality w/o UNA,
          lexical via substrate string predicates, term-kind, language tags,
          closed shapes).
      N = Native residual: genuinely new / outside the nonrecursive NAF+projection
          fragment (unbounded regular paths; recursion).
      M = Meta/reporting: not a constraint-expressivity feature (deactivated,
          message, severity) -> the paper's "organizational" category.
Path tests are bucketed by actual operator content (N iff they use
zeroOrMorePath/oneOrMorePath), not by filename.
"""
import os, re, csv, collections

ROOT = "/tmp/data-shapes/data-shapes-test-suite/tests"
CORE_DIRS = ["core/node", "core/property", "core/path", "core/targets", "core/misc"]
COMPLEX_DIR = "core/complex"
SPARQL_DIRS = ["sparql/node", "sparql/property", "sparql/component", "sparql/pre-binding"]

# feature-key -> bucket. Longest-prefix match against the filename.
FEATURE_BUCKET = [
    # qualified (E for min, the disjoint variants test qualified counting)
    ("qualifiedValueShapesDisjoint", "E"), ("qualifiedMinCountDisjoint", "E"),
    ("qualifiedValueShape", "E"), ("qualified", "E"),
    # targets (all E)
    ("targetClassImplicit", "E"), ("targetClass", "E"), ("targetObjectsOf", "E"),
    ("targetSubjectsOf", "E"), ("targetNode", "E"), ("multipleTargets", "E"),
    # paths handled separately by operator content; keys here only for feature name
    ("path-zeroOrMore", "PATH"), ("path-oneOrMore", "PATH"), ("path-zeroOrOne", "PATH"),
    ("path-alternative", "PATH"), ("path-inverse", "PATH"),
    ("path-sequence-duplicate", "PATH"), ("path-sequence", "PATH"),
    ("path-complex", "PATH"), ("path-strange", "PATH"), ("path-unused", "PATH"),
    # value range (E: concrete-domain numeric predicates)
    ("minExclusive", "E"), ("maxExclusive", "E"), ("minInclusive", "E"), ("maxInclusive", "E"),
    # cardinality (C/lossy: counting without UNA)
    ("minCount", "E"), ("maxCount", "C"),
    # lexical / term (C)
    ("minLength", "C"), ("maxLength", "C"), ("pattern", "C"),
    ("nodeKind", "C"), ("languageIn", "C"), ("uniqueLang", "C"), ("closed", "C"),
    # comparison (E)
    ("lessThanOrEquals", "E"), ("lessThan", "E"),
    ("disjoint", "E"), ("equals", "E"),
    # core value/type (E)
    ("datatype", "E"), ("class", "E"), ("hasValue", "E"), ("in", "E"),
    # logic combinators (E)
    ("and", "E"), ("or", "E"), ("not", "E"), ("xone", "E"),
    # shape references / property shapes (E, nonrecursive in the suite)
    ("node", "E"), ("property", "E"),
    # meta/reporting (M)
    ("deactivated", "M"), ("message", "M"), ("severity", "M"),
]

def is_main_test(fn):
    if not fn.endswith(".ttl"):
        return False
    if fn == "manifest.ttl":
        return False
    if fn.endswith("-data.ttl") or fn.endswith("-shapes.ttl"):
        return False
    return True

def feature_of(fn):
    base = fn[:-4]  # strip .ttl
    for key, _ in FEATURE_BUCKET:
        if base.startswith(key):
            return key
    return None

def components_in(path):
    # Union components from the main test file and any sibling -shapes/-data includes,
    # because some tests place the shapes graph in a separate file.
    paths = [path]
    base = path[:-4]
    for suf in ("-shapes.ttl", "-data.ttl"):
        if os.path.exists(base + suf):
            paths.append(base + suf)
    comps = set()
    for p in paths:
        txt = open(p, encoding="utf-8", errors="replace").read()
        comps |= set(re.findall(r"sh:[A-Za-z]+", txt))
    return comps

rows = []
for d in CORE_DIRS:
    full = os.path.join(ROOT, d)
    for fn in sorted(os.listdir(full)):
        if not is_main_test(fn):
            continue
        path = os.path.join(full, fn)
        feat = feature_of(fn)
        bucket = dict(FEATURE_BUCKET).get(feat) if feat else None
        comps = components_in(path)
        if bucket == "PATH" or feat and feat.startswith("path-"):
            unbounded = ("sh:zeroOrMorePath" in comps) or ("sh:oneOrMorePath" in comps)
            bucket = "N" if unbounded else "E"
        if feat is None:
            bucket = "?"
            feat = "UNRECOGNIZED:" + fn
        rows.append((d, fn, feat, bucket, " ".join(sorted(comps))))

# --- report ---
print("=" * 78)
print("PER-FILE CODING (core constraint + target + path + misc tests)")
print("=" * 78)
bybucket = collections.Counter()
byfeat = collections.defaultdict(lambda: collections.Counter())
for d, fn, feat, bucket, comps in rows:
    bybucket[bucket] += 1
    byfeat[feat][bucket] += 1

print(f"\n{'feature':<30}{'bucket':<8}{'n'}")
print("-" * 46)
for feat in sorted(byfeat):
    for bucket, n in byfeat[feat].items():
        print(f"{feat:<30}{bucket:<8}{n}")

print("\n" + "=" * 78)
print("BUCKET TOTALS  (core/node + core/property + core/path + core/targets + core/misc)")
print("=" * 78)
total = sum(bybucket.values())
labels = {"E": "Expressible (direct)",
          "C": "Conditional / lossy (needs mirroring or caveat)",
          "N": "Native residual (unbounded paths / recursion)",
          "M": "Meta / reporting (organizational)",
          "?": "UNRECOGNIZED"}
for b in ["E", "C", "N", "M", "?"]:
    n = bybucket.get(b, 0)
    print(f"  {b}  {labels[b]:<48} {n:>3}  ({100*n/total:4.1f}%)")
print(f"     {'TOTAL':<48} {total:>3}")

# Constraint-only denominator (exclude M meta and targets, which are not constraints)
constraint_rows = [r for r in rows if r[3] in ("E", "C", "N") and not r[2].startswith(("target", "multipleTargets"))]
cc = collections.Counter(r[3] for r in constraint_rows)
ctot = sum(cc.values())
print("\n" + "=" * 78)
print("CONSTRAINT-ONLY DENOMINATOR (exclude targets + meta; node/property/path constraints)")
print("=" * 78)
for b in ["E", "C", "N"]:
    print(f"  {b}  {labels[b]:<48} {cc[b]:>3}  ({100*cc[b]/ctot:4.1f}%)")
print(f"     {'TOTAL':<48} {ctot:>3}")
print(f"\n  E+C (expressible, possibly with caveat): {cc['E']+cc['C']} / {ctot} = {100*(cc['E']+cc['C'])/ctot:.1f}%")
print(f"  N   (genuinely native to SHACL):         {cc['N']} / {ctot} = {100*cc['N']/ctot:.1f}%")

# complex + sparql, reported separately
print("\n" + "=" * 78)
print("REPORTED SEPARATELY")
print("=" * 78)
complex_files = [f for f in sorted(os.listdir(os.path.join(ROOT, COMPLEX_DIR))) if is_main_test(f)]
print(f"core/complex (composite, multi-component, incl. SHACL-of-SHACL recursion): {complex_files}")
sp = 0
for d in SPARQL_DIRS:
    full = os.path.join(ROOT, d)
    if os.path.isdir(full):
        sp += sum(1 for f in os.listdir(full) if is_main_test(f))
print(f"sparql/* (SHACL-SPARQL extension; conditional by construction): {sp} tests")

# write CSV audit trail
out = "/home/mike/claude/shacl-nrql/shacl_test_suite_coding.csv"
with open(out, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["dir", "file", "feature", "bucket", "sh_components_present"])
    w.writerows(rows)
print(f"\nAudit CSV written: {out}  ({len(rows)} coded tests)")
