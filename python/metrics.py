import math
import numpy as np

def compactness_polsby_popper(map, partition):
    areas = np.zeros(self.n_districts)
    perimeters = np.zeros(self.n_districts)
    for t_i in range(self.map.n_tiles):
        d_i = self.tile_districts[t_i]
        perimeters[d_i] += sum(1 for _ in partition.otherDistrictNeighbours(t_i))
        areas[d_i] += 1
    concavity = 4 * math.pi * areas / (perimeters*perimeters)
    return 1-concavity.mean()

def compactness_district_centers(map, partition):
    centers = np.zeros((partition.n_districts, 2))
    district_size = np.zeros(partition.n_districts)
    distances = np.zeros(partition.n_districts)
    for t_i, d_i in enumerate(partition.tile_districts):
        centers[d_i] += map.tile_centers[t_i]
        district_size[d_i] += 1
    centers[:, 0] /= district_size
    centers[:, 1] /= district_size
    for t_i, d_i in enumerate(partition.tile_districts):
        distances[d_i] += np.linalg.norm(map.tile_centers[t_i] - centers[d_i])
    return distances.mean() / math.sqrt(map.n_tiles)

def equality(map, partition):
    areas = np.zeros(partition.n_districts)
    for t_i in range(map.n_tiles):
        d_i = partition.tile_districts[t_i]
        areas[d_i] += 1
    equality = areas.std() / areas.mean()
    return equality

def efficiency_gap(map, partition):
    n_districts = partition.n_districts
    n_classes = map.tile_populations.shape[1]
    lost_votes = np.zeros((n_districts, 2), dtype='i')
    d_pop = np.zeros((n_districts, n_classes) , dtype='i')

    total_votes = map.tile_populations.sum()

    for t_i in range(map.n_tiles):
        d_i = partition.tile_districts[t_i]
        d_pop[d_i] += map.tile_populations[t_i]

    for d_i in range(n_districts):
        if d_pop[d_i, 0] > d_pop[d_i, 1]:
            lost_votes[d_i, 0] += d_pop[d_i, 0] - d_pop[d_i].mean()
            lost_votes[d_i, 1] += d_pop[d_i, 1]
        else:
            lost_votes[d_i, 1] += d_pop[d_i, 1] - d_pop[d_i].mean()
            lost_votes[d_i, 0] += d_pop[d_i, 0]

    total_lost = np.absolute(lost_votes[:, 0] - lost_votes[:, 1]).sum()
    return 1.0-(total_lost / total_votes)