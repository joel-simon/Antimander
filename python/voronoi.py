from random import random
import polygon
import pyvoro

def smoothedRandomVoronoi(n_tiles, steps):
    seeds = [[random(), random()] for _ in range(n_tiles)]
    for _ in range(steps+1):
        cells = pyvoro.compute_2d_voronoi(
            seeds,
            [[0.0, 1.0], [0.0, 1.0]],
            2.0,
            radii=[1.0, 0.0]
        )
        seeds = [ polygon.centroid(c['vertices']) for c in cells ]

    return cells
