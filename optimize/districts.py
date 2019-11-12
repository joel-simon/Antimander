import random
import numpy as np

def make_random(state, n_districts):
    seeds = random.sample(state.boundry_tiles, n_districts)
    partition = np.full(state.n_tiles, -1, dtype='i')
    indxs = np.arange(0, state.n_tiles)
    n_empty = state.n_tiles - len(seeds)

    for i, s in enumerate(seeds):
        partition[s] = i

    while n_empty > 0:
        np.random.shuffle(indxs)
        for t in indxs:
            if partition[t] != -1:
                continue
            options = []
            for t_other in state.tile_neighbours[t]:
                if partition[t_other] != -1:
                    options.append(t_other)
            if len(options):
                t_other = random.choice(options)
                partition[t] = partition[t_other]
                n_empty -= 1

    return partition
