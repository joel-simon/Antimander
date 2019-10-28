import random, math
import numpy as np
from copy import deepcopy
from utils.articulationPoints import articulationPoints

class Partition:
    def __init__(self, map, n_districts, tile_districts, district_frontiers):
        self.map = map
        self.n_districts = n_districts
        self.tile_districts = tile_districts
        self.district_frontiers = district_frontiers

    def sameDistrictNeighbours(self, tile_idx):
        """ Helper function. """
        district = self.tile_districts[tile_idx]
        for tile_idx_2 in self.map.tile_neighbours[tile_idx]:
            if self.tile_districts[tile_idx_2] == district:
                yield tile_idx_2

    def otherDistrictNeighbours(self, tile_idx):
        """ Helper function. """
        district = self.tile_districts[tile_idx]
        for tile_idx_2 in self.map.tile_neighbours[tile_idx]:
            if self.tile_districts[tile_idx_2] != district:
                yield tile_idx_2

    def copy(self):
        return Partition(
            self.map,
            self.n_districts,
            self.tile_districts.copy(),
            deepcopy(self.district_frontiers),
        )

    def cantLose(self, district_idx):
        if len(self.district_frontiers[district_idx]) == 1:
            return self.district_frontiers[district_idx]
        return articulationPoints(self, district_idx)

    def mutate(self):
        district = random.randint(0, self.n_districts-1)
        cantLose = set(self.cantLose(district))
        options = [ i for i in np.where(self.tile_districts == district)[0] \
                    if i not in cantLose ]
        if len(options) == 0:
            return
        tile_idx = random.choice(options)
        swap_to = list(self.otherDistrictNeighbours(tile_idx))
        if len(swap_to):
            d_to = self.tile_districts[random.choice(swap_to)]
            self.switchTile(tile_idx, d_to)

    # def evaluate(self):
    #     areas = np.zeros(self.n_districts)
    #     perimeters = np.zeros(self.n_districts)
    #     for t_i in range(self.map.n_tiles):
    #         d_i = self.tile_districts[t_i]
    #         perimeters[d_i] += sum(1 for _ in self.otherDistrictNeighbours(t_i))
    #         areas[d_i] += 1

    #     concavity = 4 * math.pi * areas / (perimeters*perimeters)
    #     equality = areas.std() / areas.mean()
    #     return [ (1 - concavity).max(), equality ]

    def switchTile(self, tile_idx, d_to):
        d_from = self.tile_districts[tile_idx]
        assert d_from != d_to
        self.tile_districts[tile_idx] = d_to
        if self.tileIsFrontier(tile_idx):
            self.district_frontiers[d_to].add(tile_idx)
        self.district_frontiers[d_from].remove(tile_idx)
        for tile_idx_2 in self.map.tile_neighbours[tile_idx]:
            district_2 = self.tile_districts[tile_idx_2]
            # Remove from "disrict_to" frontier that may now be surroudned.
            if district_2 == d_to:
                if not self.tileIsFrontier(tile_idx_2):
                    self.district_frontiers[d_to].remove(tile_idx_2)
            # Add new tiles to the frontier from "district_from".
            if district_2 == d_from:
                self.district_frontiers[d_from].add(tile_idx_2)

    def tileIsFrontier(self, tile_idx):
        district = self.tile_districts[tile_idx]
        for tile_idx_2 in self.map.tile_neighbours[tile_idx]:
            if self.tile_districts[tile_idx_2] != district:
                return True
        return False

    def _validate(self):
        """ Debug method """
        for tile_idx in range(self.map.n_tiles):
            district_idx = self.tile_districts[tile_idx]
            if self.tileIsFrontier(tile_idx):
                assert tile_idx in self.district_frontiers[district_idx], \
                       f'{tile_idx} is frontier but not in {self.district_frontiers[district_idx]}'
                for district_idx_2 in range(self.n_districts):
                    if district_idx_2 != district_idx:
                        assert tile_idx not in self.district_frontiers[district_idx_2]
            else:
                for district_idx_2 in range(self.n_districts):
                    assert tile_idx not in self.district_frontiers[district_idx_2],\
                    f'{tile_idx} is not frontier but in d_{district_idx}'

    @classmethod
    def fromDistrictsArray(cls, map, n_districts, tile_districts):
        district_frontiers = [set() for _ in range(n_districts)]
        p = Partition(map, n_districts, tile_districts, district_frontiers)

        for i in range(map.n_tiles):
            if p.tileIsFrontier(i):
                district_frontiers[tile_districts[i]].add(i)
        return p

    @classmethod
    def makeRandom(cls, n_districts, map, seed=None):
        random.seed(seed)

        # Create a random seed for each disrict that is on the border.
        seeds = random.sample(map.boundry_tiles, n_districts)
        tile_districts = np.full(map.n_tiles, -1, dtype='i')
        district_frontiers = [ set([ seed ]) for seed in seeds ]
        for dist_idx, tile_idx in enumerate(seeds):
            tile_districts[tile_idx] = dist_idx

        # Preserve the front of the 'empty' district.
        empty_frontier = set()
        for t1 in seeds:
            for t2 in map.tile_neighbours[t1]:
                if tile_districts[t2] == -1:
                    empty_frontier.add(t2)

        # Treat 'empty' as a final district
        district_frontiers.append(empty_frontier)

        p = Partition(map, n_districts, tile_districts, district_frontiers)

        # Add empty tile to districts.
        while empty_frontier:
            tile = next(iter(empty_frontier))
            opts = [ t for t in map.tile_neighbours[tile] if tile_districts[t] >= 0 ]
            dist_dst = tile_districts[random.choice(opts)]
            p.switchTile(tile, dist_dst)

        # Remove the 'empty' frontier.
        p.district_frontiers = district_frontiers[:-1]

        return p

