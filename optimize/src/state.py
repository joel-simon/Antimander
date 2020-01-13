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
        # self.tile_vertices = [[tuple(v) for v in p] for p in tile_data['vertices']]
        self.tile_vertices = [[(round(x), round(y)) for x,y in p] for p in tile_data['vertices']]
        self.tile_neighbors   = tile_data['neighbors']
        self.tile_boundaries  = np.array(tile_data['boundaries'], dtype='i')
        self.population       = tile_data['population']
        self.bbox             = tile_data['bbox']
        self.area = sum(polygon.area(v) for v in self.tile_vertices)

        self.fixSingleNeighbors()
        self.fitlerSingleConnections()
        self.calculateNeighborGraph()

        self.tile_centers = np.array(
            [ polygon.centroid(v) for v in self.tile_vertices ], dtype='float32'
        )

        assert type(self.population) == int
        assert self.tile_voters.shape == (self.n_tiles, 2) #Only support 2-parties for now.
        assert self.tile_populations.shape == (self.n_tiles,)
        assert self.tile_boundaries.shape  == (self.n_tiles,), self.tile_boundaries.shape
        assert self.tile_centers.shape     == (self.n_tiles, 2)
        assert len(self.tile_vertices) == self.n_tiles
        assert len(self.tile_neighbors) == self.n_tiles
        assert all(len(n) > 0 for n in self.tile_neighbors)

    def fixSingleNeighbors(self):
        # Check for tiles totally surrounded by others (donut holes).
        to_remove = []
        to_join = []
        for ti in range(self.n_tiles):
            if len(self.tile_neighbors[ti]) == 1:
                to_remove.append(ti)
                to_join.append(list(self.tile_neighbors[ti])[0])
        self.mergeTiles(to_remove, to_join)

    def fitlerSingleConnections(self):
        to_remove = []
        to_join = []
        verts = [ set(v) for v in self.tile_vertices ]
        for ti1 in range(self.n_tiles):
            new_neighbors = [ ti2 for ti2 in self.tile_neighbors[ti1]
                            if len(verts[ti1] & verts[ti2]) > 1 ]
            if len(new_neighbors) == 0:
                to_remove.append(ti1)
                to_join.append(list(self.tile_neighbors[ti1])[0])
            self.tile_neighbors[ti1] = new_neighbors
        self.mergeTiles(to_remove, to_join)

    def mergeTiles(self, to_remove, to_join):
        # Helper function used while fixing state holes and single vert neighbors.
        if len(to_remove) == 0:
            return
        print('to_remove, to_join', to_remove, to_join)
        tile_mapping = np.zeros(self.n_tiles, dtype='i')
        idx = 0
        for ti in range(self.n_tiles):
            tile_mapping[ti] = ti - idx
            if ti in to_remove:
                idx += 1
        for src, dst in zip(to_remove, to_join):
            self.tile_voters[dst] += self.tile_voters[src]
            self.tile_populations[dst] += self.tile_populations[src]
            self.tile_vertices[dst] = merge_polygons([self.tile_vertices[dst], self.tile_vertices[src]])
        self.n_tiles -= len(to_remove)
        self.tile_voters      = np.delete(self.tile_voters, to_remove, axis=0)
        self.tile_populations = np.delete(self.tile_populations, to_remove, axis=0)
        self.tile_boundaries  = np.delete(self.tile_boundaries, to_remove, axis=0)
        self.tile_vertices    = [ v for i,v in enumerate(self.tile_vertices) if i not in to_remove ]
        self.tile_neighbors   = [
            [ tile_mapping[t] for t in tn if t not in to_remove ]
            for i, tn in enumerate(self.tile_neighbors)
            if i not in to_remove
        ]

    def calculateNeighborGraph(self):
        self.neighbor_graph = []
        for i in range(self.n_tiles):
            ng = dict()
            neighors = self.tile_neighbors[i]
            for j in neighors:
                ng[j] = [k for k in self.tile_neighbors[j] if k in neighors]
            self.neighbor_graph.append(ng)

    def calculateTileEdges(self):
        """ The districts come in as a
        """
        self.tile_edges = [ #[ {tj => [length, edge_list] } } ]
            defaultdict(lambda: {'length': 0, 'edges':[]})
            for _ in range(self.n_tiles)
        ]
        # Vert to its tile indexes.
        v2pi = defaultdict(set)
        for pi, poly in enumerate(self.tile_vertices):
            for vert in poly:
                v2pi[ vert ].add(pi)
        for ti, poly in enumerate(self.tile_vertices):
            for vi, vert_a in enumerate(poly):
                vert_b = poly[ (vi+1) % len(poly) ]
                for ti_other in v2pi[vert_a].intersection(v2pi[vert_b]):
                    if ti_other != ti:
                        length = math.hypot(vert_a[0] - vert_b[0], vert_a[1] - vert_b[1])
                        self.tile_edges[ ti ][ ti_other ][ 'length' ] += length
                        self.tile_edges[ ti ][ ti_other ][ 'edges' ].append(( vert_a, vert_b ))

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
        # Starred tiles will become the new tiles and others will merge into them.
        stars2newidxs = defaultdict(lambda: len(stars2newidxs))
        for i, idx in enumerate(to_join):
            to_join[i] = stars2newidxs[idx]
        new_n_tiles = stars.sum()
        # Create the data structures for new state.
        tile_voters = np.zeros((new_n_tiles, 2), dtype='i')
        tile_populations = np.zeros(new_n_tiles, dtype='i')
        tile_boundaries  = np.zeros(new_n_tiles, dtype='i')
        polygon_groups   = [ [] for _ in range(new_n_tiles) ]
        tile_neighbors   = [ set() for _ in range(new_n_tiles) ]
        # Merge old states into new states.
        for i_from, i_to in enumerate(to_join):
            tile_populations[i_to] += self.tile_populations[i_from]
            tile_voters[i_to] += self.tile_voters[i_from]
            if (self.tile_boundaries[i_from]):
                tile_boundaries[i_to] = True
            polygon_groups[i_to].append(self.tile_vertices[ i_from ])
            for j in self.tile_neighbors[i_from]:
                if to_join[j] != i_to:
                    tile_neighbors[i_to].add(int(to_join[j])) # cast to int to make it jsonable

        tile_vertices = [ merge_polygons(pg) for pg in polygon_groups ]

        state = State({
            'bbox': self.bbox,
            'voters': tile_voters,
            'vertices':    tile_vertices,
            'boundaries':  tile_boundaries,
            'neighbors' :  tile_neighbors,
            'population':  self.population,
            'populations': tile_populations
        })
        return state, to_join

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
        # print([ c['vertices'] for c in cells ])
        tile_data = {
            'vertices': [ [ (int(x*1000),int(y*1000)) for x,y in c['vertices']] for c in cells ],
            'neighbors': [[ e['adjacent_cell'] for e in c['faces'] if e['adjacent_cell'] >= 0] for c in cells ],
            'boundaries': tile_boundaries,
            'populations': tile_populations,
            'voters': tile_voters,
            # 'edges': [ c['faces'] for c in cells ],
            'bbox': [0, 0, 1000, 1000],
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