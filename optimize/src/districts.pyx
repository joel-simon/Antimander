# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
import random
import numpy as np
cimport numpy as np

cpdef int[:] count_pop(state, int[:] partition, int n_districts) except *:
    cdef int[:, :] tile_populations = state.tile_populations
    cdef int[:] d_pop = np.zeros(n_districts , dtype='i')
    cdef int ti
    for ti in range(state.n_tiles):
        d_pop[partition[ti]] += tile_populations[ ti, 0 ]
        d_pop[partition[ti]] += tile_populations[ ti, 1 ]
    return d_pop

cpdef bint is_frontier(int[:] partition, state, int ti) except *:
    cdef int tj
    cdef int di = partition[ti]
    for tj in state.tile_neighbours[ti]:
        if partition[tj] != di:
            return True
    return False

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
