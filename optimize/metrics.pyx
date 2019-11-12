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

cpdef float efficiency_gap(state, int[:] districts, int n_districts) except *:
    cdef int total_votes      = state.tile_populations.sum()
    cdef int[:, :] dist_pop   = np.zeros((n_districts, 2) , dtype='i')
    cdef int[:, :] lost_votes = np.zeros((n_districts, 2), dtype='i')
    cdef int[:,:] tile_populations = state.tile_populations
    cdef int ti, di

    for ti in range(state.n_tiles):
        dist_pop[districts[ti], 0] += tile_populations[ti, 0]
        dist_pop[districts[ti], 1] += tile_populations[ti, 1]

    for di in range(n_districts):
        if dist_pop[di,  0] > dist_pop[di, 1]:
            lost_votes[di, 0] += dist_pop[di, 0] - <int>((dist_pop[di, 0]+dist_pop[di, 1])*0.5)
            lost_votes[di, 1] += dist_pop[di, 1]
        else:
            lost_votes[di, 1] += dist_pop[di, 1] - <int>((dist_pop[di, 0]+dist_pop[di, 1])*0.5)
            lost_votes[di, 0] += dist_pop[di, 0]

    cdef int total_lost = 0
    for di in range(n_districts):
        total_lost += abs(lost_votes[di, 0] - lost_votes[di, 1])

    cdef float score = float(total_lost) / total_votes # range [0.5, 1]
    return (score-0.5) * 2 #[range 0, 1]



# def compactness_polsby_popper(state, districts, n_districts):
#     areas = np.zeros(n_districts)
#     perimeters = np.zeros(n_districts)
#     for t_i in range(state.n_tiles):
#         d_i = districts[t_i]
#         perimeters[d_i] += sum(1 for _ in districts.otherDistrictNeighbours(t_i))
#         areas[d_i] += 1
#     concavity = 4 * math.pi * areas / (perimeters*perimeters)
#     return 1-concavity.mean()
