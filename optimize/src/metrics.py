import math
import numpy as np
from src.utils import polygon
from src.utils.minimum_circle import make_circle
from src.districts import district_boundry_points
from src.metrics_x import *

################################################################################

def bounding_hulls(state, districts, n_districts):
    """ Return the convex hull of each district. """
    dist_points = district_boundry_points(state, districts, n_districts)
    return [ polygon.convex_hull(pl) for pl in dist_points ]

def compactness_convex_hull(state, districts, n_districts):
    """ Compactness metric: inverse to the sum hull areas. """
    hulls = bounding_hulls(state, districts, n_districts)
    hulls_area = sum( polygon.area(h) for h in hulls )
    return 1.0 - (state.area / hulls_area)

################################################################################

def bounding_circles(state, districts, n_districts):
    """ Return the bounding circle of each district. """
    dist_points = district_boundry_points(state, districts, n_districts)
    return [ make_circle(pl) for pl in dist_points ]

def compactness_reock(state, districts, n_districts):
    """ Compactness metric: inverse to the sum circle areas. """
    circles = bounding_circles(state, districts, n_districts)
    circles_area = sum( math.pi * c[2]**2 for c in circles )
    return 1.0 - ( state.area / circles_area )

# def polsby_popper(state, districts, n_districts):
#     dist_areas      = np.zeros(n_districts, dtype='f')
#     dist_perimeters = np.zeros(n_districts, dtype='f')

#     for ti in range(state.n_tiles):
#         di = districts[ti]
#         dist_areas[di] += state.tile_areas[ti]

#         for ti_1, edge_data in state.tile_edges[ti].items():
#             if ti_1 == 'boundry' or districts[ti] != districts[ti_1]:
#                 dist_perimeters[di] += edge_data['length']

#     pp_scores = (4 * math.pi * dist_areas) / (dist_perimeters*dist_perimeters)

#     return 1.0 - pp_scores.mean()