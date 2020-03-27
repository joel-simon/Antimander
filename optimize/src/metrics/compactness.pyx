# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from libc.math cimport sqrt, fabs, fmax, pi
import numpy as np
cimport numpy as np
from scipy.spatial import ConvexHull

from src.utils import polygon
from src.utils.minimum_circle import make_circle
from src.districts import district_boundry_points

################################################################################
# Utils.
cdef inline float udist(float[:] a, float[:] b):
    """ Euclidian distance between 2 2D vectors. Faster than np.linalg.norm. """
    cdef float x = a[0] - b[0]
    cdef float y = a[1] - b[1]
    return sqrt(x*x + y*y)
################################################################################

cpdef float center_distance(state, int[:] districts, int n_districts) except *:
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

################################################################################

cpdef float polsby_popper(state, int[:] districts, int n_districts) except *:
    cdef float[:] dist_areas      = np.zeros(n_districts, dtype='f')
    cdef float[:] dist_perimeters = np.zeros(n_districts, dtype='f')
    cdef float[:] tile_areas = state.tile_areas
    cdef int ti, di
    cdef object ti_1
    cdef dict edge_data

    for ti in range(state.n_tiles):
        di = districts[ti]
        dist_areas[di] += tile_areas[ti]

        for ti_1, edge_data in state.tile_edges[ti].items():
            if ti_1 == 'boundry' or districts[ti] != districts[ti_1]:
                dist_perimeters[di] += edge_data['length']

    cdef float pp_score = 0
    for di in range(n_districts):
        pp_score += ((4 * pi * dist_areas[di]) / (dist_perimeters[di]*dist_perimeters[di]))
    
    pp_score /= n_districts

    return 1.0 - pp_score

################################################################################

def bounding_hulls(state, districts, n_districts):
    """ Return the convex hull of each district. """
    dist_points = district_boundry_points(state, districts, n_districts)
    return [ polygon.convex_hull(pl) for pl in dist_points ]

def convex_hull(state, districts, n_districts):
    """ Compactness metric: inverse to the sum hull areas. """
    hulls = bounding_hulls(state, districts, n_districts)
    hulls_area = sum( polygon.area([ h ]) for h in hulls )
    return 1.0 - (state.area / hulls_area)

################################################################################

def bounding_circles(state, districts, n_districts):
    """ Return the bounding circle of each district. """
    dist_points = district_boundry_points(state, districts, n_districts)
    return [ make_circle(pl) for pl in dist_points ]

def reock(state, districts, n_districts):
    """ Compactness metric: inverse to the sum circle areas. """
    circles = bounding_circles(state, districts, n_districts)
    circles_area = sum( pi * c[2]**2 for c in circles )
    return 1.0 - ( state.area / circles_area )
