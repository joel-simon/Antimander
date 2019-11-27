import random, math, json
import numpy as np
from collections import defaultdict

from src.utils import polygon as poly

def flatten(list_of_lists):
    return [val for sublist in list_of_lists for val in sublist]

class State:
    """ The sate is static and knows nothing about districts.
        It is a set of connected tiles.
    """
    def __init__(self, tile_populations, tile_vertices, tile_neighbours, tile_boundaries, tile_edges):
        assert tile_populations.shape[1] == 2 #Only support 2-parties for now.
        self.n_tiles = len(tile_populations)
        self.population = int(tile_populations.sum())
        self.tile_populations = tile_populations
        self.tile_populations_tot = tile_populations.sum(axis=1).astype('int32')
        self.tile_vertices = tile_vertices
        self.tile_neighbours = tile_neighbours
        self.tile_boundaries = tile_boundaries
        self.tile_edges = tile_edges
        self.tile_centers = np.array([ poly.centroid(v) for v in tile_vertices ], dtype='float32')
        self.boundry_tiles = np.where(tile_boundaries)[0].tolist()
        # print(self.boundry_tiles)
        # print(tile_boundaries)
        #
        # print(self.boundry_tiles)
        # self.boundry_tiles = [ i for i in range(self.n_tiles) if self.tile_boundaries[i] ]
        self.calculateNeighbourGraph()

    def calculateNeighbourGraph(self):
        self.neighbour_graph = []
        for i in range(self.n_tiles):
            ng = dict()
            neighours = self.tile_neighbours[i]
            for j in neighours:
                ng[j] = [k for k in self.tile_neighbours[j] if k in neighours]
            self.neighbour_graph.append(ng)

    @classmethod
    def makeRandom(cls, n_tiles=100, n_classes=2, seed=None):
        from src.utils.voronoi import smoothedRandomVoronoi
        cells = smoothedRandomVoronoi(n_tiles=n_tiles, steps=10, seed=seed)
        tile_vertices = [ c['vertices'] for c in cells ]
        tile_neighbours = [[ e['adjacent_cell'] for e in c['faces'] if e['adjacent_cell'] >= 0] for c in cells ]
        tile_boundaries = [ any( e['adjacent_cell'] < 0 for e in c['faces']) for c in cells ]
        tile_populations = np.random.randint(0, 10, size=(n_tiles, n_classes), dtype='int32')
        tile_edges = [ c['faces'] for c in cells ]

        return State(tile_populations, tile_vertices, tile_neighbours, tile_boundaries, tile_edges)

    @classmethod
    def fromFile(cls, filePath):
        with open(filePath, 'r') as file:
            state_data = json.load(file)
        tile_vertices = state_data['tract_vertices']
        tile_neighbours = state_data['tract_neighbours']
        tile_boundaries = state_data['boundry_tracts']
        tile_populations = np.random.randint(0, 10, size=(len(tile_vertices), 2), dtype='int32')
        return State(tile_populations, tile_vertices, tile_neighbours, tile_boundaries, None)

    def contract(self, seed=None):
        if seed is not None: np.random.seed(seed)
        """ Do a random coin flip for each vertex. """
        stars = np.random.randint(0, 2, size=self.n_tiles, dtype='uint8')
        """ Store the idx of the newly created vertex this one will join into. """
        to_join = np.zeros(self.n_tiles, dtype='int32')

        """ For each vertex pick its star if not one. """
        for i in range(self.n_tiles):
            if stars[i] == 1:
                to_join[i] = i
            else:
                options = [j for j in self.tile_neighbours[i] if stars[j]]
                if len(options) == 0:
                    stars[i] = 1
                    to_join[i] = i
                else:
                    to_join[i] = random.choice(options)

        stars2newidxs = defaultdict(lambda: len(stars2newidxs))
        for i, idx in enumerate(to_join):
            to_join[i] = stars2newidxs[idx]

        new_n_tiles = stars.sum()
        tile_populations = np.zeros((new_n_tiles, 2), dtype='i')
        tile_boundaries = np.zeros(new_n_tiles, dtype='i')
        tile_vertices = [ [] for _ in range(new_n_tiles) ]
        tile_neighbours = [ set() for _ in range(new_n_tiles) ]

        for i_from, i_to in enumerate(to_join):
            tile_populations[i_to] += self.tile_populations[i_from]
            if (self.tile_boundaries[i_from]):
                tile_boundaries[i_to] = True
            tile_vertices[i_to].append(self.tile_vertices[ i_from ])

            for j in self.tile_neighbours[i_from]:
                if to_join[j] != i_to:
                    tile_neighbours[i_to].add(int(to_join[j])) # cast to int to make it jsonable

        tile_neighbours = [list(tn) for tn in tile_neighbours]
        tile_vertices = [ poly.union(poly_list)[0] for poly_list in tile_vertices ]
        state = State(tile_populations, tile_vertices, tile_neighbours, tile_boundaries.tolist(), None)
        return state, to_join

    def toJSON(self):
        return {
            'tract_populations': self.tile_populations.tolist(),
            'tract_vertices': self.tile_vertices,
            'tract_neighbours': self.tile_neighbours,
            'boundry_tracts': self.tile_boundaries
            # 'tile_edges': self.tile_edges,
            # 'population': self.population
        }