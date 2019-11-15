import random, math
import numpy as np
from utils import polygon

class State:
    """ The sate is static and knows nothing about districts.
        It is a set of connected tiles.
    """
    def __init__(self, tile_populations, tile_vertices, tile_neighbours, tile_boundaries, tile_edges):
        assert tile_populations.shape[1] == 2 #Only support 2-parties for now.
        self.n_tiles = len(tile_populations)
        self.tile_populations = tile_populations
        self.tile_populations_tot = tile_populations.sum(axis=1).astype('int32')
        self.tile_vertices = tile_vertices
        self.tile_neighbours = tile_neighbours
        self.tile_boundaries = tile_boundaries
        self.tile_edges = tile_edges
        self.tile_centers = np.array([ polygon.centroid(v) for v in tile_vertices ], dtype='float32')
        self.boundry_tiles = [ i for i in range(self.n_tiles) if self.tile_boundaries[i] ]

        self.neighbour_graph = []
        for i in range(self.n_tiles):
            ng = dict()
            neighours = self.tile_neighbours[i]
            for j in neighours:
                ng[j] = [k for k in self.tile_neighbours[j] if k in neighours]
            self.neighbour_graph.append(ng)


    # def areTilesNeighbours(self, tile_idx_1, tile_idx_2):
    #     return any(x == tile_idx_2 for x in self.tile_neighbours[tile_idx_1])

    @classmethod
    def makeRandom(cls, n_tiles=100, n_classes=2, seed=None):
        from utils.voronoi import smoothedRandomVoronoi
        cells = smoothedRandomVoronoi(n_tiles=n_tiles, steps=10)
        tile_vertices = [ c['vertices'] for c in cells ]
        tile_neighbours = [[ e['adjacent_cell'] for e in c['faces'] if e['adjacent_cell'] >= 0] for c in cells ]
        tile_boundaries = [ any( e['adjacent_cell'] < 0 for e in c['faces']) for c in cells ]
        tile_populations = np.random.randint(0, 10, size=(n_tiles, n_classes), dtype='int32')
        tile_edges = [ c['faces'] for c in cells ]

        return State(tile_populations, tile_vertices, tile_neighbours, tile_boundaries, tile_edges)

    def toJSON(self):
        return {
            'tile_populations': self.tile_populations.tolist(),
            'tile_vertices': self.tile_vertices,
            'tile_neighbours': self.tile_neighbours,
            'tile_edges': self.tile_edges
        }