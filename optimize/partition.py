import random
import numpy as np

def make_random(map, n_districts, seed=None):
    seeds = random.sample(map.boundry_tiles, n_districts)
    partition = np.full(map.n_tiles, -1, dtype='i')
    indxs = np.arange(0, map.n_tiles)
    n_empty = map.n_tiles - len(seeds)

    for i, s in enumerate(seeds):
        partition[s] = i

    while n_empty > 0:
        np.random.shuffle(indxs)
        for t in indxs:
            if partition[t] != -1:
                continue
            options = []
            for t_other in map.tile_neighbours[t]:
                if partition[t_other] != -1:
                    options.append(t_other)
            if len(options):
                t_other = random.choice(options)
                partition[t] = partition[t_other]
                n_empty -= 1

    return partition
