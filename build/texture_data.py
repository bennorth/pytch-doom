import omg
import omg.txdef

# Data about the wall textures used by E1M3, computed from the texture
# definitions alone.  Each column of each texture becomes one Pytch
# costume (a 1-pixel-wide "post" image, written by mk_texture_posts).
# The order of those costumes is defined here, by texture_posts(), and
# both the costume filenames and TX_DATA's costume indices follow it.

wad = omg.WAD()
wad.from_file("doom1.wad")

textures = omg.txdef.Textures(wad.txdefs)
map_e1m3 = omg.MapEditor(from_lumps=wad.maps["E1M3"])


def used_texture_names():
    names = set()
    for seg in map_e1m3.segs:
        ld = map_e1m3.linedefs[seg.line]
        if ld.back == 65535:
            sd = map_e1m3.sidedefs[ld.front]
            if sd.tx_mid != "-":
                names.add(sd.tx_mid)
    return sorted(names)


def texture_posts():
    """List of (texture name, column) pairs, in costume order."""
    return [
        (tx, col)
        for tx in used_texture_names()
        for col in range(textures[tx].width)
    ]


def post_basename(tx, col):
    return f"{tx}-{col:03d}.png"


def costume_fnames():
    return [post_basename(tx, col) for (tx, col) in texture_posts()]


def tx_data_by_id():
    tx_data = [0, 0]
    tx_id_from_name = {None: 0}
    costume_idx = 0
    for tx in used_texture_names():
        wd = textures[tx].width
        tx_id_from_name[tx] = len(tx_data)
        tx_data.append(costume_idx)
        tx_data.append(wd)
        costume_idx += wd
    return {
        "data": tx_data,
        "id_from_name": tx_id_from_name,
    }
