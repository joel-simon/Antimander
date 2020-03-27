import os, sys, time, math, json
import numpy as np
import matplotlib as plt
import shapefile
from collections import defaultdict, Counter
from itertools import combinations
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection, LineCollection
sys.path.append(os.path.abspath('.'))
from src.utils.polygon import convex_hull

def validate_neighbors(neighbors):
    for i, n in enumerate(neighbors):
        for j in n:
            assert i in neighbors[j], (i, j)
            # if i not in neighbors[j]:
                # print('wtf', (i, j))

def parse(sf):
    shapes = sf.shapes()
    records = sf.records()
    pnts2tiles = defaultdict(set)
    centers = []
    multipolygons = []
    N = len(shapes)

    for idx, shape in enumerate(shapes):
        for p in shape.points:
            pnts2tiles[p].add(idx)
        points = np.array(shape.points)
        centers.append(points.mean(axis=0).tolist())
        multigon = []
        shape.parts.append(len(shape.points))
        for i in range(len(shape.parts)-1):
            polygon = points[shape.parts[i]: shape.parts[i+1]]
            multigon.append( polygon.tolist() )

        multipolygons.append(multigon)

    boundry_tracts = [ 0 for _ in range(N) ]
    for idx, shape in enumerate(shapes):
        for p in shape.points:
            if len(pnts2tiles[p]) == 1:
                boundry_tracts[idx] = 1
                break

    neighbors = [ set() for _ in range(len(shapes)) ]
    for tile_idxs in pnts2tiles.values():
        for idx1, idx2 in combinations(tile_idxs, 2):
            if len(set(shapes[idx1].points) & set(shapes[idx2].points)) > 1:
                neighbors[idx1].add(idx2)
                neighbors[idx2].add(idx1)

    ############################################################################
    """ Merge donut holes - tiles are within another. """
    to_remove = [ ]
    def poly2set(poly):
        return frozenset((round(x), round(y)) for x,y in poly)
    for i in range(N):
        if len(neighbors[i]) == 1:
            j = list(neighbors[i])[0]
            verts_i = set(poly2set(p) for p in multipolygons[i])
            to_remove.append(i)
            records[j]['PREDEM16'] += records[i]['PREDEM16']
            records[j]['PREDEM12'] += records[i]['PREDEM12']
            records[j]['PREREP16'] += records[i]['PREREP16']
            records[j]['PREREP12'] += records[i]['PREREP12']
            records[j]['PERSONS'] += records[i]['PERSONS']
            multipolygons[j] = [ p for p in multipolygons[j] if poly2set(p) not in verts_i ]
            assert records[j]['CON'] == records[i]['CON']

    for index in sorted(to_remove, reverse=True):
        del records[index]
        del centers[index]
        del neighbors[index]
        del boundry_tracts[index]
        del multipolygons[index]
    d = 0
    idx_map = list(range(N))
    for i in range(N):
        idx_map[i] -= d
        if i in to_remove:
            d += 1
    N -= len(to_remove)
    neighbors = [[idx_map[n] for n in nl if n not in to_remove] for nl in neighbors]

    ############################################################################
    """ Temporary HACK, merge the WI disconnected island. """
    to_remove = [1318, 1319, 1323, 1324, 1325, 1326, 1327, 1333, 1334, 1335, 1336, 1337, 1338, 1339, 1343, 1344, 1345, 1346, 1347, 1348, 1349, 1350, 1351, 1352, 1358, 1359, 1360, 1361, 1362, 1363, 1364, 1369, 1370, 1375, 1376, 1379]
    d = 0
    idx_map = list(range(N))
    for i in range(N):
        idx_map[i] -= d
        if i in to_remove:
            d += 1
    N -= len(to_remove)
    new_record = defaultdict(lambda: 0)
    new_record['CON'] = records[to_remove[0]]['CON']
    assert all(new_record['CON'] == records[idx]['CON'] for idx in to_remove)
    new_polygons = []
    new_center = []
    for index in sorted(to_remove, reverse=True):
        for name in ['PREDEM16', 'PREDEM12', 'PREDEM12', 'PREREP12', 'PERSONS']:
            new_record[name] += records[index][name]
        new_polygons.extend(multipolygons[index])
        new_center.append(centers[index])

        del records[index]
        del centers[index]
        del neighbors[index]
        del boundry_tracts[index]
        del multipolygons[index]

    neighbors = [[idx_map[n] for n in nl if n not in to_remove] for nl in neighbors]
    centers.append(np.mean(new_center, axis=0).tolist())
    records.append(new_record)
    multipolygons.append(new_polygons)
    boundry_tracts.append(1)
    neighbors.append([])

    ############################################################################
    """ Fix islands - tiles that have no neighbors. """
    def cdist(i, j):
        x1, y1 = centers[i]
        x2, y2 = centers[j]
        return math.hypot(x2 - x1, y2 - y1)
    for i, n in enumerate(neighbors):
        if len(n) == 0:
            # get closest tiles to be neighbors.
            dists = [ (cdist(i, j), j) for j in range(N) if j!=i ]
            dists.sort()
            for k in range(4):
                neighbors[i].append(dists[k][1])
                neighbors[dists[k][1]].append(i)
    ############################################################################
    return multipolygons, records, neighbors, boundry_tracts, centers

def WI(shape_path):
    sf = shapefile.Reader(shape_path)
    multipolygons, records, neighbors, boundry_tracts, centers = parse(sf)
    democrats   = [ (r['PREDEM16'] + r['PREDEM12'])//2 for r in records ]
    republicans = [ (r['PREREP16'] + r['PREREP12'])//2 for r in records ]
    real_districts = [ r['CON'] for r in records ]
    state = {
        'shapes' : multipolygons,
        'neighbors' : [ list(v) for v in neighbors ],
        'boundaries': boundry_tracts,
        'populations': [ r['PERSONS'] for r in records ],
        'population': sum([ r['PERSONS'] for r in records ]),
        'voters': list(zip(democrats, republicans)),
        'bbox': list(sf.bbox),
        'centers': centers,
        'real_districts': real_districts
    }
    return state

# def NC():
#     sf = shapefile.Reader('/Users/joelsimon/Data/gerrymandering/NC_VTD/NC_VTD.shp')
#     shapes, records, patches, neighbors, boundry_tracts = parse(sf)
#     democrats   = [ (r['EL12G_PR_D'] + r['EL16G_PR_D'])//2 for r in records ]
#     republicans = [ (r['EL12G_PR_R'] + r['EL16G_PR_R'])//2 for r in records ]
#     state = {
#         'vertices'  : [ s.points for s in shapes ],
#         'neighbors'   : [ list(v) for v in neighbors ],
#         'boundaries': boundry_tracts,
#         'populations': [ r['PL10AA_TOT'] for r in records ],
#         'population': sum([ r['PL10AA_TOT'] for r in records ]),
#         'voters': list(zip(democrats, republicans)),
#         'bbox': list(sf.bbox),
#     }
#     return state, patches


plot = True
plot_neighbors = True
save = True
state_name = 'WI'
shape_path = sys.argv[1]
# state_name = 'NC'

state = WI(shape_path) if state_name == 'WI' else NC()

if save:
    with open('data/%s.json'%state_name, 'w') as fout:
        json.dump(state, fout)

if plot:
    colors = []
    patches = []
    for i, multipolygon in enumerate(state['shapes']):
        # color = 100*np.random.rand()
        color = state['real_districts'][i] * 10
        for polygon in multipolygon:
            patches.append(Polygon(polygon, True))
            colors.append(color)

    edge_list = []
    if plot_neighbors:
        for ti1, neighbors in enumerate(state['neighbors']):
            for ti2 in neighbors:
                edge_list.append((state['centers'][ti1], state['centers'][ti2]))

    fig, ax = plt.subplots(figsize=(12, 12))
    p = PatchCollection(patches, cmap=matplotlib.cm.gist_rainbow, alpha=0.4)
    p.set_array(np.array(colors))
    ax.add_collection(LineCollection(edge_list))
    ax.add_collection(p)

    for i, multipolygon in enumerate(state['shapes']):
        color = state['real_districts'][i] * 10
        for polygon in multipolygon:
            ax.plot([v[0] for v in polygon], [v[1] for v in polygon], color='black')

    ax.autoscale_view()
    plt.show()