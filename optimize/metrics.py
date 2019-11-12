import math
import numpy as np

# def compactness_polsby_popper(state, districts, n_districts):
#     areas = np.zeros(n_districts)
#     perimeters = np.zeros(n_districts)
#     for t_i in range(state.n_tiles):
#         d_i = districts[t_i]
#         perimeters[d_i] += sum(1 for _ in districts.otherDistrictNeighbours(t_i))
#         areas[d_i] += 1
#     concavity = 4 * math.pi * areas / (perimeters*perimeters)
#     return 1-concavity.mean()

def compactness(state, districts, n_districts):
    centers       = np.zeros((n_districts, 2))
    distances     = np.zeros(n_districts)
    district_size = np.zeros(n_districts)

    for t_i, d_i in enumerate(districts):
        centers[d_i] += state.tile_centers[t_i]
        district_size[d_i] += 1

    centers[:, 0] /= district_size
    centers[:, 1] /= district_size

    for t_i, d_i in enumerate(districts):
        distances[d_i] += np.linalg.norm(state.tile_centers[t_i] - centers[d_i])

    return distances.mean() / math.sqrt(state.n_tiles)

def efficiency_gap(state, districts, n_districts):
    d_pop = np.zeros((n_districts, 2) , dtype='i')
    lost_votes = np.zeros((n_districts, 2), dtype='i')
    total_votes = state.tile_populations.sum()

    for t_i in range(state.n_tiles):
        d_pop[districts[t_i]] += state.tile_populations[t_i]

    for d_i in range(n_districts):
        if d_pop[d_i, 0] > d_pop[d_i, 1]:
            lost_votes[d_i, 0] += d_pop[d_i, 0] - d_pop[d_i].mean()
            lost_votes[d_i, 1] += d_pop[d_i, 1]
        else:
            lost_votes[d_i, 1] += d_pop[d_i, 1] - d_pop[d_i].mean()
            lost_votes[d_i, 0] += d_pop[d_i, 0]

    total_lost = np.absolute(lost_votes[:, 0] - lost_votes[:, 1]).sum()
    score = total_lost / total_votes # range [0.5, 1]
    return (score-0.5) * 2 #[range 0, 1]