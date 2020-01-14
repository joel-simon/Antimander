# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from libc.math cimport sqrt, fabs, fmax
import math
import numpy as np
cimport numpy as np
from scipy.spatial import ConvexHull
from src.districts cimport district_voters, district_populations

################################################################################
# Equality
################################################################################
cpdef float equality(state, int[:] districts, int n_districts, float threshold=.05) except *:
    cdef int i
    cdef float d_score
    cdef float score = 0.0
    cdef float ideal_pop = float(state.population) / n_districts
    cdef int[:] dist_populations = district_populations(state, districts, n_districts)

    for i in range(n_districts):
        d_score = fabs(dist_populations[i] - ideal_pop) / ideal_pop
        if d_score < threshold:
            d_score = 0.0
        score = fmax(score, d_score)

    return min(score * 0.1, 1.0)

################################################################################
# Compactness
################################################################################
cpdef float compactness(state, int[:] districts, int n_districts) except *:
    cdef float[:,:] tile_centers = state.tile_centers
    cdef float[:,:] dist_centers = np.zeros((n_districts, 2), dtype='float32')
    cdef float[:] distances = np.zeros(n_districts, dtype='float32')
    cdef float[:] sizes = np.zeros(n_districts, dtype='float32')
    cdef int ti, di
    # Find the average point.
    for ti in range(state.n_tiles):
        di = districts[ti]
        dist_centers[di, 0] += tile_centers[ti, 0]
        dist_centers[di, 1] += tile_centers[ti, 1]
        sizes[di] += 1

    for di in range(n_districts):
        dist_centers[di, 0] /= sizes[di]
        dist_centers[di, 1] /= sizes[di]

    # Find distances to average point.
    for ti in range(state.n_tiles):
        di = districts[ti]
        distances[di] += udist(tile_centers[ti], dist_centers[di]) / sizes[di]

    return np.mean(distances) / max( state.bbox[2]-state.bbox[0], state.bbox[3]-state.bbox[1] )

cdef inline float udist(float[:] a, float[:] b):
    """ Euclidian distance between two vectors.
        Faster than numpy.linalg.norm.
    """
    cdef float x = a[0] - b[0]
    cdef float y = a[1] - b[1]
    return sqrt(x*x + y*y)

################################################################################
# Competitiveness
################################################################################
cpdef float competitiveness(state, int[:] districts, int n_districts) except *:
    cdef int[:, :] dist_voters = district_voters(state, districts, n_districts)
    cdef float margin, diff
    cdef float max_margin = 0.0
    cdef int di
    for di in range(n_districts):
        diff = float(abs(dist_voters[di, 0] - dist_voters[di, 1]))
        margin = diff / (dist_voters[di, 0] + dist_voters[di, 1])
        if margin > max_margin:
            max_margin = margin
    return max_margin

################################################################################
# Efficiency Gap
################################################################################
cpdef int[:, :] lost_votes(state, int[:] districts, int n_districts) except *:
    # Helper for efficiency_gap
    cdef int[:, :] dist_voters = district_voters(state, districts, n_districts)
    cdef int[:, :] lost_votes  = np.zeros((n_districts, 2), dtype='i')
    cdef int di, avg_pop
    for di in range(n_districts):
        avg_pop = (dist_voters[di, 0] + dist_voters[di, 1]) // 2
        if dist_voters[di,  0] > dist_voters[di, 1]:
            lost_votes[di, 0] += dist_voters[di, 0] - avg_pop
            lost_votes[di, 1] += dist_voters[di, 1]
        else:
            lost_votes[di, 0] += dist_voters[di, 0]
            lost_votes[di, 1] += dist_voters[di, 1] - avg_pop
    return lost_votes

cpdef float efficiency_gap(state, int[:] districts, int n_districts) except *:
    cdef float lost_a = 0
    cdef float lost_b = 0
    cdef int[:,:] lv = lost_votes(state, districts, n_districts)
    for di in range(n_districts):
        lost_a += lv[di, 0]
        lost_b += lv[di, 1]
    cdef float score = abs(lost_a - lost_b) / state.population
    return score

################################################################################
# cpdef float compactness_polsby_popper(state, int[:] districts, int n_districts):
#     cdef float[:] areas = np.zeros(n_districts, dtype='float32')
#     cdef float[:] perimeters = np.zeros(n_districts, dtype='float32')
#     cdef int ti, di, tj

#     for ti in range(state.n_tiles):
#         di = districts[ti]
#         for tj in state.tile_neighbors[ti]:
#             perimeters[di] += districts[ti] != districts[tj]
#         areas[di] += 1

#     cdef float p
#     # cdef float mean_concavity = 0
#     for di in range(n_districts):
#         p = perimeters[di] * perimeters[di]
#         areas[di] = 4 * math.pi * areas[di] / (p)

#     return 1.0 - np.min(areas)
