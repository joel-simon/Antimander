# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from libc.math cimport sqrt, fabs, fmax
import math
import random
import numpy as np
cimport numpy as np
from libc.stdlib cimport rand, RAND_MAX

cdef int rand_int(int min, int max):
    """ Fast cython randint """
    return int(min + (rand()/float(RAND_MAX)) * (max - min))

cdef inline float udist(float[:] a, float[:] b):
    """ Euclidian distance between two 2D vectors. Faster than np.linalg.norm. """
    cdef float x = a[0] - b[0]
    cdef float y = a[1] - b[1]
    return sqrt(x*x + y*y)

cpdef float[:,:,:] dist_centers(int[:,:] districts, int n_districts, float[:,:] tile_centers):
    cdef int i, ti, di
    cdef int n_districtings = districts.shape[0]
    cdef int n_tiles = districts.shape[1]
    cdef float[:,:,:] dcenters = np.zeros([ n_districtings, n_districts, 2 ], dtype='f')
    cdef float[:] counts = np.zeros(n_districts, dtype='f')
    for i in range(n_districtings):
        counts[:] = 0
        for ti in range(n_tiles):
            di = districts[i, ti]
            counts[di] += 1
        for ti in range(n_tiles):
            di = districts[i, ti]
            dcenters[i, di, 0] += tile_centers[ti, 0] / counts[di]
            dcenters[i, di, 1] += tile_centers[ti, 1] / counts[di]
    return dcenters

cpdef list centers_histograms(int[:,:] districts, int n_districts, int bins, float[:,:] tile_centers):
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
        # print(distances)
        result.append(np.histogram(distances, bins=bins)[0])

    return result

cpdef list edges_histograms(
    int[:, :] districts, int n_districts, int bins, int n,
    float[:,:] tile_centers, list tile_neighbors
):
    """ Histogram of distances between tiles within the same district. """
    cdef int i, j, ti, di, tj, n_edge_tiles
    cdef list district_tis
    cdef list result = []
    cdef int n_tiles = districts.shape[1]
    cdef float[:] values = np.zeros(n, dtype='f')
    for i in range(districts.shape[0]):
        edge_tiles = []
        values[:] = 0.0
        for ti in range(n_tiles):
            di = districts[i, ti]
            for tj in tile_neighbors[ti]:
                if di != districts[i, tj]:
                    edge_tiles.append(ti)
                    break
        n_edge_tiles = len(edge_tiles)
        for j in range(n):
            ti = rand() % n_edge_tiles
            tj = rand() % n_edge_tiles
            values[j] = udist(tile_centers[ti], tile_centers[tj])
        result.append(np.histogram(values, bins=bins, density=True)[0])
    return result
