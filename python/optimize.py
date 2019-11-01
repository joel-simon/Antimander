import sys, os, json, random, argparse
import numpy as np
import matplotlib.pyplot as plt

from pymoo.algorithms.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.factory import get_problem, get_sampling, get_crossover, get_mutation
from pymoo.model.crossover import Crossover
from pymoo.model.mutation import Mutation
from pymoo.model.problem import Problem
from pymoo.operators.crossover.util import crossover_mask
from pymoo.performance_indicator.hv import Hypervolume

from map import Map
from partition import Partition
from metrics import efficiency_gap, equality, compactness_district_centers as compactness
from constraints import fix_pop_equality

metric = Hypervolume(ref_point=np.array([2.0, 2.0]))

class PartitionCross(Crossover):
    def __init__(self, **kwargs):
        super().__init__(n_parents=2, n_offsprings=2, **kwargs)
    def _do(self, problem, X, **kwargs):
        return X.copy()

class PartitionMutation(Mutation):
    def __init__(self, map, n_districts):
        super().__init__()
        self.map = map
        self.n_districts = n_districts

    def _do(self, problem, X, **kwargs):
        partitions = [
            Partition.fromDistrictsArray(self.map, self.n_districts, x)
            for x in X
        ]
        for i in range(len(partitions)):
            p_orig = partitions[i].copy()
            if random.random() < 0.2:
                partitions[i] = Partition.makeRandom(self.n_districts, self.map)
            for _ in range(random.randint(0, 10)):
                partitions[i].mutate()

            try:
                fix_pop_equality(self.map, partitions[i])
            except ValueError as e:
                partitions[i] = p_orig

        return np.array([ p.tile_districts for p in partitions ])

class DistrictProblem(Problem):
    def __init__(self, map, n_districts, **kwargs):
        super().__init__(n_var=map.n_tiles, n_obj=2, type_var=np.integer, **kwargs)
        self.map = map
        self.n_districts = n_districts

    # def _calc_pareto_front(self, n_pareto_points=100):
    #     x = np.linspace(0, 1, n_pareto_points)
    #     return np.array([x, x, x]).T
        # return np.array([0, 0, 0])

    def _evaluate(self, X, out, *args, **kwargs):
        partitions = [
            Partition.fromDistrictsArray(self.map, self.n_districts, x)
            for x in X
        ]
        out['F'] = np.array([
            [ f(self.map, p) for f in (compactness, efficiency_gap) ]
            for p in partitions
        ])
        print(metric.calc(out['F']))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-d', '--n_districts', default=5, type=int)
    parser.add_argument('-t', '--n_tiles', default=100, type=int)
    parser.add_argument('-p', '--pop_size', default=100, type=int)
    parser.add_argument('-g', '--n_gens', default=100, type=int)
    parser.add_argument('-o', '--out', required=True)
    args = parser.parse_args()

    m = Map.makeRandom(args.n_tiles, seed=0)

    seeds = [
        Partition.makeRandom(args.n_districts, m)
        for _ in range(args.pop_size)
    ]
    for p in seeds:
        fix_pop_equality(m, p, tolerance=.20, max_iters=600)
    seeds = np.array([ p.tile_districts for p in seeds ])

    algorithm = NSGA2(
        pop_size=args.pop_size,
        sampling=seeds,
        crossover=PartitionCross(),
        mutation=PartitionMutation(m, args.n_districts),
    )
    algorithm.func_display_attrs = None

    problem = DistrictProblem(m, args.n_districts)

    res = minimize(
        problem,
        algorithm,
        ('n_gen', args.n_gens),
        seed=1,
        verbose=True,
        save_history=True
    )

    with open(os.path.join(args.out, 'rundata.json'), 'w') as f:
        json.dump({
            'n_districts': args.n_districts,
            'nsga_config': {},
            'map': m.toJSON(),
            'values': res.F.tolist(),
            'solutions': res.X.tolist()
        }, f)

    plt.scatter(res.F[:, 0], res.F[:, 1])
    plt.savefig(os.path.join(args.out, 'pareto_front.png'))

    pop_each_gen = [ a.pop for a in res.history[1:] ]
    obj_and_feasible_each_gen = [pop[pop.get("feasible")[:,0]].get("F") for pop in pop_each_gen]
    hv = [ metric.calc(f) for f in obj_and_feasible_each_gen ]

    plt.plot(np.arange(len(hv)), hv, '-o')
    plt.title("Convergence")
    plt.xlabel("Generation")
    plt.ylabel("Hypervolume")
    plt.savefig(os.path.join(args.out, 'convergence.png'))
