import random, math
import numpy as np

from utils import polygon


class Map:
    """ The map is static and knows nothing about partitions.
        It is a s set of connected tiles.
    """
    def __init__(self, tile_populations, tile_vertices, tile_neighbours, tile_boundaries):
        self.n_tiles = len(tile_populations)
        self.tile_populations = tile_populations
        self.tile_vertices = tile_vertices
        self.tile_neighbours = tile_neighbours
        self.tile_boundaries = tile_boundaries
        self.tile_centers = [ polygon.centroid(v) for v in tile_vertices ]
        self.boundry_tiles = [ i for i in range(self.n_tiles) if self.tile_boundaries[i] ]

    def areTilesNeighbours(self, tile_idx_1, tile_idx_2):
        return any(x == tile_idx_2 for x in self.tile_neighbours[tile_idx_1])

    @classmethod
    def makeRandom(cls, n_tiles=100, n_classes=2, seed=None):
        from utils.voronoi import smoothedRandomVoronoi
        cells = smoothedRandomVoronoi(n_tiles=n_tiles, steps=10)

        tile_vertices = [ c['vertices'] for c in cells ]
        tile_neighbours = [[ e['adjacent_cell'] for e in c['faces'] if e['adjacent_cell'] >= 0] for c in cells ]
        tile_boundaries = [ any( e['adjacent_cell'] < 0 for e in c['faces']) for c in cells ]
        # tile_populations = np.random.randint(0, 10, size=(n_tiles, n_classes))
        tile_populations = np.ones((n_tiles, n_classes))

        return Map(tile_populations, tile_vertices, tile_neighbours, tile_boundaries)

    def toJSON(self):
        return {
            'tile_populations': self.tile_populations.tolist(),
            'tile_vertices': self.tile_vertices
        }