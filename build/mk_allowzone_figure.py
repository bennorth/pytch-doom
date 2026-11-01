import io
import os
import sys

import matplotlib.pyplot as plt
import omg
from PIL import Image
import shapely
from shapely.geometry import LinearRing, Polygon
from shapely.plotting import plot_polygon

from build_logging import get_logger
from build_paths import image_path

logger = get_logger("mk_simple_map")

out_fname = sys.argv[1] if len(sys.argv) > 1 else "blog-figures/allowzone-detail-0.png"
os.makedirs(os.path.dirname(out_fname) or ".", exist_ok=True)

want_solid = (len(sys.argv) > 2) and (sys.argv[2] == "solid")

wad = omg.WAD()
wad.from_file("doom1.wad")
map_e1m3 = omg.MapEditor(from_lumps=wad.maps["E1M3"])

# Chain one-sided linedefs into closed loops of vertices.
one_sided_lines = [ld for ld in map_e1m3.linedefs if ld.back == 65535]
line_from_v1 = {ld.vx_a: ld for ld in one_sided_lines}

pending_lines = one_sided_lines[:]
vertex_loops = []
while pending_lines:
    ld = pending_lines.pop(0)
    vertex_loop = [ld.vx_a, ld.vx_b]
    cur_vx = ld.vx_b
    while True:
        next_ld = line_from_v1[cur_vx]
        pending_lines.remove(next_ld)
        cur_vx = next_ld.vx_b

        # Fudge for weirdness in map:
        if cur_vx == 771: cur_vx = 764

        if cur_vx == vertex_loop[0]:
            break
        vertex_loop.append(cur_vx)
    vertex_loops.append(vertex_loop)

lrs = [
    LinearRing([(map_e1m3.vertexes[vx].x, map_e1m3.vertexes[vx].y) for vx in vloop])
    for vloop in vertex_loops
]
level_polygon = Polygon(lrs[0], lrs[1:])

fig, ax = plt.subplots(1, figsize=(12.0, 12.0))

style_kwargs = {
    "facecolor": "#8a4", "edgecolor": "#793", "lw": 0.5
}

plot_polygon(
    level_polygon,
    ax=ax,
    add_points=False,
    facecolor="#8a4",
    edgecolor="none",
    lw=0.5
)
plot_polygon(
    shapely.buffer(level_polygon, -16, quad_segs=1),
    ax=ax,
    add_points=False,
    facecolor="none",
    edgecolor="#000",
    lw=3.0
)
ax.set_aspect(1)
ax.set_xlim(-1700, -900)
ax.set_ylim(-2820, -2020)
ax.set_axis_off()

buf = io.BytesIO()
fig.savefig(buf, dpi=300, transparent=True)
buf.seek(0)

img = Image.open(buf)
img.crop(img.getbbox()).save(out_fname)
logger.info(f"wrote {out_fname}")
