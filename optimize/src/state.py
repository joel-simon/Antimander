import random, math, json
import numpy as np
from collections import defaultdict, namedtuple
from src.utils import polygon
from src.test import merge_polygons

class State:
    """ The sate is static and knows nothing about districts.
        It is a set of connected tiles.
    """
    def __init__( self, tile_data ):
        self.n_tiles = len(tile_data['populations'])
        self.tile_populations = np.array(tile_data['populations'], dtype='i')
        self.tile_voters      = np.array(tile_data['voters'], dtype='i')
        self.tile_vertices    = [[(round(x), round(y)) for x,y in p]
                                  for p in tile_data['vertices']]
        self.tile_neighbors   = tile_data['neighbors']
        self.tile_boundaries  = np.array(tile_data['boundaries'], dtype='i')
        self.population       = tile_data['population']
        self.bbox             = tile_data['bbox']
        assert all(len(v) > 2 for v in self.tile_vertices)
        assert all(len(n) > 0 for n in self.tile_neighbors)
        self.calculateStats()

    def calculateStats(self):
        self.area = sum(polygon.area(v) for v in self.tile_vertices)
        self.tile_centers = np.array(
            [ polygon.centroid(v) for v in self.tile_vertices ], dtype='float32'
        )
        self.tile_bboxs = np.array(
            [ polygon.bounding_box(v) for v in self.tile_vertices ], dtype='float32'
        )
        self.calculateNeighborGraph()
        assert type(self.population) == int
        assert self.tile_voters.shape == (self.n_tiles, 2) #Only support 2-parties for now.
        assert self.tile_populations.shape == (self.n_tiles,)
        assert self.tile_boundaries.shape  == (self.n_tiles,), self.tile_boundaries.shape
        assert self.tile_centers.shape     == (self.n_tiles, 2)
        assert len(self.tile_vertices) == self.n_tiles
        assert len(self.tile_neighbors) == self.n_tiles

    def calculateNeighborGraph(self):
        self.neighbor_graph = []
        for i in range(self.n_tiles):
            ng = dict()
            neighors = self.tile_neighbors[i]
            for j in neighors:
                ng[j] = [k for k in self.tile_neighbors[j] if k in neighors]
            self.neighbor_graph.append(ng)

    def contract(self, seed=None):
        """ Do Star contraction to contract the graph.
            http://www.cs.cmu.edu/afs/cs/academic/class/15210-f12/www/lectures/lecture16.pdf
        """
        if seed is not None: np.random.seed(seed)
        # Do a random coin flip for each tile.
        stars = np.random.randint(0, 2, size=self.n_tiles, dtype='uint8')
        # Store the idx of tile this one will join into.
        to_join = np.arange(self.n_tiles, dtype='int32')
        # Turn into sets for fast intersection tests.
        verts = [ set(v) for v in self.tile_vertices ]
        # For each non-star tile pick a star neighbor to join onto.
        for i in range(self.n_tiles):
            if not stars[i]:
                #options = [ j for j in self.tile_neighbors[i] if stars[j] ]
                options = [ j for j in self.tile_neighbors[i] if stars[j] and len(verts[i] & verts[j]) > 1 ]
                if len(options):
                    to_join[i] = random.choice(options)

        # Mapping go between indexes of old state to new state.
        state, mapping1 = self._mergeTiles(to_join)
        state, mapping2 = state.mergeIslands()
        # We now how to merge the mappings!
        final_mapping = np.array([ mapping2[mapping1[ti]] for ti in range(self.n_tiles) ], dtype='i')
        return state, final_mapping

    def mergeIslands(self):
        # Check for tiles totally surrounded by others.
        to_join = np.arange(self.n_tiles, dtype='int32')
        for ti in range(self.n_tiles):
            if len(self.tile_neighbors[ti]) == 1:
                to_join[ti] = self.tile_neighbors[ti][0]
        state, mapping = self._mergeTiles(to_join)
        assert all(len(n) > 1 for n in state.tile_neighbors)
        return state, mapping

    def _mergeTiles(self, to_join):
        # Starred tiles will become the new tiles and others will merge into them.
        old_2_new_idxs = defaultdict(lambda: len(old_2_new_idxs))
        mapping = to_join.copy()
        for i, idx in enumerate(to_join):
            mapping[i] = old_2_new_idxs[idx]
        new_n_tiles = len(set(mapping))
        # Create the data structures for new state.
        tile_voters      = np.zeros((new_n_tiles, 2), dtype='i')
        tile_populations = np.zeros(new_n_tiles, dtype='i')
        tile_boundaries  = np.zeros(new_n_tiles, dtype='i')
        polygon_groups   = [ [] for _ in range(new_n_tiles) ]
        tile_neighbors   = [ set() for _ in range(new_n_tiles) ]
        # Merge old states into new states.
        for i_from, i_to in enumerate(mapping):
            tile_populations[i_to] += self.tile_populations[i_from]
            tile_voters[i_to] += self.tile_voters[i_from]
            if (self.tile_boundaries[i_from]):
                tile_boundaries[i_to] = True
            polygon_groups[i_to].append(self.tile_vertices[ i_from ])
            for j in self.tile_neighbors[i_from]:
                if mapping[j] != i_to:
                    tile_neighbors[i_to].add(int(mapping[j])) # cast to int to make it jsonable
        # Create new polygon objects out of polygon groups.
        tile_vertices = [  ]
        for pg in polygon_groups:
            new_vertices = merge_polygons(pg)
            assert len(new_vertices) > 2, (pg, new_vertices)
            tile_vertices.append(new_vertices)
        tile_neighbors = [ list(tn) for tn in tile_neighbors ]
        state = State({
            'bbox': self.bbox,
            'voters': tile_voters,
            'vertices':    tile_vertices,
            'boundaries':  tile_boundaries,
            'neighbors' :  tile_neighbors,
            'population':  self.population,
            'populations': tile_populations
        })
        return state, mapping

    @classmethod
    def makeRandom(cls, n_tiles=100, n_parties=2, seed=None):
        from src.utils.voronoi import smoothedRandomVoronoi
        if seed is not None:
            np.random.seed(seed)
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
            'vertices': [ [ (int(x*1000),int(y*1000)) for x,y in c['vertices']] for c in cells ],
            'neighbors': [[ e['adjacent_cell'] for e in c['faces'] if e['adjacent_cell'] >= 0] for c in cells ],
            'boundaries': tile_boundaries,
            'populations': tile_populations,
            'voters': tile_voters,
            'bbox': [0, 0, 1000, 1000],
            'population': int(tile_populations.sum())
        }
        state = State(tile_data)
        # state.mergeIslands(None)
        # state.fitlerSingleConnections(None)
        return state

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