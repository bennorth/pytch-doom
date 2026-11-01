import contextlib
import os
import sys

from PIL import Image

from build_logging import get_logger
from build_paths import code_fname, image_path
from mk_allowzone_data import (
    blockmap_data,
    blockmap_sz,
    movement_step_sz,
    xmin as blockmap_xmin,
    ymin as blockmap_ymin,
)
from pd_data import dump_data
from texture_data import costume_fnames, tx_data_by_id

logger = get_logger("mk_pytch_code")

tx_data_by_id = tx_data_by_id()
costume_fnames = costume_fnames()

MAP_SCALE_SIZE = 1 / 9


def write_pytch_code():
    """Write the "flat" Pytch program to stdout."""
    print("import pytch")
    print("pytch.set_max_import_loop_iterations(10000)")

    print(f"\nMAP_SCALE_SIZE = {MAP_SCALE_SIZE}")

    map_img = Image.open(image_path("simplified-map.png"))
    map_img_wd, map_img_ht = map_img.size

    print(f"\nMAP_SCALED_IMG_WD = {map_img_wd * MAP_SCALE_SIZE}")
    print(f"MAP_SCALED_IMG_HT = {map_img_ht * MAP_SCALE_SIZE}\n")

    with open("pytchdoom/render_bsp.py", "rt") as f_in:
        for line in f_in:
            if line.startswith("from pytchdoom.pddata_generated import"):
                map_bbox = dump_data(tx_data_by_id["id_from_name"])
            else:
                sys.stdout.write(line)

    print(f"\nMAP_XMIN = {map_bbox[2]}")
    print(f"MAP_WD = {map_bbox[3] - map_bbox[2]}")
    print(f"MAP_YMIN = {map_bbox[1]}")
    print(f"MAP_HT = {map_bbox[0] - map_bbox[1]}\n")

    print(f"TX_DATA = {tx_data_by_id['data']}\n\n")

    print(f"MOVEMENT_STEP_SZ = {movement_step_sz}")
    print(f"BLOCKMAP_XMIN = {blockmap_xmin}")
    print(f"BLOCKMAP_YMIN = {blockmap_ymin}")
    print(f"BLOCKMAP_CELLSIZE = {blockmap_sz}")
    print("blockmap_data = [")

    for row_data in blockmap_data:
        n_prev_Nones = 0
        print("    [", end="")
        for cell_data in row_data:
            if len(cell_data) == 0:
                if n_prev_Nones == 0:
                    print("\n        None,", end="")
                    n_prev_Nones += 1
                else:
                    print(" None,", end="")
                    n_prev_Nones += 1
                    if n_prev_Nones == 12:
                        n_prev_Nones = 0
            else:
                n_prev_Nones = 0
                print(f"\n        {cell_data},", end="")
        print("\n    ],")
    print("]\n")

    with open("pytchdoom/allowzone.py", "rt") as f_in:
        for line in f_in:
            sys.stdout.write(line)

    with open("pytchdoom/sprites.py", "rt") as f_in:
        for line in f_in:
            if line.startswith("    Costumes = []") and line.strip().endswith(
                "TO FILL"
            ):
                print(f"    Costumes = {costume_fnames}")
            else:
                sys.stdout.write(line)


if __name__ == "__main__":
    os.makedirs(os.path.dirname(code_fname), exist_ok=True)
    with open(code_fname, "wt") as f_out, contextlib.redirect_stdout(f_out):
        write_pytch_code()
    logger.info(f"wrote {code_fname}")
