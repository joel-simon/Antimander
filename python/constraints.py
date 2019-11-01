import numpy as np

def _count_pop(map, partition):
    d_pop = np.zeros(partition.n_districts , dtype='i')

    for t_i in range(map.n_tiles):
        d_i = partition.tile_districts[t_i]
        d_pop[d_i] += map.tile_populations[t_i].sum()

    return d_pop

def pop_equality(map, partition, tolerance=.15):
    total_pop = map.tile_populations.sum()
    ideal_pop = total_pop / partition.n_districts
    d_pop = np.zeros(partition.n_districts , dtype='i')

    for t_i in range(map.n_tiles):
        d_i = partition.tile_districts[t_i]
        d_pop[d_i] += map.tile_populations[t_i].sum()

    if d_pop.max() > ideal_pop * (1+tolerance):
        return False
    elif d_pop.min() < ideal_pop * (1-tolerance):
        d_pop.max() > ideal_pop * 1+tolerance

    return True

def fix_pop_equality(map, partition, tolerance=.20, max_iters=200):
    assert 0 < tolerance < 1.0
    total_pop = map.tile_populations.sum()
    ideal_pop = total_pop / partition.n_districts

    for i in range(max_iters):
        changes_needed = False
        d_pop = _count_pop(map, partition)

        for d_i in range(partition.n_districts):
            if d_pop[d_i] > ideal_pop * (1+tolerance):
                partition.removeTileRandom(d_i)
                changes_needed = True
            elif d_pop[d_i] < ideal_pop * (1-tolerance):
                partition.addTileRandom(d_i)
                changes_needed = True

        if not changes_needed:
            return True

    raise ValueError('Failed to fix pop_equality')



