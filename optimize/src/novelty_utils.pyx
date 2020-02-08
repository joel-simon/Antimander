# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from libc.math cimport sqrt, fabs, fmax
import math
import numpy as np
cimport numpy as np

cdef inline float udist(float[:] a, float[:] b):
    """ Euclidian distance between two 2D vectors. Faster than np.linalg.norm. """
    cdef float x = a[0] - b[0]
    cdef float y = a[1] - b[1]
    return sqrt(x*x + y*y)

cpdef list histogram_features(int[:,:] districts, int n_districts, int bins, float[:,:] tile_centers):
    # cdef int[:,:] result = np.zeros((districts.shape[0], bins), dtype='i')
    cdef list result = []
    cdef float[:,:] dcenters = np.zeros([ n_districts, 2 ], dtype='f')
    cdef float[:] counts = np.zeros(n_districts, dtype='f')
    # cdef int[:]
    cdef int i, ti, di, tj, b
    cdef list distances

    for i in range(districts.shape[0]):
        distances = []
        dcenters[:, :] = 0
        counts[:] = 0

        for ti in range(districts[i].shape[0]):
            di = districts[i, ti]
            counts[di] += 1

        for ti in range(districts[i].shape[0]):
            di = districts[i, ti]
            dcenters[di, 0] += tile_centers[ti, 0] / counts[di]
            dcenters[di, 1] += tile_centers[ti, 1] / counts[di]

        for ti in range(1, n_districts):
            for tj in range(ti):
                distances.append(udist(dcenters[ti], dcenters[tj]))

        # result[i, :] = np.array(np.histogram(distances, bins=bins)[0], dtype='i')
        result.append(np.histogram(distances, bins=bins)[0])

    return result