# Steps to build Pytch Doom

All of the instructions here are to be followed within this `build`
directory.  The bash script `make.sh` performs the following steps.
This file gives more details on what that script does.


## Required tools

We use poetry for dependency management.  See [its web
page](https://python-poetry.org/) for instructions on how to install
it, if you don't already have poetry on your system.


## Get a copy of the `DOOM1.WAD` file

This is part of the freely-available shareware release, but it's not
clear that redistributing just the WAD file is permitted.  You can go
to [DOOM1.WAD page on DoomWiki](https://doomwiki.org/wiki/DOOM1.WAD)
to find a link to the required file.  Save the file into this
directory with (lower-case) filename `doom1.wad`.

### Verify the file

Run

``` shell
sha1sum doom1.wad
```

and verify that the checksum is
`5b2e249b9c5133ec987b3ea77596381dc0d6bc1d`.


## Set up Python environment

Install a Python virtual environment with

``` shell
poetry install
```


## Create build-output directory

``` shell
mkdir -p pytch-project/code
mkdir -p pytch-project/images
```


## Copy image assets

``` shell
cp ../assets/spinner.png pytch-project/images
cp ../assets/gradient-bg.png pytch-project/images
```


## Build image files

The project needs some individual images and sets of images.  Create
them as follows.

### Frame

The mottled border which, in the original Doom, could allow the game
to run on less-powerful hardware by rendering a smaller viewport.
Here, we use it so that the Pytch port can render a 320×240 region in
the centre of the 480×360 stage.

``` shell
poetry run python mk_doom_frame.py
```

### One-pixel-wide "posts" of all used textures

The rendering is done by having 320 clones, each positioned centrally
in the 320 pixel-wide strips of the centre portion of the stage.
Every frame, each clone then dons a costume for the slice of texture
which should appear at that *x*-coordinate, and scales itself
according to the distance from the player.  This results in quite a
lot of costume files.

``` shell
poetry run python mk_texture_posts.py
```

### Slices of the title screen

Used for the "dripping" effect.

``` shell
poetry run python mk_title_posts.py
```

### Map and player-position marker

Used for the map overlay.

``` shell
poetry run python mk_simple_map.py
poetry run python mk_map_marker.py
```


## Build "flat" Pytch program

Running

``` shell
poetry run python mk_pytch_code.py
```

will write the combined Pytch program into the file
`pytch-project/code/pytch-doom.py`.


## Create Pytch project

In my testing, Chrome cannot handle the large number of images the
project uses.  Firefox 158 runs the project successfully (on Linux,
anyway).

Go to [the Pytch website](https://pytch.org/), click "My projects",
then "Create".  create a new "Edit as one big program" project,
without example code.  Then:

* Remove the `python-logo.png` image from your project.

* Add the many image files from the `pytch-project/images/` directory
  here.  Select them all (3091 of them) in one go.  It will take a
  while (around a minute on my machine) for Pytch to add them to your
  project.

* Copy and paste the contents of `pytch-project/code/pytch-doom.py`
  into the code editor pane.  (`xclip` is useful for this.)


## Run the game!

Click Pytch's green play button and explore!  Controls are:

* Arrow keys: move forward or backward or turn.

* `C` and `V`: step sideways left and right (without turning).

* `M`: toggle map.
