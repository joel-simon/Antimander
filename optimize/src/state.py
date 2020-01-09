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
    def __init__( self, tile_data ):
        self.n_tiles = len(tile_data['populations'])
        self.tile_populations = np.array(tile_data['populations'], dtype='i')
        self.tile_voters      = np.array(tile_data['voters'], dtype='i')
        self.tile_vertices    = tile_data['vertices']
        self.tile_neighbors   = tile_data['neighbors']
        self.tile_boundaries  = np.array(tile_data['boundaries'], dtype='i')
        self.population       = tile_data['population']
        self.bbox             = tile_data['bbox']
        self.tile_centers = np.array([ poly.centroid(v) for v in self.tile_vertices ], dtype='float32')

        assert type(self.population) == int
        assert self.tile_voters.shape == (self.n_tiles, 2) #Only support 2-parties for now.
        assert self.tile_populations.shape == (self.n_tiles,)
        assert self.tile_boundaries.shape  == (self.n_tiles,), self.tile_boundaries.shape
        assert self.tile_centers.shape     == (self.n_tiles, 2)
        assert len(self.tile_vertices) == self.n_tiles
        assert len(self.tile_neighbors) == self.n_tiles
        assert all(len(n) > 0 for n in self.tile_neighbors)

        self.calculateneighborGraph()

    def calculateneighborGraph(self):
        self.neighbor_graph = []
        for i in range(self.n_tiles):
            ng = dict()
            neighours = self.tile_neighbors[i]
            for j in neighours:
                ng[j] = [k for k in self.tile_neighbors[j] if k in neighours]
            self.neighbor_graph.append(ng)

    def contract(self, seed=None):
        """ Do Star contraction to cotnract the graph.
            http://www.cs.cmu.edu/afs/cs/academic/class/15210-f12/www/lectures/lecture16.pdf
        """
        if seed is not None: np.random.seed(seed)
        # Do a random coin flip for each vertex.
        stars = np.random.randint(0, 2, size=self.n_tiles, dtype='uint8')
        # Store the idx of the newly created vertex this one will join into.
        to_join = np.zeros(self.n_tiles, dtype='int32')
        # For each non-star vertex pick a star neighbor.
        for i in range(self.n_tiles):
            if stars[i] == 1:
                to_join[i] = i
            else:
                options = [ j for j in self.tile_neighbors[i] if stars[j] ]
                if len(options) == 0:
                    stars[i] = 1
                    to_join[i] = i
                else:
                    to_join[i] = random.choice(options)

        stars2newidxs = defaultdict(lambda: len(stars2newidxs))
        for i, idx in enumerate(to_join):
            to_join[i] = stars2newidxs[idx]

        new_n_tiles = stars.sum()

        tile_voters = np.zeros((new_n_tiles, 2), dtype='i')
        tile_populations = np.zeros(new_n_tiles, dtype='i')
        tile_boundaries  = np.zeros(new_n_tiles, dtype='i')
        tile_vertices    = [ [] for _ in range(new_n_tiles) ]
        tile_neighbors   = [ set() for _ in range(new_n_tiles) ]

        for i_from, i_to in enumerate(to_join):
            tile_populations[i_to] += self.tile_populations[i_from]
            tile_voters[i_to] += self.tile_voters[i_from]
            if (self.tile_boundaries[i_from]):
                tile_boundaries[i_to] = True
            tile_vertices[i_to].append(self.tile_vertices[ i_from ])

            for j in self.tile_neighbors[i_from]:
                if to_join[j] != i_to:
                    tile_neighbors[i_to].add(int(to_join[j])) # cast to int to make it jsonable
        state = State({
            'voters': tile_voters,
            'populations': tile_populations,
            'boundaries': tile_boundaries,
            'vertices': [ poly.test(poly_list)[0] for poly_list in tile_vertices ],
            'neighbors' : [ list(tn) for tn in tile_neighbors ],
            # 'edges': None, #TODO
            'population': self.population,
            'bbox': self.bbox
        })
        return state, to_join

    @classmethod
    def makeRandom(cls, n_tiles=100, n_parties=2, seed=None):
        from src.utils.voronoi import smoothedRandomVoronoi
        cells = smoothedRandomVoronoi(n_tiles=n_tiles, steps=10, seed=seed)
        boundry_tiles = [ any( e['adjacent_cell'] < 0 for e in c['faces']) for c in cells ]
        tile_boundaries = np.zeros(n_tiles, dtype='uint8')
        tile_boundaries[ boundry_tiles ] = 1
        tile_populations = np.random.randint(0, 1000, size=n_tiles, dtype='int32')
        tile_voters = np.array([
            (0.7 * 0.5 * np.random.rand(n_tiles) * tile_populations),
            (0.7 * 0.5 * np.random.rand(n_tiles) * tile_populations)
        ]).astype('int32').T
        tile_data = {
            'vertices': [ c['vertices'] for c in cells ],
            'neighbors': [[ e['adjacent_cell'] for e in c['faces'] if e['adjacent_cell'] >= 0] for c in cells ],
            'boundaries': tile_boundaries,
            'populations': tile_populations,
            'voters': tile_voters,
            # 'edges': [ c['faces'] for c in cells ],
            'bbox': [0, 0, 1, 1],
            'population': int(tile_populations.sum())
        }
        return State(tile_data)

    @classmethod
    def fromFile(cls, filePath):
        with open(filePath, 'r') as file:
            state_data = json.load(file)
        return State(state_data)

    def toJSON(self):
        return {
            'n_tiles': self.n_tiles,
            'population': self.population,
            'populations': self.tile_populations.tolist(),
            'voters': self.tile_voters.tolist(),
            'vertices': self.tile_vertices,
            'neighbors': self.tile_neighbors,
            'boundaries': self.tile_boundaries.tolist(),
            'bbox': self.bbox
        }