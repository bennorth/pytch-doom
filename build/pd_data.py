import omg

from pd_prune_segs import prune_segs

########################################################################


def dump_data(tx_id_from_name):
    wad = omg.WAD()
    wad.from_file("doom1.wad")

    map_lumps = wad.maps["E1M3"]
    map_e1m3 = omg.MapEditor(from_lumps=map_lumps)

    map_xmin = map_ymin = 10000
    map_xmax = map_ymax = -10000
    print(
        """
K_VERTEX_X = 0
K_VERTEX_Y = 1"""
    )
    n_in_row = 8
    print("map_vertexes = [", end="")
    for v in map_e1m3.vertexes:
        if n_in_row == 8:
            print("\n   ", end="")
            n_in_row = 0
        print(f" [{v.x}, {v.y}],", end="")
        n_in_row += 1
        if v.x > map_xmax:
            map_xmax = v.x
        if v.x < map_xmin:
            map_xmin = v.x
        if v.y > map_ymax:
            map_ymax = v.y
        if v.y < map_ymin:
            map_ymin = v.y
    print("]")

    print(
        """
K_NODE_X0 = 0
K_NODE_Y0 = 1
K_NODE_XT = 2
K_NODE_YT = 3
K_NODE_L_BBOX_T = 4
K_NODE_L_BBOX_B = 5
K_NODE_L_BBOX_L = 6
K_NODE_L_BBOX_R = 7
K_NODE_R_BBOX_T = 8
K_NODE_R_BBOX_B = 9
K_NODE_R_BBOX_L = 10
K_NODE_R_BBOX_R = 11
K_NODE_L_IDX = 12
K_NODE_R_IDX = 13"""
    )
    print("map_nodes = [")
    for n in map_e1m3.nodes:
        print(
            f"    [{n.x_start}, {n.y_start}, {n.x_vector}, {n.y_vector},",
            f"{n.left_bbox_top}, {n.left_bbox_bottom},",
            f"{n.left_bbox_left}, {n.left_bbox_right},",
            f"{n.right_bbox_top}, {n.right_bbox_bottom},",
            f"{n.right_bbox_left}, {n.right_bbox_right},",
            f"{n.left_index}, {n.right_index}],",
        )
    print("]")

    pruned_segs, pruned_ssectors = prune_segs(map_e1m3)

    print(
        """
K_SSECTOR_IDX0 = 0
K_SSECTOR_NSEGS = 1"""
    )
    print("map_ssectors = [", end="")
    n_in_row = 8
    for ss in pruned_ssectors:
        if n_in_row == 8:
            print("\n   ", end="")
            n_in_row = 0
        print(f" [{ss.seg_a}, {ss.numsegs}],", end="")
        n_in_row += 1
    print("]")

    # Tangent and normal vectors, and normal angle, computed on load.
    print(
        """
K_SEG_FRONT_TX = 0
K_SEG_VX1 = 1
K_SEG_VX2 = 2
K_SEG_OFFSET = 3
K_SEG_TANGENT_X = 4
K_SEG_TANGENT_Y = 5
K_SEG_NORMAL_X = 6
K_SEG_NORMAL_Y = 7
K_SEG_NORMAL_TH = 8"""
    )
    print("map_segs = [", end="")
    n_in_row = 5
    for s in pruned_segs:
        tx_offset = 0
        linedef = map_e1m3.linedefs[s.line]
        if linedef.back != 65535:
            tx = None
        else:
            sidedef = map_e1m3.sidedefs[linedef.front]
            tx_mid = sidedef.tx_mid
            if tx_mid == "-":
                tx = None
            else:
                tx = tx_mid
                tx_offset = sidedef.off_x + s.offset
        tx_id = tx_id_from_name[tx]
        if n_in_row == 5:
            print("\n   ", end="")
            n_in_row = 0
        print(f" [{tx_id}, {s.vx_a}, {s.vx_b}, {tx_offset}],", end="")
        n_in_row += 1
    print("]")

    return (map_ymax, map_ymin, map_xmin, map_xmax)
