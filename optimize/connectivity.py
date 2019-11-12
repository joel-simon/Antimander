def dfs(partition, graph, visited, t_i):
    if visited[t_i]:
        return
    visited[t_i] = True
    for t_j in graph[t_i]:
        if partition[t_j] == partition[t_i]:
            dfs(partition, graph, visited, t_j)

def can_lose(partition, map, n_districts, t_i):
    d_i = partition[t_i]
    vis = { t_j: False for t_j in map.tile_neighbours[t_i] if partition[t_j] == d_i}
    fist_key = next(iter(vis.keys()))
    dfs(partition, map.neighbour_graph[t_i], vis, fist_key)
    return all(vis.values())
