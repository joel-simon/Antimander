cpdef int[:] district_populations(state, int[:] partition, int n_districts) except *
cpdef int[:, :] district_voters(state, int[:] partition, int n_districts) except *
cpdef bint is_frontier(int[:] partition, state, int ti) except *
