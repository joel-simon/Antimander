# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
import random
import numpy as np
cimport numpy as np

cpdef int[:] district_populations(state, int[:] districts, int n_districts) except *:
    cdef int[:] tile_populations = state.tile_populations
    cdef int[:] dist_pops = np.zeros(n_districts , dtype='i')
    cdef int ti
    for ti in range(state.n_tiles):
        dist_pops[districts[ti]] += tile_populations[ ti ]
    return dist_pops

cpdef int[:,:] district_voters(state, int[:] districts, int n_districts) except *:
    cdef int[:,:] tile_voters = state.tile_voters
    cdef int[:,:] dist_voters = np.zeros((n_districts, 2) , dtype='i')
    cdef int ti
    for ti in range(state.n_tiles):
        dist_voters[districts[ti], 0] += tile_voters[ti, 0]
        dist_voters[districts[ti], 1] += tile_voters[ti, 1]
    return dist_voters

cpdef bint is_frontier(int[:] partition, state, int ti) except *:
    cdef int tj
    cdef int di = partition[ti]
    for tj in state.tile_neighbors[ti]:
        if partition[tj] != di:
            return True
    return False

cpdef list district_boundry_points(state, int[:] districts, int n_districts):
    """ Helper functions for compactness metrics."""
    cdef list points = [ [] for _ in range(n_districts) ]
    cdef int ti, di, ti_n
    cdef float x0, y0, x1, y1
    cdef bint add_tile
    for ti in range(state.n_tiles):
        di = districts[ti]
        # x0, y0, x1, y1 = state.tile_bboxs[ti]
        add_tile = False
        for ti_n in state.tile_neighbors[ti]:
            if districts[ti_n] != di:
                add_tile = True
                break
        if add_tile or state.tile_boundaries[ti]:
            points[di].extend(state.tile_hulls[ti])
            # points[di].append((x0, y0))
            # points[di].append((x1, y1))
            # points[di].append((x0, y1))
            # points[di].append((x1, y0))
    return points

def make_random(state, n_districts):
    boundry_tiles = np.where(state.tile_boundaries)[0].tolist()
    seeds = random.sample(boundry_tiles, n_districts)
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
            for t_other in state.tile_neighbors[t]:
                if partition[t_other] != -1:
                    options.append(t_other)
            if len(options):
                t_other = random.choice(options)
                partition[t] = partition[t_other]
                n_empty -= 1

    return partition

# def make_random(state, n_districts):
    # boundry_tiles = np.where(state.tile_boundaries)[0].tolist()
    # seeds = random.sample(boundry_tiles, n_districts)
    # districts = np.full(state.n_tiles, -1, dtype='i')
    # n_assigned = 0
    # open_neighbors = [ set() for _ in range(n_districts) ]
    # d_populations  = [ state.tile_populations[idx] for idx in seeds ]
    # for d_idx, t_idx in enumerate(seeds):
    #     districts[ t_idx ] = d_idx
    #     n_assigned += 1
    #     for t_idx0 in state.tile_neighbors[t_idx]:
    #         if districts[t_idx0] == -1:
    #             open_neighbors[d_idx].add(t_idx0)
    # while n_assigned < state.n_tiles:
    #     # Select the smallest district that has open neighbors.
    #     d_idx = next(d for d in np.argsort(d_populations) if len(open_neighbors[d]) > 0)
    #     # Give it a random neighbor.
    #     t_idx = random.choice(list(open_neighbors[d_idx]))
    #     # print('giving %i to %i'%(t_idx, d_idx))
    #     districts[ t_idx ] = d_idx
    #     d_populations[ d_idx ] += state.tile_populations[ t_idx ]
    #     n_assigned += 1
    #     for on in open_neighbors:
    #         if t_idx in on:
    #             on.remove(t_idx)
    #     for t_idx0 in state.tile_neighbors[t_idx]:
    #         if districts[t_idx0] == -1:
    #             open_neighbors[d_idx].add(t_idx0)
    # assert districts.min() == 0
    # assert all(len(on) == 0 for n in open_neighbors)
    # return districts
