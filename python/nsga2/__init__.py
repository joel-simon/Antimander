import math
import random
from nsga2.utils import *

def run(config, seed, crossover, evaluate, notification, copy ):
    pop_size = config['pop_size']
    solution = [ seed() for _ in range(pop_size) ]

    for gen_no in range(config['max_gen']):
        values1 = evaluate(solution)
        ndss = fast_non_dominated_sort(values1)

        if notification:
            notification(gen_no, [solution[i] for i in ndss[0]], [values1[i] for i in ndss[0]])
        if gen_no == config['max_gen']-1:
            return [solution[i] for i in ndss[0]], [values1[i] for i in ndss[0]]

        solution2 = solution[:]

        # Generating offsprings
        while len(solution2) < 2*pop_size:
            a1 = random.randint(0, pop_size-1)
            b1 = random.randint(0, pop_size-1)
            [ child1, child2 ] = crossover(solution[a1], solution[b1])
            assert child1, (child1, solution[a1], solution[b1])
            assert child2, (child2, solution[a1], solution[b1])
            solution2.append(child1)
            if len(solution2) < 2 * pop_size:
                solution2.append(child2)

        values2 = evaluate(solution2)
        ndss2 = fast_non_dominated_sort(values2)

        # print(sorted(solution2[v] for v in ndss2[0]))
        # for valuez in ndss2[0]:
        #     print(round(solution[valuez], 3), end=" ")
        # exit()

        crowding_distance_values2 = []
        for front in ndss2:
            crowding_distance_values2.append(crowding_distance(values2, front[:]))
        new_solution = []
        for i in range(len(ndss2)):
            ndss2_1 = [index_of(ndss2[i][j],ndss2[i] ) for j in range(0,len(ndss2[i]))]
            front22 = sort_by_values(ndss2_1[:], crowding_distance_values2[i][:])
            front = [ndss2[i][front22[j]] for j in range(0, len(ndss2[i]))]
            front.reverse()
            for value in front:
                new_solution.append(value)
                if(len(new_solution)==pop_size):
                    break
            if (len(new_solution) == pop_size):
                break
        solution = [ solution2[i] for i in new_solution ]
        # print(len(new_solution))
        # notification(gen_no, solution, )

    return solution, np.array([values2[i] for i in new_solution])