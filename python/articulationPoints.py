from collections import defaultdict

def articulationPoints(partition, district_idx):
    time = 0
    tiles = [ i for i, v in enumerate(partition.tile_districts) if v == district_idx ]

    '''A recursive function that find aprticulation points
    using DFS traversal
    u --> The vertex to be visited next
    visited[] --> keeps tract of visited vertices
    disc[] --> Stores discovery times of visited vertices
    parent[] --> Stores parent vertices in DFS tree
    ap[] --> Store articulation points'''
    def APUtil( u, visited, ap, parent, low, disc):
        nonlocal time
        #Count of children in current node
        children = 0

        # Mark the current node as visited and print it
        visited[ u ] = True

        # Initialize discovery time and low value
        disc[u] = time
        low[u] = time
        time += 1

        # Recur for all the vertices adjacent to this vertex
        for v in partition.sameDistrictNeighbours(u):
            # If v is not visited yet, then make it a child of u
            # in DFS tree and recur for it
            if visited[v] == False:
                parent[v] = u
                children += 1
                APUtil(v, visited, ap, parent, low, disc)

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

    visited = { t: False for t in tiles }
    disc = { t: float("Inf") for t in tiles }
    low = { t: float("Inf") for t in tiles }
    parent = { t: -1 for t in tiles }
    ap = { t: False for t in tiles } # To store articulation points.

    # Call the recursive helper function
    # to find articulation points
    # in DFS tree rooted with vertex 'i'
    for t in tiles:
        if not visited[ t ]:
            APUtil(t, visited, ap, parent, low, disc)

    return [ t for t, is_ap in ap.items() if is_ap ]
