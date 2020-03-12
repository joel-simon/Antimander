import random, math, json
import numpy as np
from collections import defaultdict, Counter
from itertools import combinations
from src.utils import polygon
from src.test import merge_polygons

def flatten(a):
    return [ item for sublist in a for item in sublist ]

class State:
    """ The sate is static and knows nothing about districts.
        It is a set of connected tiles.
    """
    def __init__( self, tile_data ):
        self.n_tiles = len(tile_data['populations'])
        self.tile_populations = np.array(tile_data['populations'], dtype='i')
        self.tile_voters      = np.array(tile_data['voters'], dtype='i')
        self.tile_vertices    = [ polygon.pround(p) for p in tile_data['shapes'] ]
        self.tile_neighbors   = tile_data['neighbors']
        self.tile_boundaries  = np.array(tile_data['boundaries'], dtype='i')
        self.population       = tile_data['population']
        self.bbox             = tile_data['bbox']
        assert all(len(p) > 0 for p in self.tile_vertices)
        assert all(len(n) > 0 for n in self.tile_neighbors)
        self.calculateStats()

    def calculateStats(self):
        self._calculateStatsTileProperties()
        self._calculateStatsTileEdges()
        self._calculateNeighborGraph()
        self.area = sum(self.tile_areas)
        assert type(self.population) == int
        assert (self.tile_voters.shape == (self.n_tiles, 2)), self.tile_voters.shape #Only support 2-parties for now.
        assert self.tile_populations.shape == (self.n_tiles,)
        assert self.tile_boundaries.shape  == (self.n_tiles,), self.tile_boundaries.shape
        assert self.tile_centers.shape     == (self.n_tiles, 2)
        assert len(self.tile_vertices) == self.n_tiles
        assert len(self.tile_neighbors) == self.n_tiles

    def _calculateStatsTileProperties(self):
        self.tile_centers = np.array(
            [ polygon.centroid(v) for v in self.tile_vertices ], dtype='f'
        )
        self.tile_areas = np.array(
            [ polygon.area(v) for v in self.tile_vertices ], dtype='f'
        )
        self.tile_hulls = [ polygon.convex_hull(flatten(v)) for v in self.tile_vertices ]

    def _calculateStatsTileEdges(self):
        """ The districts come in as a
        """
        self.tile_edges = [ #[ {tj => [length, edge_list] } } ]
            defaultdict(lambda: { 'length': 0, 'edges':[  ] })
            for _ in range(self.n_tiles)
        ]

        v2ti = defaultdict(set) # Vert to its tile indexes.
        v2poly = Counter()
        for ti, polygons in enumerate(self.tile_vertices):
            for poly in polygons:
                for vert in poly:
                    v2ti[ vert ].add(ti)
                    v2poly[ vert ] += 1

        for ti, polygons in enumerate(self.tile_vertices):
            for poly in polygons:
                for vi, vert_a in enumerate(poly):
                    vert_b = poly[ (vi+1) % len(poly) ]
                    edge = (vert_a, vert_b)
                    length = math.hypot(vert_a[0] - vert_b[0], vert_a[1] - vert_b[1])
                    other_tiles = v2ti[ vert_a ].intersection(v2ti[vert_b])
                    boundry_edge = len(other_tiles) == 1
                    if boundry_edge:
                        # if len(other_tiles) == 1 and :# Is a boundry tile
                        self.tile_edges[ ti ][ 'boundry' ][ 'length' ] += length
                        self.tile_edges[ ti ][ 'boundry' ][ 'edges' ].append(( vert_a, vert_b ))
                    else:
                        for ti_other in other_tiles:
                            if ti_other != ti:
                                self.tile_edges[ ti ][ ti_other ][ 'length' ] += length
                                self.tile_edges[ ti ][ ti_other ][ 'edges' ].append(( vert_a, vert_b ))

        # Convert to regular dicts so that it can be JSON'd.
        self.tile_edges = [ dict(x) for x in self.tile_edges ]

    def _calculateNeighborGraph(self):
        self.neighbor_graph = []
        for i in range(self.n_tiles):
            ng = dict()
            neighors = self.tile_neighbors[i]
            for j in neighors:
                ng[j] = [k for k in self.tile_neighbors[j] if k in neighors]
            self.neighbor_graph.append(ng)

    def _tileDist(self, i, j):
        x1, y1 = self.tile_centers[i]
        x2, y2 = self.tile_centers[j]
        return math.hypot(x1-x2, y1-y2)

    def contract(self, seed=None):
        """ Do Star contraction to contract the graph.
            http://www.cs.cmu.edu/afs/cs/academic/class/15210-f12/www/lectures/lecture16.pdf
        """
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        # Do a random coin flip for each tile.
        stars = np.random.randint(0, 2, size=self.n_tiles, dtype='uint8')
        # Store the idx of tile this one will join into.
        to_join = np.arange(self.n_tiles, dtype='int32')
        # Turn into sets for fast intersection tests.
        verts = [ set(flatten(polygons)) for polygons in self.tile_vertices ]
        # For each non-star tile pick a star neighbor to join onto.
        for ti in range(self.n_tiles):
            if not stars[ti]:
                options = [ j for j in self.tile_neighbors[ti] if stars[j] and len(verts[ti] & verts[j]) > 1 ]
                options = [ (self._tileDist(ti, j), j) for j in options ]
                options.sort()
                if len(options):
                    # to_join[ti] = random.choice(options)[1]
                    to_join[ti] = options[0][1]

        # Prevent created islands. If an interior tiles neighbors are all
        # combining, join into that one as well.
        for ti in range(self.n_tiles):
            ji = to_join[ti]
            jn = to_join[self.tile_neighbors[ti][0]]
            if self.tile_boundaries[ti]:
                continue
            if ji != jn and all(to_join[tn] == jn for tn in self.tile_neighbors[ti]):
                to_join[ti] = jn
        # Mapping go between indexes of old state to new state.
        state, mapping1 = self._mergeTiles(to_join)
        return state, mapping1
        # state, mapping2 = state.mergeIslands()
        # We now how to merge the mappings!
        # final_mapping = np.array([ mapping2[mapping1[ti]] for ti in range(self.n_tiles) ], dtype='i')
        # return state, final_mapping

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
            for j in self.tile_neighbors[ i_from ]:
                if mapping[ j ] != i_to:
                    tile_neighbors[ i_to ].add(int(mapping[j])) # cast to int to make it jsonable

        # Create new polygon objects out of polygon groups.
        tile_vertices = [  ]
        for idx, pg in enumerate(polygon_groups):
            # polygon = merge_polygons(pg)
            polygon = flatten(pg)
            # if len(polygon) < 3:
            #     print(polygon)
            #     print([len(p) for p in pg ])
            #     print( np.argwhere(mapping == idx) )
            #     for a, b in combinations(pg,2):
            #         print(len(set(a)&set(b)))
            # assert len(polygon) > 2
            tile_vertices.append(polygon)

        # verts = [ set(v) for v in tile_vertices ]
        # for (i, a), (j, b) in combinations(enumerate(verts), 2):
        #     if len(a) == len(b) and a & b == a:
        #         print('DUPLICATE TILES FOUND', i, j)
        #         print(np.argwhere(mapping == i).T[0])
        #         print(np.argwhere(mapping == j).T[0])
        #         # exit()

        tile_neighbors = [ list(tn) for tn in tile_neighbors ]
        state = State({
            'bbox': self.bbox,
            'voters': tile_voters,
            'shapes':    tile_vertices,
            'boundaries':  tile_boundaries,
            'neighbors' :  tile_neighbors,
            'population':  self.population,
            'populations': tile_populations
        })
        return state, mapping

    @classmethod
    def makeRandom(
        cls, n_tiles=100, n_parties=2, seed=None, n_cities=3,
        total_pop=1e6,
        city_strength=.1, # How big are cities in terms of percent of total pop.
        voter_turnout=0.7, # Arbitrary.
        smooth_steps=6
    ):
        from src.utils.voronoi import smoothedRandomVoronoi
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        cells = smoothedRandomVoronoi(n_tiles=n_tiles, steps=5, seed=seed)
        boundry_tiles = [ any( e['adjacent_cell'] < 0 for e in c['faces']) for c in cells ]
        tile_boundaries = np.zeros(n_tiles, dtype='uint8')
        tile_boundaries[ boundry_tiles ] = 1
        tile_neighbors = [[ e['adjacent_cell'] for e in c['faces']
                            if e['adjacent_cell'] >= 0] for c in cells ]
 
        noise = np.random.uniform(low=0.2, high=0.8, size=(n_tiles,))
        tile_voters = np.array([ noise, 1-noise ]).T

        # Assumes cities skew to one party.
        for ti in random.sample(list(range(n_tiles)), n_cities):
            tile_voters[ti, 0] = n_tiles * city_strength / n_cities

        # Smooth.
        for _ in range(smooth_steps):
            _tile_voters = np.zeros_like(tile_voters)
            for ti in range(n_tiles):
                nn = len(tile_neighbors[ti])
                _tile_voters[ti, 0] = sum(tile_voters[ti_o, 0] for ti_o in tile_neighbors[ti]) / nn
                _tile_voters[ti, 1] = sum(tile_voters[ti_o, 1] for ti_o in tile_neighbors[ti]) / nn
            tile_voters = 0.5 * (_tile_voters + tile_voters)
        
        # Ensure same number of each party.
        tile_voters[:, 0] *= 1 / tile_voters[:, 0].sum()
        tile_voters[:, 1] *= 1 / tile_voters[:, 1].sum()

        tile_populations = tile_voters.sum(axis=1) / voter_turnout
        scale = total_pop / tile_populations.sum()
        tile_populations = (scale * tile_populations).astype('i')
        tile_voters = (scale * tile_voters).astype('i')
        
        for ti in range(n_tiles):
            assert tile_voters[ti].sum() < tile_populations[ti]

        print('p1', tile_voters[:, 0].sum())
        print('p2', tile_voters[:, 1].sum())
        print('total_voters', tile_voters.sum())
        print('total_pop', tile_populations.sum())

        tile_data = {
            'shapes': [ [[ (int(x*1000), int(y*1000)) for x,y in c['vertices']]] for c in cells ],
            'neighbors': tile_neighbors,
            'boundaries': tile_boundaries,
            'populations': tile_populations,
            'voters': tile_voters,
            'bbox': [0, 0, 1000, 1000],
            'population': int(tile_populations.sum())
        }
        state = State(tile_data)
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
            'shapes': self.tile_vertices,
            'neighbors': self.tile_neighbors,
            'boundaries': self.tile_boundaries.tolist(),
            'bbox': self.bbox,
            'tile_edges': self.tile_edges
        }