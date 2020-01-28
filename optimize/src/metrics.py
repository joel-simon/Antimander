import math
import numpy as np
from src.utils import polygon
from scipy.spatial import ConvexHull, Delaunay
from src.utils.minimum_circle import make_circle
from src.metrics_x import equality, compactness, competitiveness, lost_votes, efficiency_gap
from src.utils.convex_hull import convex_hull
from src.districts import district_boundry_points

################################################################################

def bounding_hulls(state, districts, n_districts):
    """ Return the convex hull of each district. """
    dist_points = district_boundry_points(state, districts, n_districts)
    dist_points = [ np.array(x, dtype='f') for x in dist_points ]
    hulls = [ pl[ ConvexHull(pl).vertices ] for pl in dist_points ]
    return hulls

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




