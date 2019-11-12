# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True

cimport numpy as np
import numpy as np

cdef APUtil(
    int *time,
    int[:] tile_districts,
    map,
    int u,
    int[:] visited,
    int[:] ap,
    int[:] parent,
    double[:] low,
    double[:] disc
):
    cdef int v
    # Count of children in current node
    cdef int children = 0

    # Mark the current node as visited and print it
    visited[ u ] = True

    # Initialize discovery time and low value
    disc[u] = time[0]
    low[u] = time[0]
    time[0] += 1

    cdef list neighbors = map.tile_neighbours[u]
    for v in neighbors:
        # Dont count connections between tiles of differnet districts.
        if (tile_districts[u] != tile_districts[v]):
            continue
        # If v is not visited yet, then make it a child of u
        # in DFS tree and recur for it
        if visited[v] == False:
            parent[v] = u
            children += 1
            APUtil(time, tile_districts, map, v, visited, ap, parent, low, disc)

            # Check if the subtree rooted with v has a connection to
            # one of the ancestors of u
            low[u] = min(low[u], low[v])

            # u is an articulation point in following cases
            # (1) u is root of DFS tree and has two or more chilren.
            if parent[u] == -1 and children > 1:
                ap[u] = True

            #(2) If u is not root and low value of one of its child is more
            # than discovery value of u.
            if parent[u] != -1 and low[v] >= disc[u]:
                ap[u] = True

        # Update low value of u for parent function calls
        elif v != parent[u]:
            low[u] = min(low[u], disc[v])

cpdef int[:] articulationPoints(int[:] tile_districts, map) except *:
    cdef int time = 0
    cdef int n, t
    n = map.n_tiles
    cdef int[:] visited = np.zeros(n, dtype='i')
    cdef int[:] parent = np.full(n, -1.0, dtype='i')
    cdef int[:] ap = np.zeros(n, dtype='i')
    cdef double[:] low = np.full(n, np.inf)
    cdef double[:] disc = np.full(n, np.inf)

    for t in range(n):
        if not visited[t]:
            APUtil(&time, tile_districts, map, t, visited, ap, parent, low, disc)

    return ap

# cpdef int[:] articulationPoints(
#     int[:] tile_districts,
#     map,
#     cdef int[:] visited,
#     cdef int[:] parent,
#     cdef int[:] ap,
#     cdef double[:] low,
#     cdef double[:] disc
# ) except *:
#     cdef int time = 0
#     cdef int n, t
#     n = map.n_tiles

#     visited.fill(0)
#     parent.fill(-1)
#     ap.fill(0)
#     low.fill(np.inf)
#     disc.fill(np.inf)
#     cdef int[:] parent = np.full(n, -1.0, dtype='i')
#     cdef int[:] ap = np.zeros(n, dtype='i')
#     cdef double[:] low = np.full(n, np.inf)
#     cdef double[:] disc = np.full(n, np.inf)

#     for t in range(n):
#         if not visited[t]:
#             APUtil(&time, tile_districts, map, t, visited, ap, parent, low, disc)

#     return ap

