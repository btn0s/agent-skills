#!/bin/bash
# Builds ~/dev/perf-demo: dedupe() is O(n^2) on main, O(n) on perf/dedupe-set.
set -e
R=~/dev/perf-demo
rm -rf "$R"; mkdir -p "$R"; cd "$R"
git init -q -b main
git config user.name "proof demo"; git config user.email "proof@devbox"; git config color.ui always
cat > dedupe.py <<'PY'
def dedupe(items):
    """Drop repeats, keep first-seen order."""
    out = []
    for x in items:
        if x not in out:
            out.append(x)
    return out
PY
cat > test_dedupe.py <<'PY'
import unittest
from dedupe import dedupe

class DedupeTest(unittest.TestCase):
    def test_order(self):
        self.assertEqual(dedupe([3, 1, 3, 2, 1]), [3, 1, 2])
    def test_empty(self):
        self.assertEqual(dedupe([]), [])
    def test_strings(self):
        self.assertEqual(dedupe(list("banana")), ["b", "a", "n"])
PY
cat > bench.py <<'PY'
"""Time dedupe() from two git refs on identical inputs; print a table and write bench.json."""
import json, random, subprocess, sys, time

REFS = sys.argv[1:] or ["main", "HEAD"]
SIZES = [1000, 2000, 4000, 8000, 16000]

def load(ref):
    ns = {}
    exec(subprocess.check_output(["git", "show", f"{ref}:dedupe.py"], text=True), ns)
    return ns["dedupe"]

def best_ms(fn, data, reps=3):
    t = []
    for _ in range(reps):
        s = time.perf_counter(); fn(data); t.append(time.perf_counter() - s)
    return min(t) * 1000

rng = random.Random(1)
fns = {ref: load(ref) for ref in REFS}
res = {ref: [] for ref in REFS}
print(f"{'n':>7}" + "".join(f"{r:>22}" for r in REFS) + f"{'speedup':>10}")
for n in SIZES:
    data = [rng.randrange(n // 2) for _ in range(n)]
    for ref, fn in fns.items():
        res[ref].append(round(best_ms(fn, data), 3))
    a, b = res[REFS[0]][-1], res[REFS[-1]][-1]
    print(f"{n:>7}" + "".join(f"{res[r][-1]:>19.2f} ms" for r in REFS) + f"{a / b:>9.0f}x")
json.dump({"x": SIZES, "series": res, "unit": "ms"}, open("bench.json", "w"))
PY
echo bench.json > .gitignore
git add -A; git commit -qm "dedupe: initial"
git switch -qc perf/dedupe-set
cat > dedupe.py <<'PY'
def dedupe(items):
    """Drop repeats, keep first-seen order."""
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out
PY
git commit -qam "dedupe: track seen items in a set (O(n))"
git switch -q main
echo "built $R"
