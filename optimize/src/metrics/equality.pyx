# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from libc.math cimport fmax, fmin, fabs
import numpy as np
cimport numpy as np
from src.districts cimport district_voters, district_populations

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
    return fmin(score, 1.0)
