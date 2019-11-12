import random
from connectivity import can_lose, is_frontier
from constraints import count_pop

def mutate(partition, n_districts, map, m_rate, pop_min, pop_max):
    """ Mutate a partition.
    """
    d_pop = count_pop(map, partition, n_districts)
    front = set([ ti for ti in range(map.n_tiles) if is_frontier(partition, map, ti) ])

    edits = 0
    to_edit = int(m_rate * map.n_tiles)
    max_tries = 200

    for m_i in range(max_tries):
        #### Pick random tile to change district.
        t_i = random.choice(tuple(front))
        d_i = partition[t_i]

        ### See if removing will break population equality constraint.
        if d_pop[d_i] - map.tile_populations[t_i].sum() < pop_min:
            continue

        ### See if removing will break contiguity constraint.
        if not can_lose(partition, map, n_districts, t_i):
            continue

        options = []
        for t_other in map.tile_neighbours[t_i]:
            d_other = partition[t_other]
            if partition[t_other] == partition[t_i]:
                continue
            if d_pop[d_other] + map.tile_populations[t_i].sum() > pop_max:
                continue

            options.append(t_other)

        if len(options):
            t_other = random.choice(options)
            partition[t_i] = partition[t_other]

            for tk in map.tile_neighbours[t_i]:
                is_front = is_frontier(partition, map, tk)
                if is_front:
                    front.add(tk)
                elif tk in front:
                    front.remove(tk)

            edits += 1
            if edits == to_edit:
                break
    return
    # partition