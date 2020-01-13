# import numpy as np
# from scipy.spatial import ConvexHull, Delaunay
# from src.utils.minimum_circle import make_circle, _make_circle_one_point, is_in_circle

# def compactness_ec(state, districts, n_districts):
#     """ Compacntess with enclosing circle.
#     """
#     dist_points = [ [] for _ in range(n_districts) ]

#     for ti in range(state.n_tiles):
#         dist_points[ districts[ti] ].append( state.tile_centers[ti] )

#     dist_circles = [ make_circle(pl) for pl in dist_points ]

#     circle_counts = np.zeros(n_districts, dtype='uint8')

#     for p in state.tile_centers:
#         for di, circle in enumerate(dist_circles):
#             if is_in_circle(circle, p):
#                 circle_counts[di] += 1

#     percents = [  (circle_counts[i]-len(p))/len(p) for i,p in enumerate(dist_points) ]

#     return np.mean(percents)


# def compactness_reock(state, districts, n_districts):
#     circles = [ None for _ in range(n_districts) ]
#     for ti in range(state.n_tiles):
#         di = districts[ti]
#         for p in state.tile_vertices[ti]:
#             dist_points[  ].append( state.tile_centers[ti] )
#     # c = None
#     # for (i, p) in enumerate(points):
#     #     if c is None or not is_in_circle(c, p):
#     #         c = _make_circle_one_point(points[ : i + 1], p)
#     # return c

#     return state.area / sum( math.pi * c[2]**2 for c in circles )



# ################################################################################
# # Compactness using concave hull.
# ################################################################################
# def compactness_ch(state, districts, n_districts):
#     """ Compacntess with concave hull. """
#     dist_points = [ [] for _ in range(n_districts) ]

#     for ti in range(state.n_tiles):
#         dist_points[ districts[ti] ].append( state.tile_centers[ti] )

#     # Invalid to have a district of less than three tiles.
#     for pl in dist_points:
#         if len(pl) < 3:
#             return 1.0

#     dist_points = [ np.array(pl) for pl in dist_points ]
#     dist_hulls  = [ pl[ ConvexHull(pl).vertices ] for pl in dist_points ]
#     circle_counts = np.zeros(n_districts, dtype='uint8')

#     cdef float[:] center

#     for center in state.tile_centers:
#         for di, hull in enumerate(dist_hulls):
#             # if hull.contains_point(p):
#             if contains_point(hull, center[0], center[1]):
#                 circle_counts[di] += 1

#     percents = [ (circle_counts[i]-len(p)) / len(p) for i,p in enumerate(dist_points) ]
#     percents = [ max(0, min(p, 1.0)) for p in percents ]
#     # np.clip(percents, 0, 1, out=percents)
#     return np.mean(percents)