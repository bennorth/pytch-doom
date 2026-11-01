import os
import sys

import numpy as np
import omg
from PIL import Image

from build_logging import get_logger
from build_paths import image_path

logger = get_logger("mk_doom_frame")

# Screen border for the Pytch stage: Doom's back-screen flat, tiled,
# with Doom's bevel patches (BRDR_*) around a transparent hole where
# the 3D view goes.  Laid out as vanilla Doom's R_FillBackScreen()
# does: each bevel strip is 3 Doom pixels wide, directly outside the
# view, with the edge patches repeating every 8 Doom pixels starting
# from the view's top-left corner.
#
# We work out the colour at many sample points per output pixel by
# mapping back into Doom pixels, then average.  This gives clean
# results with non-integer scale factors.

stage_wd, stage_ht = 480, 360
hole_x0, hole_y0 = 80, 60
hole_wd, hole_ht = 320, 240

# Output pixels per Doom pixel.  Doom's 320x200 screen is displayed
# at 4:3, so a Doom pixel is 1.2 times as tall as it is wide.  With
# 2.0, the hole is exactly 160x100 Doom pixels.
scale_x = 2.0
scale_y = 1.2 * scale_x

# Which point of the tiled flat (in Doom pixels) is at the stage's
# top-left corner.  Doom tiles it from the screen's top-left corner.
flat_phase_x, flat_phase_y = 0, 0

bevel_wd = 3
supersample = 4

wad = omg.WAD()
wad.from_file("doom1.wad")

flat = np.array(wad.flats["FLOOR7_2"].to_Image("RGB"))
patches = {
    name: np.array(wad.graphics[f"BRDR_{name}"].to_Image("RGB"))
    for name in ["T", "B", "L", "R", "TL", "TR", "BL", "BR"]
}


def sample_coords(n_out, out_0, scale, n_hole_out):
    """Return per-sample coordinates, in Doom pixels, along one axis.

    The returned dict holds the coordinate relative to the start of
    the stage (for the flat), plus masks and patch indices for the
    near-side bevel, the hole, and the far-side bevel.
    """
    pos = (np.arange(n_out * supersample) + 0.5) / supersample
    t = (pos - out_0) / scale
    t_end = n_hole_out / scale
    return {
        "stage": pos / scale,
        "near": (t >= -bevel_wd) & (t < 0),
        "hole": (t >= 0) & (t < t_end),
        "far": (t >= t_end) & (t < t_end + bevel_wd),
        "near_idx": np.clip(np.floor(t + bevel_wd).astype(int), 0, bevel_wd - 1),
        "far_idx": np.clip(np.floor(t - t_end).astype(int), 0, bevel_wd - 1),
        "along_idx": np.floor(t).astype(int) % 8,
    }


xs = sample_coords(stage_wd, hole_x0, scale_x, hole_wd)
ys = sample_coords(stage_ht, hole_y0, scale_y, hole_ht)

flat_cols = np.floor(xs["stage"] + flat_phase_x).astype(int) % 64
flat_rows = np.floor(ys["stage"] + flat_phase_y).astype(int) % 64
rgb = flat[np.ix_(flat_rows, flat_cols)]


def paint(patch, y_mask, row_idx, x_mask, col_idx):
    rgb[np.ix_(y_mask, x_mask)] = patch[np.ix_(row_idx[y_mask], col_idx[x_mask])]


paint(patches["T"], ys["near"], ys["near_idx"], xs["hole"], xs["along_idx"])
paint(patches["B"], ys["far"], ys["far_idx"], xs["hole"], xs["along_idx"])
paint(patches["L"], ys["hole"], ys["along_idx"], xs["near"], xs["near_idx"])
paint(patches["R"], ys["hole"], ys["along_idx"], xs["far"], xs["far_idx"])
paint(patches["TL"], ys["near"], ys["near_idx"], xs["near"], xs["near_idx"])
paint(patches["TR"], ys["near"], ys["near_idx"], xs["far"], xs["far_idx"])
paint(patches["BL"], ys["far"], ys["far_idx"], xs["near"], xs["near_idx"])
paint(patches["BR"], ys["far"], ys["far_idx"], xs["far"], xs["far_idx"])

alpha = np.full(rgb.shape[:2] + (1,), 255, dtype=np.uint8)
alpha[np.ix_(ys["hole"], xs["hole"])] = 0
rgba = np.concatenate([rgb, alpha], axis=2).astype(float)

# Average each supersample x supersample block to one output pixel.
rgba = rgba.reshape(stage_ht, supersample, stage_wd, supersample, 4).mean(axis=(1, 3))
rgba = np.round(rgba).astype(np.uint8)

# Hole edges fall on whole output pixels, so the hole is cleanly cut.
im = Image.fromarray(rgba, "RGBA")
im.paste((0, 0, 0, 0), (hole_x0, hole_y0, hole_x0 + hole_wd, hole_y0 + hole_ht))

out_fname = sys.argv[1] if len(sys.argv) > 1 else image_path("doom-frame.png")
os.makedirs(os.path.dirname(out_fname) or ".", exist_ok=True)
im.save(out_fname)
logger.info(f"wrote {out_fname}")
