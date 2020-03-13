import math
from itertools import combinations
import numpy as np
from prince import MCA
from sklearn.decomposition import PCA
from pykdtree.kdtree import KDTree
from src import districts
from src.novelty_utils import histogram_features, histogram_features2

class NoveltyArchive(object):
    def __init__(self, state, n_districts, novelty_threshold=1.5,
                archive_stagnation=3,ns_K=10):
        self.state = state
        self.n_districts = n_districts
        self.novelty_threshold = novelty_threshold
        self.archive_stagnation = archive_stagnation
        self.evals_since_last_archiving = 0
        self.ns_K = ns_K
        # seeds = [ districts.make_random(state, n_districts) for _ in range(n_seeds) ]
        # self.archive = self._features(seeds)

    def _makeSparseness(self, features):
        feature_arr = np.array(features)
        tree = KDTree( np.vstack( (np.array(self.archive), feature_arr ) ) )
        dists, _ = tree.query(feature_arr, k=self.ns_K+1)
        sparseness = np.mean(dists[:, 1:], axis=1)
        sparseness /= sparseness.max()
        return sparseness

    def _features(self, districts):
        raise NotImplementedError()

    def getNovelty(self, districts):
        features   = self._features(districts)
        sparseness = self._makeSparseness(features)
        return sparseness

    def updateAndGetSparseness(self, districts):
        features   = self._features(districts)
        sparseness = self._makeSparseness(features)

        n_archive_added = 0
        for i, (feature, sp) in enumerate(zip(features, sparseness)):
            if sp > self.novelty_threshold:
                self.archive.append(feature)
                n_archive_added += 1

        if n_archive_added == 0:
            self.evals_since_last_archiving += 1
        else:
            self.evals_since_last_archiving = 0

        # Dynamic novelty_threshold
        if self.evals_since_last_archiving > self.archive_stagnation:
            self.novelty_threshold *= .9
        elif n_archive_added > 4:
            self.novelty_threshold *= 1.1

        return sparseness

class DistrictHistogramNoveltyArchive(NoveltyArchive):
    def __init__(self, state, n_districts, bins=16, n_seeds=200, **kwargs):
        self.bins = bins
        super().__init__(state, n_districts, **kwargs)
        seeds = [ districts.make_random(state, n_districts) for _ in range(n_seeds) ]
        self.archive = self._features(seeds)

    def _features(self, districts):
        districts = np.array(districts, dtype='i')
        return histogram_features2( 
            districts, self.n_districts, self.bins, self.state.tile_centers,
            self.state.tile_neighbors
        )

class MutualTilesNoveltyArchive(NoveltyArchive):

    def __init__(self, state, n_districts, n_seeds=200,
                 use_MCA=False, use_binary_features=True,
                 binary_n=2, **kwargs ):
        self.use_MCA = use_MCA
        self.use_binary_features = use_binary_features
        self.binary_n = binary_n # How many pairs to use, multiplier of the number of tiles.
        if use_MCA:
            self.dim_reduction = MCA( n_components=10 )
        else:
            self.dim_reduction = PCA( n_components=10 )

        seeds = [ districts.make_random(state, n_districts) for _ in range(n_seeds) ]

        if use_binary_features:
            n = state.n_tiles * self.binary_n
            self.binary_idxs_a = np.random.randint(0, high=state.n_tiles-1, size=n)
            self.binary_idxs_b = np.random.randint(0, high=state.n_tiles-1, size=n)
            seeds = [ self._makeBinaryFeature(f) for f in seeds ]

        self.dim_reduction.fit(np.array(seeds))
        self.archive = np.array(self.dim_reduction.transform(seeds)).tolist()
        super().__init__(state, n_districts, **kwargs)

    def _makeBinaryFeature(self, district):
        """ Convert a district (an integer array) into a binary array where each
            values corresponds to if a pair of tiles are in the same district.
        """
        return district[ self.binary_idxs_a ] == district[ self.binary_idxs_b ]

    def _features(self, districts):
        if self.use_binary_features:
            x = np.stack([ self._makeBinaryFeature(d) for d in districts ])
        else:
            x = districts
        x_reduced = np.array(self.dim_reduction.transform(x))
        return x_reduced
