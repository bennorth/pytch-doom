import sys

import omg


def prune_segs(mapinfo):
    exp_seg_0 = None
    for si, ss in enumerate(mapinfo.ssectors):
        sfx = ""
        if exp_seg_0 is not None:
            if exp_seg_0 != ss.seg_a:
                raise RuntimeError(
                    f"{si=} exp={exp_seg_0} {ss.seg_a=} {ss.numsegs=}{sfx}"
                )
        exp_seg_0 = ss.seg_a + ss.numsegs

    pruned_segs = []
    new_seg_idx_f_old = []
    for s in mapinfo.segs:
        new_seg_idx_f_old.append(len(pruned_segs))

        tx_offset = 0
        linedef = mapinfo.linedefs[s.line]
        if linedef.back == 65535:
            sidedef = mapinfo.sidedefs[linedef.front]
            tx_mid = sidedef.tx_mid
            if tx_mid != "-":
                pruned_segs.append(s)
    new_seg_idx_f_old.append(len(pruned_segs))

    pruned_ssectors = []
    for ss in mapinfo.ssectors:
        new_seg_idx = new_seg_idx_f_old[ss.seg_a]
        next_seg_idx = new_seg_idx_f_old[ss.seg_a + ss.numsegs]
        nsegs = next_seg_idx - new_seg_idx
        pruned_ssectors.append(omg.SubSector(nsegs, new_seg_idx))

    return pruned_segs, pruned_ssectors


if __name__ == "__main__":
    wad = omg.WAD()
    wad.from_file("doom1.wad")

    map_lumps = wad.maps["E1M3"]
    map_e1m3 = omg.MapEditor(from_lumps=map_lumps)

    prune_segs(map_e1m3)
