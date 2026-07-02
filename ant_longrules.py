"""Prospecting expedition: random longer rule strings (8-12 states)."""
import random, time
from ant_census import run, classify

random.seed(20260702)  # today, for reproducibility

candidates = set()
for n in (8, 10, 12):
    while len([c for c in candidates if len(c) == n]) < 60:
        r = ''.join(random.choice('LR') for _ in range(n))
        if len(set(r)) > 1:
            candidates.add(r)

t0 = time.time()
rows = []
for i, rule in enumerate(sorted(candidates)):
    r = run(rule, 1200, 1200, 600_000)
    r['class'] = classify(r)
    rows.append((rule, r))
    if (i + 1) % 30 == 0:
        print(f"  {i+1}/{len(candidates)} ({time.time()-t0:.0f}s)", flush=True)

print(f"\nTotal {time.time()-t0:.0f}s\n")
# surface the outliers: bounded cages, highways, and unusually big/small footprints
for rule, r in rows:
    w, h = r['bbox']
    interesting = (
        r['class'] in ('bounded', 'highway', 'highway-ish')
        or w * h > 90_000        # unusually expansive
        or (w * h < 1600 and not r['escaped'])  # unusually caged
        or r['escaped']
    )
    if interesting:
        print(f"{rule:14s} {r['class']:14s} bbox={w}x{h:<5} visited={r['visited']:<7} "
              f"steps={r['steps']:<7} {'ESCAPED' if r['escaped'] else ''}")
