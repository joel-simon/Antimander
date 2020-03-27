# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from libc.math cimport fmax, fmin
import numpy as np
cimport numpy as np
from src.districts cimport district_voters

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

def inefficiency_gap(state, districts, n_districts):
    return 1.0 - efficiency_gap(state, districts, n_districts)

def dem_advantage(state, districts, n_districts):
    lv = np.array(lost_votes(state, districts, n_districts))
    return lv[:, 0].sum() / state.population # Count dem lost votes.
    
def rep_advantage(state, districts, n_districts):
    lv = np.array(lost_votes(state, districts, n_districts))
    return lv[:, 1].sum() / state.population # Count rep lost votes.
