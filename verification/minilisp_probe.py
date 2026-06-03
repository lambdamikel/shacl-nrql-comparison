#!/usr/bin/env python3
"""Characterize RacerPro's MiniLisp -- the lambda/:reject escape hatch.

This is what corrected the paper's section 5.5: the hatch is NOT Turing-complete.
It is a deliberately termination-safe sandbox (see source/expressions.lisp in the
Racer sources: call-function aborts recursion "to ensure termination", and
+allowed-cl-functions+ is a curated whitelist). There is no regex engine, so a
general sh:pattern is not expressible even via the hatch.

Run a RacerPro 2.0 server on TCP 8088, then: python3 minilisp_probe.py
Each probe uses a fresh connection so a hang cannot cascade.
"""
import socket

def probe(cmd, t=7):
    try:
        s = socket.create_connection(("127.0.0.1", 8088), timeout=8)
        s.settimeout(t)
        s.sendall((cmd + "\n").encode())
        buf = b""
        while True:
            ch = s.recv(1)
            if not ch:
                break
            if ch == b"\r" and buf:
                break
            if ch in (b"\r", b"\n"):
                continue
            buf += ch
        s.close()
        fr = buf.decode("latin-1")
        return fr.split(" ", 2)[-1] if fr.startswith(":") else fr
    except socket.timeout:
        return "<<timeout/hang>>"
    except Exception as e:
        return f"<<{e}>>"

PROBES = [
    # present (termination-safe functional core + string ops + KB callbacks):
    "(evaluate (+ 1 2 3))",
    '(evaluate (search "Joh" "Johann"))',     # substring search -> 0 (match index)
    '(evaluate (search "Joh" "Maria"))',      # -> nil (no match)
    '(evaluate (subseq "Johann" 0 3))',
    '(evaluate (elt "Johann" 0))',
    '(evaluate (length "Johann"))',
    '(evaluate (format nil "~a-~a" 1 2))',
    "(evaluate (reduce + (list 1 2 3)))",
    "(evaluate (dotimes (i 3 i) i))",         # bounded iteration only
    # ABSENT (the restriction that guarantees termination / blocks regex):
    "(evaluate (require :regexp2))",          # no module loading
    "(evaluate (excl:match-re \"x\" \"x\"))", # no regex engine
    "(evaluate (loop for i from 1 to 3 sum i))",
    "(evaluate (funcall (lambda (x) x) 1))",
    "(evaluate (mapcar (lambda (x) x) (list 1)))",
]

if __name__ == "__main__":
    for c in PROBES:
        print(f"{c:50} => {probe(c)}")
