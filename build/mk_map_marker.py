import math
import os
import sys

from PIL import Image

from build_logging import get_logger
from build_paths import image_path

logger = get_logger("mk_map_marker")

# Player marker for the map overlay: a disc at the player's position,
# with a 90-degree field-of-view wedge pointing up and to the right.
# The wedge is filled with yellow whose alpha falls off with distance
# from the apex.
#
# Coordinates are continuous, with pixel (x, y) covering the square
# from (x, y) to (x + 1, y + 1).  The disc and the wedge's apex are
# both at the image centre, so the marker rotates about the right
# point.  The 1px edge lines sit just inside the wedge.

size = 64
yellow = (255, 255, 0)

centre = size / 2

# Alpha falloff: 255 * (1 - r / falloff_radius) ** falloff_power.
falloff_radius = 51.0
falloff_power = 2.4

disc_radius = 8.0

im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
px = im.load()

for y in range(size):
    for x in range(size):
        dx = (x + 0.5) - centre
        dy = centre - (y + 0.5)
        r = math.hypot(dx, dy)

        if r <= disc_radius:
            alpha = 255
        elif dx < 0 or dy < 0:
            alpha = 0
        elif dx < 1 or dy < 1:
            # Edge lines: the first pixel column / row inside the wedge.
            alpha = 255
        else:
            t = max(0.0, 1.0 - r / falloff_radius)
            alpha = round(255 * t**falloff_power)

        if alpha > 0:
            px[x, y] = yellow + (alpha,)

out_fname = sys.argv[1] if len(sys.argv) > 1 else image_path("map-marker.png")
os.makedirs(os.path.dirname(out_fname) or ".", exist_ok=True)
im.save(out_fname)
logger.info(f"wrote {out_fname}")
