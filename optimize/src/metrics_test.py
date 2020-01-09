import numpy as np
from scipy.spatial import ConvexHull, Delaunay
from src.utils.minimum_circle import make_circle, _make_circle_one_point, is_in_circle

def mean(data):
    n = 0
    mean = 0.0

    for x in data:
        n += 1
        mean += (x - mean)/n

    if n < 1:
        return float('nan');
    else:
        return mean

def compactness_ec(state, districts, n_districts):
    """ Compacntess with enclosing circle.
    """
    dist_points = [ [] for _ in range(n_districts) ]

    for ti in range(state.n_tiles):
        dist_points[ districts[ti] ].append( state.tile_centers[ti] )

    dist_circles = [ make_circle(pl) for pl in dist_points ]

    circle_counts = np.zeros(n_districts, dtype='uint8')

    for p in state.tile_centers:
        for di, circle in enumerate(dist_circles):
            if is_in_circle(circle, p):
                circle_counts[di] += 1

    # percents = [ len(p) / circle_counts[i] for i,p in enumerate(dist_points) ]
    percents = [  (circle_counts[i]-len(p))/len(p) for i,p in enumerate(dist_points) ]

    return mean(percents)

