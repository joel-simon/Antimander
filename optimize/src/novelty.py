from prince import MCA
from sklearn.decomposition import PCA
import numpy as np
from pykdtree.kdtree import KDTree

from src import districts

class NoveltyArchive(object):
    def __init__(
        self, state, n_districts,
        n_seeds=200,
        novelty_threshold=1.5,
        archive_stagnation=3,
        ns_K=10,
        use_MCA=False
    ):
        self.state = state
        self.novelty_threshold = novelty_threshold
        self.archive_stagnation = archive_stagnation
        self.evals_since_last_archiving = 0
        self.ns_K = ns_K
        self.use_MCA = use_MCA

        initial_adj = [
            self.makeAdjanecy(districts.make_random(state, n_districts))
            for _ in range(n_seeds)
        ]

        if use_MCA:
            self.dim_reduction = MCA( n_components=10 )
        else:
            self.dim_reduction = PCA( n_components=10 )

        self.dim_reduction.fit(np.array(initial_adj))
        self.archive = self.dim_reduction.transform(initial_adj).tolist()
        # self.novelty_threshold = self.makeSparseness([ ]).mean()
        # print('self.novelty_threshold', self.novelty_threshold)

    def makeAdjanecy(self, district):
        n = self.state.n_tiles * 2
        a = np.random.randint(0, high=district.shape[0]-1, size=n)
        b = np.random.randint(0, high=district.shape[0]-1, size=n)
        np.random.shuffle(b)
        return district[a] == district[b]

    def makeSparseness(self, features):
        feature_arr = np.array(features)
        tree = KDTree( np.vstack( (np.array(self.archive), feature_arr ) ) )
        dists, _ = tree.query(feature_arr, k=self.ns_K+1)
        sparseness = np.mean(dists[:, 1:], axis=1)
        return sparseness

    def updateAndGetSparseness(self, districts):
        adj = np.stack([ self.makeAdjanecy(d) for d in districts ])
        features = np.array(self.dim_reduction.transform(adj))
        sparseness = self.makeSparseness(features)

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
