import json
import numpy as np
import matplotlib as plt
import shapefile
from collections import defaultdict
from itertools import combinations

import matplotlib.pyplot as plt
import matplotlib
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection, LineCollection
import time

plot = False
save = True

t = time.time()
sf = shapefile.Reader('/Users/joelsimon/Data/gerrymandering/NC_VTD/NC_VTD.shp')

shapes = sf.shapes()
records = sf.records()
patches = []
pnts2tiles = defaultdict(set)
centers = []

for idx, shape in enumerate(shapes):
    for p in shape.points:
        pnts2tiles[p].add(idx)
    points = np.array(shape.points)
    centers.append(points.mean(axis=0).tolist())
    polygon = Polygon(points, True)
    patches.append(polygon)

boundry_tracts = np.zeros(len(records), dtype='i')
for idx, shape in enumerate(shapes):
    for p in shape.points:
        if len(pnts2tiles[p]) == 1:
            boundry_tracts[idx] = 1
            break

edge_list = []
neighbors = [ set() for _ in range(len(shapes)) ]
for dis_idxs in pnts2tiles.values():
    for idx1, idx2 in combinations(dis_idxs, 2):
        neighbors[idx1].add(idx2)
        neighbors[idx2].add(idx1)
        edge_list.append((centers[idx1], centers[idx2]))

# Fix islands
# to_remove = set(i for i, n in enumerate(neighbors) if len(n) < 1)
# print('to filter', to_remove)

for idx, shape in enumerate(shapes):
    for p in shape.points:
        pnts2tiles[p].add(idx)
    points = np.array(shape.points)
    centers.append(points.mean(axis=0).tolist())
    polygon = Polygon(points, True)
    patches.append(polygon)

# state = {
#     'shapes'  : [ s.points for i,s in enumerate(shapes) if i not in to_remove ],
#     'neighbors'   : [ list(v) for i,v in enumerate(neighbors) if i not in to_remove ],
#     'boundry_tracts': [ x for i, x in enumerate(boundry_tracts) if i not in to_remove ],
#     'populations': [ r['PERSONS'] for r in records ],
#     'democrats': [ (r['PREDEM16'] + r['PREDEM12'])//2 for i,r in enumerate(records) if i not in to_remove ],
#     'republicans': [ (r['PREREP16'] + r['PREREP12'])//2 for i,r in enumerate(records) if i not in to_remove ]
#     # 'tract_data_header': records_to_use,
#     # 'tract_data': [ [ r[name] for name in records_to_use ] for r in records ]
# }

# WI
# state = {
#     'shapes'  : [ s.points for s in shapes ],
#     'neighbors'   : [ list(v) for v in neighbors ],
#     'boundry_tracts': boundry_tracts,
#     'populations': [ r['PERSONS'] for r in records ],
#     'democrats': [ (r['PREDEM16'] + r['PREDEM12'])//2 for r in records ],
#     'republicans': [ (r['PREREP16'] + r['PREREP12'])//2 for r in records ]
# }

# NC
democrats = [ (r['EL12G_PR_D'] + r['EL16G_PR_D'])//2 for r in records ]
republicans = [ (r['EL12G_PR_R'] + r['EL16G_PR_R'])//2 for r in records ]

state = {
    'vertices'  : [ s.points for s in shapes ],
    'neighbors'   : [ list(v) for v in neighbors ],
    'boundaries': boundry_tracts.tolist(),
    'populations': [ r['PL10AA_TOT'] for r in records ],
    'population': sum([ r['PL10AA_TOT'] for r in records ]),
    'voters': list(zip(democrats, republicans)),
    'bbox': list(sf.bbox),
}

if save:
    with open('data/NC.json', 'w') as fout:
        json.dump(state, fout)

if plot:
    patches = [p for i, p in enumerate(patches) if i not in to_remove]

    # for shape in state['shapes']:
    #     points = np.array(shape)
    #     centers.append(points.mean(axis=0).tolist())
    #     polygon = Polygon(points, True)
    #     patches.append(polygon)

    # for dis_idxs in pnts2tiles.values():
    #     for idx1, idx2 in combinations(dis_idxs, 2):
    #         edge_list.append((centers[idx1], centers[idx2]))


    fig, ax = plt.subplots(figsize=(15, 15))
    p = PatchCollection(patches, cmap=matplotlib.cm.jet, alpha=0.4)
    colors = 100*np.random.rand(len(patches))
    p.set_array(np.array(colors))
    # ax.add_collection(LineCollection(edge_list))
    ax.add_collection(p)
    ax.autoscale_view()
    plt.show()