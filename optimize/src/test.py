import time
from src.utils import polygon
from collections import defaultdict, Counter
from itertools import combinations

def merge_overlapping_polygons(polygons):
    # start = time.time()
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
    # assert len(polygon) == len(outside_verts), (len(polygon), len(outside_verts), polygons)
    # print('Merged %i polygns in %f'%(len(polygons), time.time() - start))
    return polygon
    # except Exception as e:
    #     print("Failed to merge")
    #     print("SIZES:", [ len(p) for p in polygons ])
    #     for (i, p1), (j, p2) in combinations(enumerate(polygons), 2):
    #         print(i, j, len(set(p1) & set(p2)))
    #     raise e

def merge_polygons(polygons):
    # groups = []
    # for poly in polygons:
    return merge_overlapping_polygons(polygons)