import random, math
import randomcolor
rand_color = randomcolor.RandomColor()
import polygon
import itertools
from articulationPoints import articulationPoints

class Map:
    """ The map is static and knows nothing about partitions.
        It is a s set of connected tiles.
    """
    def __init__(self, tiles, n_classes):
        self.tiles = tiles
        self.n_classes = n_classes

    @classmethod
    def makeRandom(cls, n_tiles=100, n_classes=2, seed=None):
        from voronoi import smoothedRandomVoronoi
        random.seed(seed)
        cells = list(smoothedRandomVoronoi(n_tiles, 10))
        tiles = []

        """ Create a maptile for each cell.
        """
        for cell in cells:
            tiles.append(
                MapTile(
                    edges=[],
                    area=cell['volume'],
                    vertices=cell['vertices'],
                    populations=[ random.randint(0, 10) for _ in range(n_classes) ]
                )
            )

        """ Connect the edges.
        """
        for cell, tile in zip(cells, tiles):
            for edge in cell['faces']:
                neighbour = tiles[edge['adjacent_cell']] if edge['adjacent_cell'] >=0 else None
                tile_edge = MapTileEdge(1, neighbour, edge['vertices'])
                tile.edges.append(tile_edge)
                assert len(tile.vertices) > max(edge['vertices'])

        return Map(tiles, n_classes)

class MapTile:
    def __init__(self, vertices, area, edges, populations):
        self.vertices = vertices
        self.area = area
        self.edges = edges
        self.populations = populations
        self.center = polygon.centroid(vertices)

    def isBoundry(self):
        return any(e.neighbour is None for e in self.edges)

    def isNeighbour(self, other):
        return any(e.neighbour is other for e in self.edges)

    def neighbours(self, district=None):
        """ Utility function for accessing neighbour tiles. """
        for e in self.edges:
            n = e.neighbour
            if e.neighbour is None:
                continue
            if district and n not in district.tiles:
                continue
            yield e.neighbour

class MapTileEdge:
    def __init__(self, length, neighbour, vertices):
        self.length = length
        self.neighbour = neighbour
        self.vertices = vertices

class District:
    """ The district is a set of tiles that is a contiguos area of a map.
    """
    def __init__(self, tiles=[]):
        self.tiles = set()
        self.frontier = set()
        self.color = rand_color.generate(format_=('rgb', 'Array'))[0]

        for t in tiles:
            self.addTile(t)

    def addTile(self, tile):
        """ Incorporate a new tile and update the frontier
        """
        assert tile not in self.tiles
        self.tiles.add(tile)

        # New tiles must be on the frontier
        self.frontier.add(tile)

        # Check if any existing tiles are no longer on the district-fontier
        for edge in tile.edges:
            if edge.neighbour and edge.neighbour in self.frontier:
                if not self._isFrontier(edge.neighbour):
                    self.frontier.remove(edge.neighbour)

    def loseTile(self, tile):
        self.tiles.remove(tile)
        for e in tile.edges:
            if e.neighbour in self.tiles:
                self.frontier.add(e.neighbour)

    def _isFrontier(self, tile):
        neighbours = (e.neighbour for e in tile.edges if e.neighbour is not None)
        return any(n for n in neighbours if n not in self.tiles)

    # def _isLeaf(self, tile):
    #     return sum([ 1 for e in tile.edges if e.neighbour in self.tiles ]) == 1

    def canLose(self):
        ap = articulationPoints(self)
        return self.tiles - set(ap)

    # def removeTile(self, tile):
    # def _calculateFrontier(self):
    #     frontier = set()
    #     for tile in self.tiles:
    #         if any(e.neighbour not in self.tiles for e in tile.edges):
    #             frontier.add(tile)
    #     return frontier

    def compactness(self):
        area = 0
        perimeter = 0
        for tile in self.tiles:
            area += tile.area
            for edge in tile.edges:
                if edge.neighbour not in self.tiles:
                    perimeter += edge.length
        return 4 * math.pi * area / (perimeter**2)

    def lostVotes(self):
        return 1
        # self.winners = []


class Partition:
    """ Partition is a set of non-overlapping districts that cover a map.
    """
    def __init__(self, districts, map):
        self.districts = districts
        self.map = map
        self.tile2district = dict()

    def evaluate(self):
        compactness = max(d.compactness() for d in self.districts)
        lost_votes = max(d.lostVotes() for d in self.districts)
        return [ compactness, lost_votes ]

    def mutate(self):
        district = random.choice(self.districts)
        options = list(district.frontier.intersection(district.canLose()))
        if len(options) == 0:
            return
        to_lose = random.choice(options)
        give_to = [ self.tile2district[n] for n in to_lose.neighbours() if self.tile2district[n] != district ]
        if len(give_to):
            district.loseTile(to_lose)
            give_to = random.choice(give_to)
            give_to.addTile(to_lose)
            self.tile2district[to_lose] = give_to

    @classmethod
    def makeRandom(cls, n_districts, map, seed=None):
        random.seed(seed)
        frontier = [t for t in map.tiles if t.isBoundry()]
        seeds = random.sample(frontier, n_districts)
        districts = [ District( [ s ] ) for s in seeds ]
        assigned = set(seeds)

        p = Partition(districts, map)

        for dist, tile in zip(districts, seeds):
            p.tile2district[tile] = dist

        district_iter = itertools.cycle(districts)
        while len(assigned) < len(map.tiles):
            rand_dist = next(district_iter)
            rand_tile = random.sample(rand_dist.frontier, 1)[0]

            options = [ e.neighbour for e in rand_tile.edges if e.neighbour is not None ]
            options = [ t for t in options if t not in rand_dist.tiles and t not in assigned ]

            if len(options):
                tile = random.choice(options)
                rand_dist.addTile(tile)
                assigned.add(tile)
                p.tile2district[tile] = rand_dist

        return p


