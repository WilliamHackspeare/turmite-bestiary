"""Render the curated turmite bestiary to PNGs."""
import colorsys, json, math, time
from PIL import Image

DX = (0, 1, 0, -1)
DY = (-1, 0, 1, 0)

def run_full(rule, w, h, max_steps):
    n = len(rule)
    turns = [1 if c == 'R' else -1 for c in rule]
    grid = bytearray(w * h)
    x, y, d = w // 2, h // 2, 0
    minx = maxx = x; miny = maxy = y
    visited = 0
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
            break
    return grid, (x, y), (minx, miny, maxx, maxy), step, visited

def palette(n, base_hue, hue_span=0.16, sat=0.72, v_lo=0.32, v_hi=0.97):
    """Background + (n-1) colors sweeping hue/value. Hues in [0,1)."""
    cols = [(13, 15, 20)]  # state 0: near-black
    if n == 2:
        r, g, b = colorsys.hsv_to_rgb(base_hue, sat, 0.95)
        return cols + [(int(r*255), int(g*255), int(b*255))]
    for k in range(1, n):
        t = (k - 1) / max(1, n - 2)
        h_ = (base_hue + hue_span * (t - 0.5)) % 1.0
        s_ = sat * (0.80 + 0.20 * t)
        v_ = v_lo + (v_hi - v_lo) * t
        r, g, b = colorsys.hsv_to_rgb(h_, s_, v_)
        cols.append((int(r*255), int(g*255), int(b*255)))
    return cols

def render(rule, steps_budget, base_hue, grid_side=2400, target=1000, tag=None):
    t0 = time.time()
    grid, ant, bbox, steps, visited = run_full(rule, grid_side, grid_side, steps_budget)
    minx, miny, maxx, maxy = bbox
    m = 3  # margin cells
    minx = max(0, minx - m); miny = max(0, miny - m)
    maxx = min(grid_side - 1, maxx + m); maxy = min(grid_side - 1, maxy + m)
    bw, bh = maxx - minx + 1, maxy - miny + 1

    n = len(rule)
    pal = palette(n, base_hue)
    img = Image.new('P', (bw, bh), 0)
    flat = bytearray(bw * bh)
    for yy in range(bh):
        row = grid[(miny + yy) * grid_side + minx:(miny + yy) * grid_side + minx + bw]
        flat[yy * bw:(yy + 1) * bw] = row
    img.putdata(flat)
    p = []
    for c in pal:
        p.extend(c)
    p.extend((255, 255, 255))  # index n = ant marker
    img.putpalette(p + [0] * (768 - len(p) - 3))
    # mark the ant
    ax, ay = ant[0] - minx, ant[1] - miny
    if 0 <= ax < bw and 0 <= ay < bh:
        img.putpixel((ax, ay), n)

    scale = max(1, target // max(bw, bh))
    if scale > 1:
        img = img.resize((bw * scale, bh * scale), Image.NEAREST)
    name = tag or rule
    img.save(f"art_{name}.png", optimize=True)
    meta = dict(rule=rule, states=n, steps=steps, visited=visited,
                bbox=[bw - 2*m, bh - 2*m], escaped=steps < steps_budget,
                px=list(img.size), file=f"art_{name}.png")
    print(f"{rule:14s} steps={steps:>9,} visited={visited:>8,} bbox={bw-2*m}x{bh-2*m} "
          f"scale={scale} {'ESCAPED' if meta['escaped'] else '':8s} ({time.time()-t0:.1f}s)", flush=True)
    return meta

GOLD, ROSE, CYAN, VIOLET, GREEN, AMBER, BLUE, MAGENTA = (
    0.11, 0.93, 0.52, 0.75, 0.36, 0.07, 0.60, 0.85)

SPECIMENS = [
    # (rule, steps, hue, tag)
    ("LR",            16_000,    AMBER,   "classic"),      # the original ant
    ("LLRL",          500_000,   CYAN,    "latebloom"),    # chaos ~300k then highway
    ("LLRR",          6_000_000, ROSE,    "cardioid"),     # symmetric slow builder
    ("LLLRRLLL",      600_000,   VIOLET,  "cage8"),        # 15x18 prison, 8 states
    ("RRRRRRRRLL",    600_000,   GREEN,   "cage10"),       # 13x14 prison, 10 states
    ("RLLLRLLLLRRL",  4_000_000, BLUE,    "bigspread"),    # 12-state giant
    ("LRRRRLLR",      3_000_000, MAGENTA, "spread8"),      # 8-state dense
    ("LRLLLR",        3_000_000, GOLD,    "spread6"),      # 6-state dense
    ("LLRLL",         3_000_000, CYAN,    "spread5"),      # 5-state dense
    ("RRLRRRLLLR",    800_000,   ROSE,    "latebloom10"),  # chaos ~570k then highway
    ("LLRRLRLRRLLL",  300_000,   GREEN,   "latebloom12"),  # 12-state, escapes ~149k
    ("LRRRRRLLR",     1_200_000, VIOLET,  "guest_square"), # reputed square-filler
    ("RRLLLRLLLRRR",  2_000_000, AMBER,   "guest_triangle"), # reputed triangle-builder
]

metas = []
for rule, steps, hue, tag in SPECIMENS:
    metas.append(render(rule, steps, hue, tag=tag))

with open("bestiary.json", "w") as f:
    json.dump(metas, f, indent=1)
print("\ndone")
