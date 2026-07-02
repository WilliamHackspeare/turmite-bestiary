"""A census of turmites: every L/R rule string of length 2-6.

Rule semantics (classic multi-state Langton's ant):
  - Grid cells hold a state in [0, n). All start at 0.
  - On a cell in state s: turn rule[s] (L or R), flip cell to (s+1) % n, step forward.
Classic Langton's ant is "RL".
"""
import itertools, json, math, time

W = H = 1200          # sweep grid
STEPS = 400_000       # sweep budget per rule

DX = (0, 1, 0, -1)    # N, E, S, W
DY = (-1, 0, 1, 0)

def run(rule, w, h, max_steps, checkpoints=8):
    n = len(rule)
    turns = [1 if c == 'R' else -1 for c in rule]
    grid = bytearray(w * h)
    x, y, d = w // 2, h // 2, 0
    ox, oy = x, y
    minx = maxx = x; miny = maxy = y
    visited = 0
    traj = []  # (step, displacement) checkpoints
    ckpt = max(1, max_steps // checkpoints)
    dx, dy = DX, DY
    step = 0
    while step < max_steps:
        i = y * w + x
        s = grid[i]
        d = (d + turns[s]) & 3
        if s == 0:
            visited += 1
        grid[i] = (s + 1) % n
        x += dx[d]; y += dy[d]
        step += 1
        if x < minx: minx = x
        elif x > maxx: maxx = x
        if y < miny: miny = y
        elif y > maxy: maxy = y
        if x <= 0 or x >= w - 1 or y <= 0 or y >= h - 1:
            traj.append((step, math.hypot(x - ox, y - oy)))
            return dict(escaped=True, steps=step, visited=visited,
                        bbox=(maxx - minx + 1, maxy - miny + 1), traj=traj)
        if step % ckpt == 0:
            traj.append((step, math.hypot(x - ox, y - oy)))
    return dict(escaped=False, steps=step, visited=visited,
                bbox=(maxx - minx + 1, maxy - miny + 1), traj=traj)

def classify(r):
    """Rough behavioral taxonomy from the stats."""
    w, h = r['bbox']
    area = w * h
    disp = r['traj'][-1][1] if r['traj'] else 0.0
    if r['escaped'] and disp / r['steps'] > 0.005:
        return 'highway'          # ballistic escape
    if not r['escaped'] and area < 400:
        return 'bounded'          # tiny cage / periodic
    # growth exponent of displacement vs steps over the checkpoints
    if len(r['traj']) >= 3:
        (s1, d1), (s2, d2) = r['traj'][len(r['traj'])//2], r['traj'][-1]
        if d1 > 2 and d2 > 2 and s2 > s1:
            alpha = math.log(d2 / d1) / math.log(s2 / s1)
            if alpha > 0.8:
                return 'highway-ish'
    dens = r['visited'] / max(1, area)
    return 'chaotic-dense' if dens > 0.55 else 'chaotic'

def canonical(rule):
    # L<->R swap is a mirror image; keep one representative
    mirror = rule.translate(str.maketrans('LR', 'RL'))
    return min(rule, mirror)

def main():
    rules = []
    for n in range(2, 7):
        for combo in itertools.product('LR', repeat=n):
            r = ''.join(combo)
            if len(set(r)) == 1:
                continue  # all-L / all-R just spins in a circle of 4 cells... skip
            if canonical(r) != r:
                continue
            rules.append(r)

    print(f"{len(rules)} canonical rules to run\n", flush=True)
    t0 = time.time()
    results = {}
    for i, rule in enumerate(rules):
        r = run(rule, W, H, STEPS)
        r['class'] = classify(r)
        results[rule] = r
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(rules)} done ({time.time()-t0:.0f}s)", flush=True)

    print(f"\nTotal {time.time()-t0:.0f}s\n")

    by_class = {}
    for rule, r in results.items():
        by_class.setdefault(r['class'], []).append(rule)

    for cls, rs in sorted(by_class.items()):
        print(f"{cls}: {len(rs)}")
        for rule in rs:
            r = results[rule]
            print(f"   {rule:8s} bbox={r['bbox'][0]}x{r['bbox'][1]:<5} visited={r['visited']:<7} "
                  f"steps={r['steps']:<7} {'ESCAPED' if r['escaped'] else ''}")

    with open('census.json', 'w') as f:
        json.dump({k: {kk: vv for kk, vv in v.items() if kk != 'traj'}
                   for k, v in results.items()}, f, indent=1)

if __name__ == '__main__':
    main()
