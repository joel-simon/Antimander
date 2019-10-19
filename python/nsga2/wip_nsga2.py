import numpy as np
import math, random
from typing import Dict, List

def sort_by_values(array, values):
    return array.sort(key=lambda a: values[a])

def sort_by_other(array, other):
    """
    """
    return [ b for a, b in sorted(zip(other, array)) ]


def dominates(p, q, values, maximize=True):
    """ returns 1 if p dominates q and -1 if q dominates p.
        0 if neither dominates the other.
    """
    n_objectives = len(values[0])
    dominate_p = False
    dominate_q = False
    for i in range(n_objectives):
        v_p = values[p, i]
        v_q = values[q, i]
        if not maximize:
            v_p *= -1
            v_q *= -1

        if v_p > v_q:
            dominate_p = True
        elif v_p < v_q:
            dominate_q = True

    if dominate_p == dominate_q:
        # Both have the same values.
        return 0
    elif dominate_p:
        return 1
    else:
        return -1

def non_dominated_sort(values, maximize):
    """ Function to carry out NSGA-II's fast non dominated sort """
    n_individual, n_objectives = values.shape
    dominated_by = [[] for _ in range(n_individual)]
    front = [[]]
    domination_count = np.zeros(n_individual, dtype='i')
    rank = np.zeros(n_individual, dtype='i')

    for p in range(n_individual):
        for q in range(n_individual):
            domination = dominates(p, q, values, maximize)
            if domination == 1:
                dominated_by[p].append(q)
            elif (domination == -1):
                domination_count[p] += 1
        if domination_count[p] == 0:
            rank[p] = 0
            front[0].append(p)

    i = 0
    while front[i]:
        Q = []
        for p in front[i]:
            for q in dominated_by[p]:
                domination_count[q] -= 1
                if domination_count[q] == 0:
                    rank[q] = i + 1
                    if q not in Q:
                        Q.append(q)
        i += 1
        front.append(Q)

    return front[:-1]

def crowding_distance(values, front):
    n_individual, n_objectives = values.shape
    distance = np.zeros(len(front))
    distance[0] = 99999999999999
    distance[len(front) - 1] = 99999999999999
    for i in range(n_objectives):
        v = [values[j][i] for j in range(n_individual)]
        sort_by_values(front, v)
        dv = max(v) - min(v)
        for k in range(1, len(front)-1):
            distance[k] += (v[front[k+1]] - v[front[k-1]]) / dv
    return distance


def run(config, seed, crossover, mutate, evaluate, notification, copy ):
    # Create an initial population.
    solution = [ seed() for _ in range(config['pop_size']) ]
    values1 = evaluate(solution)
    assert values1.shape == (config['pop_size'], config['n_objectives'])

    for gen_no in range(config['max_gen']):
        fronts1 = non_dominated_sort(values1, config['maximize'])

        if notification:
            notification(
                gen_no,
                [solution[i] for i in fronts1[0]],
                [values1[i] for i in fronts1[0]]
            )

        solution2 = [ copy(s) for s in solution ]

        # Generating offsprings
        while len(solution2) < 2*config['pop_size']:
            if random.random() < config['crossover']:
                # Crossover someone from pareto front with a random.
                a1 = random.choice( fronts1[0] )
                b1 = random.randint(0, config['pop_size'] - 1)
                child = crossover(solution2[a1], solution2[b1])
                if random.random() < config['mutation']:
                    mutate(child)
                solution2.append(child)
            else:
                idx = random.choice(fronts1[0])
                child = mutate(copy(solution2[idx]))
                solution2.append(child)

        assert len(solution2) == 2*config['pop_size']

        values2 = evaluate(solution2)

        assert values2.shape == (2*config['pop_size'], config['n_objectives'])

        fronts2 = non_dominated_sort(values2, config['maximize'])
        new_solution = []

        for i in range(len(fronts2)):
            if (len(new_solution) + len(fronts2[i]) <= config['pop_size']):
                new_solution += fronts2[i]
            else:
                crowding = crowding_distance(values2, fronts2[i])
                # print(fronts2[i], crowding, values2.shape)
                # print(crowding, values2.shape)
                # fronts2.
                # fronts2[i].sort()
                n_needed = config['pop_size'] - len(new_solution)
                new_solution += sort_by_other(fronts2[i], crowding)[:n_needed]
                break

        assert len(new_solution) == config['pop_size'], ('wrong size', [len(new_solution), config['pop_size']])
        solution = np.array([ solution2[i] for i in new_solution ])
        values1 = np.array([ values2[i] for i in new_solution ])

    return solution
