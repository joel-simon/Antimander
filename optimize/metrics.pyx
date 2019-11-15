# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from libc.math cimport sqrt
import math
import numpy as np
cimport numpy as np

cdef inline float udist(float[:] a, float[:] b):
    """ Euclidian distance between two vectors.
        Faster than numpy.linalg.norm.
    """
    cdef float x = a[0] - b[0]
    cdef float y = a[1] - b[1]
    return sqrt(x*x + y*y)

cpdef float compactness(state, int[:] districts, int n_districts) except *:
    cdef float[:,:] tile_centers = state.tile_centers
    cdef float[:,:] centers   = np.zeros((n_districts, 2), dtype='float32')
    cdef float[:] distances   = np.zeros(n_districts, dtype='float32')
    cdef float[:] district_size = np.zeros(n_districts, dtype='float32')
    cdef int ti, di

    #---------------------------------------------------------------------------
    # Find the average point.
    for ti in range(districts.shape[0]):
        di = districts[ti]
        centers[di, 0] += tile_centers[ti, 0]
        centers[di, 1] += tile_centers[ti, 1]
        district_size[di] += 1

    for di in range(n_districts):
        centers[di, 0] /= district_size[di]
        centers[di, 1] /= district_size[di]

    #---------------------------------------------------------------------------

    for ti in range(districts.shape[0]):
        di = districts[ti]
        distances[di] += udist(tile_centers[ti], centers[di])

    return np.mean(distances) / sqrt(state.n_tiles)

cpdef float competitiveness(state, int[:] districts, int n_districts) except *:
    cdef int[:,:] tile_populations = state.tile_populations
    cdef float[:, :] dist_pop = np.zeros((n_districts, 2) , dtype='float32')
    cdef float margin
    cdef float max_margin = 0.0
    cdef int di, ti

    for ti in range(state.n_tiles):
        dist_pop[districts[ti], 0] += tile_populations[ti, 0]
        dist_pop[districts[ti], 1] += tile_populations[ti, 1]

    for di in range(n_districts):
        margin = abs(dist_pop[di, 0] - dist_pop[di, 1]) / (dist_pop[di, 0] + dist_pop[di, 1])
        if margin > max_margin:
            max_margin = margin

    return max_margin


cpdef float efficiency_gap(state, int[:] districts, int n_districts) except *:
    cdef int total_votes      = state.tile_populations.sum()
    cdef int[:, :] dist_pop   = np.zeros((n_districts, 2) , dtype='i')
    cdef int[:, :] lost_votes = np.zeros((n_districts, 2), dtype='i')
    cdef int[:,:] tile_populations = state.tile_populations
    cdef int ti, di, avg_pop

    for ti in range(state.n_tiles):
        dist_pop[districts[ti], 0] += tile_populations[ti, 0]
        dist_pop[districts[ti], 1] += tile_populations[ti, 1]

    for di in range(n_districts):
        avg_pop = <int>((dist_pop[di, 0]+dist_pop[di, 1])*0.5)
        if dist_pop[di,  0] > dist_pop[di, 1]:
            lost_votes[di, 0] += dist_pop[di, 0] - avg_pop
            lost_votes[di, 1] += dist_pop[di, 1]
        else:
            lost_votes[di, 1] += dist_pop[di, 1] - avg_pop
            lost_votes[di, 0] += dist_pop[di, 0]

    cdef int total_lost = 0
    for di in range(n_districts):
        total_lost += abs(lost_votes[di, 0] - lost_votes[di, 1])

    cdef float score = float(total_lost) / total_votes # range [0.5, 1]
    return (score-0.5) * 2 #[range 0, 1]

cpdef float compactness_polsby_popper(state, int[:] districts, int n_districts):
    cdef float[:] areas = np.zeros(n_districts, dtype='float32')
    cdef float[:] perimeters = np.zeros(n_districts, dtype='float32')
    cdef int ti, di, tj

    for ti in range(state.n_tiles):
        di = districts[ti]
        for tj in state.tile_neighbours[ti]:
            perimeters[di] += districts[ti] != districts[tj]
        areas[di] += 1

    cdef float p
    # cdef float mean_concavity = 0
    for di in range(n_districts):
        p = perimeters[di] * perimeters[di]
        areas[di] = 4 * math.pi * areas[di] / (p)

    return 1.0 - np.min(areas)
