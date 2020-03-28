from .fairness import efficiency_gap, dem_advantage, rep_advantage, lost_votes 
from .compactness import reock, convex_hull, polsby_popper, center_distance, bounding_hulls, bounding_circles
from .equality import equality
from .competitiveness import competitiveness

from collections import defaultdict
limits = defaultdict(lambda:1)
limits['convex_hull'] = .6
limits['polsby_popper'] = .6
limits['reock'] = .65
limits['center_distance'] = 0.06
