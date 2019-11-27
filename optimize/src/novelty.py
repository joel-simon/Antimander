import numpy as np
class NoveltyMetric1():
    def __init__(self, state, n_districts):
        n_clusters = 500
        self.clusters = np.random.randint(0, n_districts, size=(n_clusters, n_districts), dtype='uint8')
        self.seen = np.zeros((n_clusters, n_districts), dtype='uint8')

    def __call__(self, X):
        seen.fill(0)
        for ci, cluster in enumerate(self.clusters):
            x = X[ci]
            for ti in clusters:
                di = x[ti]
                seen[di] = 1

