#!/bin/bash

poetry run python drawmaps.py doom1.wad E1M3 4000 png
convert E1M3_map.png \
        -filter Box \
        -resize 944x944 \
        -bordercolor '#eee' -border 8 \
        blog-figures/e1m3-original.png
rm E1M3_map.png

poetry run python mk_simple_map.py m1.png solid
convert m1.png \
        -filter Box \
        -resize 944x944 \
        -bordercolor '#eee' -border 8 \
        blog-figures/e1m3-one-sided-only.png
rm m1.png

poetry run python mk_allowzone_figure.py
convert blog-figures/allowzone-detail-0.png \
        -background '#eee' -flatten \
        -filter Box \
        -resize 960x960 \
        blog-figures/allowzone-detail.png
rm blog-figures/allowzone-detail-0.png
