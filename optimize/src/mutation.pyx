# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
import random
from src.connectivity import can_lose
from src.districts cimport district_populations, is_frontier

cpdef void mutate(
    int[:] districts,
    int n_districts,
    state,
    float m_rate,
    int pop_min,
    int pop_max
) except *:
    """ Mutate a partition.
    """
    cdef int edits = 0
    cdef int to_edit = max(1, int(m_rate * state.n_tiles))
    cdef int max_tries = 200
    cdef int ti, tk, di, t_other, d_other
    cdef list options
    cdef bint is_front
    cdef int[:] d_pop = district_populations(state, districts, n_districts)
    cdef set front = set([ ti for ti in range(state.n_tiles) if is_frontier(districts, state, ti) ])
    cdef int[:] tile_populations = state.tile_populations

    for _ in range(max_tries):
        ### Pick random tile to change district. ###
        ti = random.choice(tuple(front))
        di = districts[ti]

        ### See if removing will break population equality constraint. ###
        if d_pop[di] - tile_populations[ti] < pop_min:
            continue

        ### See if removing will break contiguity constraint. ###
        if not can_lose(districts, state, n_districts, ti):
            continue

        options = []
        for t_other in state.tile_neighbors[ti]:
            d_other = districts[t_other]
            if districts[t_other] == districts[ti]:
                continue
            if d_pop[d_other] + tile_populations[ti] > pop_max:
                continue

            options.append(t_other)

        if len(options):
            t_other = random.choice(options)
            districts[ti] = districts[t_other]

            for tk in state.tile_neighbors[ti]:
                is_front = is_frontier(districts, state, tk)
                if is_front:
                    front.add(tk)
                elif tk in front:
                    front.remove(tk)

            edits += 1
            if edits == to_edit:
                break
    return
