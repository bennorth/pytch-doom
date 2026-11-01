def on_segment(p, q, r):
    return (
        q[0] <= max(p[0], r[0])
        and q[0] >= min(p[0], r[0])
        and q[1] <= max(p[1], r[1])
        and q[1] >= min(p[1], r[1])
    )


def orientation(p, q, r):
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if val == 0:
        return 0
    elif val < 0:
        return -1
    else:
        return 1


# Line segments are [p1, q1] and [p2, q2]
def segments_intersect(p1, q1, p2, q2):
    o1 = orientation(p1, q1, p2)
    o2 = orientation(p1, q1, q2)
    o3 = orientation(p2, q2, p1)
    o4 = orientation(p2, q2, q1)

    # general case
    if o1 != o2 and o3 != o4:
        return True

    # special cases
    # p1, q1 and p2 are collinear and p2 lies on segment p1q1
    if o1 == 0 and on_segment(p1, p2, q1):
        return True

    # p1, q1 and q2 are collinear and q2 lies on segment p1q1
    if o2 == 0 and on_segment(p1, q2, q1):
        return True

    # p2, q2 and p1 are collinear and p1 lies on segment p2q2
    if o3 == 0 and on_segment(p2, p1, q2):
        return True

    # p2, q2 and q1 are collinear and q1 lies on segment p2q2
    if o4 == 0 and on_segment(p2, q1, q2):
        return True

    return False


def movement_ok(cur_pt, new_pt):
    block_x_idx = (cur_pt[0] - BLOCKMAP_XMIN) // BLOCKMAP_CELLSIZE
    block_y_idx = (cur_pt[1] - BLOCKMAP_YMIN) // BLOCKMAP_CELLSIZE
    allow_boundary_segs = blockmap_data[block_y_idx][block_x_idx]
    if allow_boundary_segs is None:
        return True
    for seg in allow_boundary_segs:
        if segments_intersect(cur_pt, new_pt, seg[0], seg[1]):
            return False
    return True
