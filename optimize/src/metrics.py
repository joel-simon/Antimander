import math
import numpy as np
from src.utils import polygon
from scipy.spatial import ConvexHull, Delaunay
from src.utils.minimum_circle import make_circle
from src.metrics_x import equality, compactness, competitiveness, lost_votes, efficiency_gap

################################################################################
# Helper functions for compactness.

def district_points(state, districts, n_districts):
    points = [ [] for _ in range(n_districts) ]
    for ti in range(state.n_tiles):
        di = districts[ti]
        x0, y0, x1, y1 = state.tile_bboxs[ti]
        if  state.tile_boundaries[ti] or any(districts[ti_n] != di for ti_n in state.tile_neighbors[ti]):
            points[di].append((x0, y0))
            points[di].append((x1, y1))
            points[di].append((x0, y1))
            points[di].append((x1, y0))
    return points

def bounding_hulls(state, districts, n_districts):
    dist_points = [ np.array(p) for p in district_points(state, districts, n_districts) ]
    return [ pl[ ConvexHull(pl).vertices ] for pl in dist_points ]

def bounding_circles(state, districts, n_districts):
    dist_points = district_points(state, districts, n_districts)
    return [ make_circle(pl) for pl in dist_points ]

################################################################################

def compactness_reock(state, districts, n_districts):
    circles = bounding_circles(state, districts, n_districts)
    circles_area = sum( math.pi * c[2]**2 for c in circles )
    return 1.0 - ( state.area / circles_area )

def compactness_convex_hull(state, districts, n_districts):
    hulls = bounding_hulls(state, districts, n_districts)
    hulls_area = sum( polygon.area(h) for h in hulls )
    return 1.0 - (state.area / hulls_area)
