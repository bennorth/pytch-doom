import os

import omg
from PIL import Image

from build_logging import get_logger
from build_paths import image_path, images_dir

logger = get_logger("mk_title_posts")

imwd, imht = 480, 360
colwd = 16


def mk_title_posts():
    titlepic = (
        omg.WAD("doom1.wad")
        .graphics["TITLEPIC"]
        .to_Image()
        .resize((imwd, imht))
    )

    os.makedirs(images_dir, exist_ok=True)

    for col0 in range(0, imwd, colwd):
        post_img = titlepic.crop((col0, 0, col0 + colwd, imht))
        basename = f"titlepic-post-{(col0 // colwd):02d}.png"
        post_img.save(image_path(basename))

    logger.info(f"wrote {imwd // colwd} files to {images_dir}/")


if __name__ == "__main__":
    mk_title_posts()
