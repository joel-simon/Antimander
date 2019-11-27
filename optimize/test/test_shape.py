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

sf = shapefile.Reader("/Users/joelsimon/Downloads/gz_2010_55_140_00_500k(wisconsin_census_tracts)/gz_2010_55_140_00_500k.shp")
shapes = sf.shapes()
fig, ax = plt.subplots()
patches = []
pnts2dists = defaultdict(set)
centers = []

for idx, shape in enumerate(shapes):
    for p in shape.points:
        pnts2dists[p].add(idx)

    points = np.array(shape.points)
    centers.append(points.mean(axis=0).tolist())
    polygon = Polygon(points, True)
    patches.append(polygon)


boundry_tracts = []
for idx, shape in enumerate(shapes):
    for p in shape.points:
        if len(pnts2dists[p]) == 1:
            boundry_tracts.append(idx)
            break

edge_list = []
neighbors = [set() for _ in range(len(shapes))]

for dis_idxs in pnts2dists.values():
    for idx1, idx2 in combinations(dis_idxs, 2):
        neighbors[idx1].add(idx2)
        neighbors[idx2].add(idx1)
        edge_list.append((centers[idx1], centers[idx2]))

state = {
    'tract_shapes': [ s.points for s in shapes ],
    'adjacencies': [list(v) for v in neighbors ],
    'boundry_tracts': boundry_tracts
}
# print(state)
# with open('state.json', 'w') as fout:
#     json.dump(state, fout)

p = PatchCollection(patches, cmap=matplotlib.cm.jet, alpha=0.4)
colors = 100*np.random.rand(len(patches))
p.set_array(np.array(colors))

ax.add_collection(LineCollection(edge_list))

ax.add_collection(p)
ax.autoscale_view()
plt.show()