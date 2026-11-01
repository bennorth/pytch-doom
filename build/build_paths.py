import os

# Where the build scripts write the Pytch project's images and code,
# relative to this build directory.

images_dir = "pytch-project/images"
code_fname = "pytch-project/code/pytch-doom.py"


def image_path(basename):
    return os.path.join(images_dir, basename)
