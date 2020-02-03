import random
import pyvoro
from src.utils import polygon

def smoothedRandomVoronoi(n_tiles, steps, seed=None):
    if seed is not None: random.seed(seed)
    seeds = [[random.random(), random.random()] for _ in range(n_tiles)]
    for _ in range(steps+1):
        cells = pyvoro.compute_2d_voronoi(
            seeds,
            [[0.0, 1.0], [0.0, 1.0]],
            2.0,
            radii=[1.0, 0.0]
        )
        seeds = [ polygon.centroid([c['vertices']]) for c in cells ]

    return cells
