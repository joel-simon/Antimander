# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from libc.math cimport fabs, fmax
from src.districts cimport district_voters

cpdef float competitiveness(state, int[:] districts, int n_districts, float threshold=0.02) except *:
    # Consider anything below 2% equally competitive.
    cdef int[:, :] dist_voters = district_voters(state, districts, n_districts)
    cdef float margin, diff
    cdef float max_margin = 0.0
    cdef int di
    for di in range(n_districts):
        diff = float(fabs(dist_voters[di, 0] - dist_voters[di, 1]))
        margin = diff / (dist_voters[di, 0] + dist_voters[di, 1])
        max_margin = fmax(max_margin, margin)
    return fmax(max_margin, threshold)