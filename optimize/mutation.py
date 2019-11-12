import random
from connectivity import can_lose, is_frontier
from constraints import count_pop

def mutate(districts, n_districts, state, m_rate, pop_min, pop_max):
    """ Mutate a partition.
    """
    d_pop = count_pop(state, districts, n_districts)
    front = set([ ti for ti in range(state.n_tiles) if is_frontier(districts, state, ti) ])

    edits = 0
    to_edit = int(m_rate * state.n_tiles)
    max_tries = 200

    for m_i in range(max_tries):
        #### Pick random tile to change district.
        t_i = random.choice(tuple(front))
        d_i = districts[t_i]

        ### See if removing will break population equality constraint.
        if d_pop[d_i] - state.tile_populations[t_i].sum() < pop_min:
            continue

        ### See if removing will break contiguity constraint.
        if not can_lose(districts, state, n_districts, t_i):
            continue

        options = []
        for t_other in state.tile_neighbours[t_i]:
            d_other = districts[t_other]
            if districts[t_other] == districts[t_i]:
                continue
            if d_pop[d_other] + state.tile_populations[t_i].sum() > pop_max:
                continue

            options.append(t_other)

        if len(options):
            t_other = random.choice(options)
            districts[t_i] = districts[t_other]

            for tk in state.tile_neighbours[t_i]:
                is_front = is_frontier(districts, state, tk)
                if is_front:
                    front.add(tk)
                elif tk in front:
                    front.remove(tk)

            edits += 1
            if edits == to_edit:
                break
    return
    # districts