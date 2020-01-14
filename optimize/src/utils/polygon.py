import pyclipper
import numpy as np
from src.utils import polygon_x

def shoelace(vertices):
    """ The shoelace algorithm for polgon area """
    area = 0.0
    n = len(vertices)
    for i in range(n):
        j = (i + 1) % n
        area += (vertices[j][0] - vertices[i][0]) * \
                (vertices[j][1] + vertices[i][1])
    return area

def area(vertices):
    if type(vertices) == np.ndarray:
        return polygon_x.area(vertices)
    else:
        return abs(shoelace(vertices)) / 2

def centroid(point_list):
    x = [p[0] for p in point_list]
    y = [p[1] for p in point_list]
    minx, maxx = min(x), max(x)
    miny, maxy = min(y), max(y)
    dx = (maxx + minx) / 2
    dy = (maxy + miny) / 2
    return (dx, dy)

def union(polygons, s=10000):
    polygons = [[ (int(x*s), int(y*s)) for x,y in p ] for p in polygons ]
    pc = pyclipper.Pyclipper()
    pc.AddPaths(polygons, pyclipper.PT_SUBJECT, closed=True)
    result = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
    return [[ (x/s, y/s)  for x,y in p ] for p in result ]

def offset(poly, v, s=10000):
    poly = [ (int(x*s), int(y*s)) for x,y in poly ]
    pco = pyclipper.PyclipperOffset()
    pco.AddPath(poly, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
    solution = pco.Execute(v)
    return [ (x/s, y/s) for x,y in solution[0] ]

def bounding_box(polygon):
    if len(polygon) < 3:
        raise ValueError('Polygon must have more than two points.')
    bbox = [ float('inf'), float('inf'), float('-inf'), float('-inf')  ]
    for x,y in polygon:
        bbox[0] = min(bbox[0], x)
        bbox[1] = min(bbox[1], y)
        bbox[2] = max(bbox[2], x)
        bbox[3] = max(bbox[3], y)
    return bbox

    raise

# def union_offset(polygons, s=10000, off=5):
#     """ A temporary hack. Union polygon
#     """
#     polygons = [ offset(p, off, s) for p in polygons ]
#     merged = union(polygons, s)
#     return [ offset(p, -off, s) for p in merged ]

import time
from collections import defaultdict, Counter
from itertools import combinations
def merge_polygons(polygons):
    """ Assumes polygons **share identical integer vertices.**
    """
    # try:
    start = time.time()
    edge_faces = Counter()
    for pi, poly in enumerate(polygons):
        for vi, v in enumerate(poly):
            v_n = poly[(vi+1)%len(poly)]
            edge_faces[(min(v, v_n), max(v, v_n))] += 1
    outside_edges = set(e for e, c in edge_faces.items() if c == 1)
    vert_neighbors = defaultdict(set)
    for v1, v2 in outside_edges:
        vert_neighbors[v1].add(v2)
        vert_neighbors[v2].add(v1)
    outside_verts = list(vert_neighbors.keys())
    if len(outside_verts) == 0: # TODO fix this.
        return []
    vert = next(iter(outside_verts))
    start_vert = vert
    added = set()
    polygon = []
    while True:
        assert vert not in added
        polygon.append(vert)
        added.add(vert)
        options = [ v for v in vert_neighbors[ vert ] if v not in added ]
        if len(options) == 0:
            break
        vert = options[0]
    assert len(polygon) == len(outside_verts), (len(polygon), len(outside_verts), polygons)
    # print('Merged %i polygns in %f'%(len(polygons), time.time() - start))
    return polygon
    # except Exception as e:
    #     print("Failed to merge")
    #     print("SIZES:", [ len(p) for p in polygons ])
    #     for (i, p1), (j, p2) in combinations(enumerate(polygons), 2):
    #         print(i, j, len(set(p1) & set(p2)))
    #     raise e
