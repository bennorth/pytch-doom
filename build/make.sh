#!/bin/bash
#
# Build Pytch Doom.  See README.md for what each step does.

set -Eeuo pipefail

fail() {
    echo "make.sh: ERROR: $*" >&2
    exit 1
}

trap 'echo "make.sh: ERROR: command failed (exit $?) at line $LINENO: $BASH_COMMAND" >&2' ERR

step() {
    echo
    echo "==> $*"
}

# All steps run within this build directory.
cd "$(dirname "$(readlink -f "$0")")"

step "Checking for poetry"
if ! command -v poetry > /dev/null; then
    fail "poetry is not installed.  See https://python-poetry.org/ for how to install it, then re-run this script."
fi

step "Checking for doom1.wad"
if [ ! -f doom1.wad ]; then
    fail "doom1.wad not found in $(pwd)"
fi

# Shareware Doom v1.9, as listed at https://doomwiki.org/wiki/DOOM1.WAD
expected_sha1=5b2e249b9c5133ec987b3ea77596381dc0d6bc1d
actual_sha1=$(sha1sum doom1.wad | cut -d' ' -f1)
if [ "$actual_sha1" != "$expected_sha1" ]; then
    fail "doom1.wad has SHA-1 $actual_sha1, but expected $expected_sha1 (shareware Doom v1.9).  See https://doomwiki.org/wiki/DOOM1.WAD"
fi

step "Setting up Python environment"
poetry install

step "Creating build-output directories"
mkdir -p pytch-project/code
mkdir -p pytch-project/images

step "Copying image assets"
cp ../assets/spinner.png pytch-project/images
cp ../assets/gradient-bg.png pytch-project/images

step "Building frame"
poetry run python mk_doom_frame.py

step "Building texture posts"
poetry run python mk_texture_posts.py

step "Building title-screen slices"
poetry run python mk_title_posts.py

step "Building map and player-position marker"
poetry run python mk_simple_map.py
poetry run python mk_map_marker.py

step "Building flat Pytch program"
poetry run python mk_pytch_code.py

step "Done"
