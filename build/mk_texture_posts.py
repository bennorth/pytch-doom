import os

from PIL import Image

from build_logging import get_logger
from build_paths import image_path, images_dir
from texture_data import post_basename, texture_posts, textures, wad

logger = get_logger("mk_texture_posts")


def texture_image(wad, tx, scale=1):
    # Use an image way too big to avoid having to clip patches. Not
    # sure if that ever happens but anyway.
    canvas = Image.new("RGB", (640, 640))
    for p in tx.patches:
        pim = wad.patches[p.name].to_Image("RGBA")
        canvas.paste(pim, (p.x, p.y), mask=pim)
    im = canvas.crop((0, 0, tx.width, tx.height))
    return im.resize((tx.width * scale, tx.height * scale))


def full_height_texture_image(txname):
    img = texture_image(wad, textures[txname])
    wd, ht = img.size

    if ht < 128:
        support_img = texture_image(wad, textures["SUPPORT2"])
        full_img = Image.new("RGB", (wd, 128))
        for col0 in range(0, wd, 64):
            full_img.paste(support_img, (col0, 0, col0 + 64, 128))
        full_img.paste(img, (0, 128 - ht))
        img = full_img

    return img


def mk_texture_posts():
    os.makedirs(images_dir, exist_ok=True)

    posts = texture_posts()
    img_from_name = {}
    for tx, col in posts:
        if tx not in img_from_name:
            img_from_name[tx] = full_height_texture_image(tx)
        img = img_from_name[tx]
        post_img = img.crop((col, 0, col + 1, img.size[1]))
        post_img.save(image_path(post_basename(tx, col)))

    logger.info(f"wrote {len(posts)} files to {images_dir}/")


if __name__ == "__main__":
    mk_texture_posts()
