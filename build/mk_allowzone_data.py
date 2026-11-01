import math

import omg
import shapely
from shapely.geometry import LinearRing, Polygon

########################################################################

blockmap_sz = 192
movement_step_sz = 6

########################################################################

wad = omg.WAD()
wad.from_file("doom1.wad")

map_lumps = wad.maps["E1M3"]
map_e1m3 = omg.MapEditor(from_lumps=map_lumps)

one_sided_lines = [ld for ld in map_e1m3.linedefs if ld.back == 65535]

line_from_v1 = {ld.vx_a: ld for ld in one_sided_lines}

pending_lines = one_sided_lines[:]
vertex_loops = []
while pending_lines:
    ld = pending_lines.pop(0)
    vertex_loop = [ld.vx_a, ld.vx_b]
    cur_vx = ld.vx_b
    closed = False
    # print("new loop", vertex_loop)
    while not closed:
        next_ld = line_from_v1[cur_vx]
        # print("next line", next_ld)
        pending_lines.remove(next_ld)
        cur_vx = next_ld.vx_b

        # Fudge for weirdness in map:
        if cur_vx == 771:
            cur_vx = 764

        if cur_vx == vertex_loop[0]:
            closed = True
        else:
            vertex_loop.append(cur_vx)
    vertex_loops.append(vertex_loop)

lrs = [
    LinearRing([(map_e1m3.vertexes[vx].x, map_e1m3.vertexes[vx].y) for vx in vloop])
    for vloop in vertex_loops
]

level_polygon = Polygon(lrs[0], lrs[1:])

allow_region = shapely.buffer(level_polygon, -16, quad_segs=1)


def segs_of_coord_loop(coords):
    coords = list(coords)
    return list(zip(coords, coords[1:]))


def segs_in_geom(geom):
    if isinstance(geom, (shapely.MultiPolygon, shapely.GeometryCollection)):
        return sum((segs_in_geom(g1) for g1 in geom.geoms), [])
    if isinstance(geom, shapely.Polygon):
        return segs_of_coord_loop(geom.exterior.coords) + sum(
            (segs_of_coord_loop(hole.coords) for hole in geom.interiors), []
        )
    if isinstance(geom, (shapely.LineString, shapely.Point)):
        # Don't count these, for purposes of what lines we'll
        # need to do intersection tests against.
        return []
    raise RuntimeError(f"unk geom {type(geom)}")


bbox_corners = list(allow_region.envelope.exterior.normalize().coords)
xmin, ymin = bbox_corners[0]
xmax, ymax = bbox_corners[2]


xmin = int(math.floor(xmin / blockmap_sz) * blockmap_sz)
xmax = int(math.ceil(xmax / blockmap_sz) * blockmap_sz)
ymin = int(math.floor(ymin / blockmap_sz) * blockmap_sz)
ymax = int(math.ceil(ymax / blockmap_sz) * blockmap_sz)


allowmap_segs = segs_in_geom(allow_region)
allowmap_linestrings = [shapely.LineString(seg) for seg in allowmap_segs]

blockmap_data = []
for cell_ymin in range(ymin, ymax, blockmap_sz):
    cell_ymax = cell_ymin + blockmap_sz
    row_data = []
    for cell_xmin in range(xmin, xmax, blockmap_sz):
        cell_xmax = cell_xmin + blockmap_sz

        buffered_xmin = cell_xmin - movement_step_sz
        buffered_xmax = cell_xmax + movement_step_sz
        buffered_ymin = cell_ymin - movement_step_sz
        buffered_ymax = cell_ymax + movement_step_sz

        blockmap_cell = shapely.Polygon(
            [
                (buffered_xmin, buffered_ymin),
                (buffered_xmin, buffered_ymax),
                (buffered_xmax, buffered_ymax),
                (buffered_xmax, buffered_ymin),
            ]
        )
        datum = []
        for map_ls in allowmap_linestrings:
            if not shapely.intersection(blockmap_cell, map_ls).is_empty:
                datum.append(list(map_ls.coords))

        row_data.append(datum)
    blockmap_data.append(row_data)
