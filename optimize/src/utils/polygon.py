# from collections import defaultdict

# from shapely.geometry import Polygon
# from shapely.ops import cascaded_union
import pyclipper

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
    return abs(shoelace(vertices)) / 2

def centroid(point_list):
    x = [p[0] for p in point_list]
    y = [p[1] for p in point_list]
    minx, maxx = min(x), max(x)
    miny, maxy = min(y), max(y)
    dx = (maxx + minx) / 2
    dy = (maxy + miny) / 2
    return (dx, dy)

def union(polygons):
    s = 10000
    polygons = [[ (int(x*s), int(y*s)) for x,y in p ] for p in polygons ]
    pc = pyclipper.Pyclipper()
    pc.AddPaths(polygons, pyclipper.PT_SUBJECT, closed=True)
    result = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)
    return [[ (x/s, y/s)  for x,y in p ] for p in result ]

def offset(poly, v):
    s = 10000
    poly = [ (int(x*s), int(y*s)) for x,y in poly ]
    pco = pyclipper.PyclipperOffset()
    pco.AddPath(poly, pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
    solution = pco.Execute(v)
    return [ (x/s, y/s)  for x,y in solution[0] ]

def test(polygons):
    """ A temporary hack. Union polygon
    """
    polygons = [ offset(p, 5) for p in polygons ]
    return [ offset(union(polygons)[0], -5) ]

# def merge(polygons):
#     """ Assumes poylgons **share vertices.**
#     """
#     vert2poly = defaultdict(set)
#     for poly_idx, poly in enumerate(polygons):
#         for vert in poly:
#             vert2poly[vert].add(poly_idx)

#