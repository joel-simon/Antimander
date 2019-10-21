import sys, os, json, random
import numpy as np
from pymoo.algorithms.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.visualization.scatter import Scatter
from pymoo.factory import get_problem, get_sampling, get_crossover, get_mutation
import matplotlib.pyplot as plt

from pymoo.model.crossover import Crossover
from pymoo.model.mutation import Mutation
from pymoo.model.problem import Problem

from pymoo.operators.crossover.util import crossover_mask

from map import Map
from partition import Partition
from pymoo.util.misc import stack

pop_size = 200
n_tiles = 100
m = Map.makeRandom(n_tiles, seed=0)
n_districts = 5

class PartitionCross(Crossover):
    def __init__(self, **kwargs):
        super().__init__(n_parents=2, n_offsprings=2, **kwargs)
    def _do(self, problem, X, **kwargs):
        return X.copy()

class PartitionMutation(Mutation):
    def __init__(self):
        super().__init__()

    def _do(self, problem, X, **kwargs):
        partitions = [ Partition.fromDistrictsArray(m, n_districts, x) for x in X ]
        for p in partitions:
            for _ in range(random.randint(0, 10)):
                p.mutate()
        return np.array([ p.tile_districts for p in partitions ])

class DistrictProblem(Problem):
    def __init__(self, **kwargs):
        super().__init__(n_var=n_tiles, n_obj=2, type_var=np.integer, **kwargs)

    def _calc_pareto_front(self, n_pareto_points=100):
        x = np.linspace(0, 1, n_pareto_points)
        return np.array([x, 1 - x]).T

    def _evaluate(self, X, out, *args, **kwargs):
        partitions = [ Partition.fromDistrictsArray(m, n_districts, x) for x in X ]
        F = np.array([p.evaluate() for p in partitions])
        out['F'] = F


seeds = [ Partition.makeRandom(n_districts, m) for _ in range(pop_size) ]
seeds = np.array([ p.tile_districts for p in seeds ])

algorithm = NSGA2(
    pop_size=pop_size,
    sampling=seeds,
    crossover=PartitionCross(),
    mutation=PartitionMutation()
)

problem = DistrictProblem()

res = minimize(
    problem,
    algorithm,
    ('n_gen', 400),
    seed=1,
    verbose=True,
    save_history=True
)

with open('out/rundata.json', 'w') as f:
    json.dump({
        'n_districts': n_districts,
        'nsga_config': {},
        'map': m.toJSON(),
        'values': res.F.tolist(),
        'solutions': res.X.tolist()
    }, f)

plt.scatter(res.F[:, 0], res.F[:, 1])
plt.savefig('out/pareto_front.png')
# plt.show()

from pymoo.performance_indicator.hv import Hypervolume
metric = Hypervolume(ref_point=np.array([2.0, 2.0]))
pop_each_gen = [a.pop for a in res.history]

obj_and_feasible_each_gen = [pop[pop.get("feasible")[:,0]].get("F") for pop in pop_each_gen]
hv = [ metric.calc(f) for f in obj_and_feasible_each_gen ]

plt.plot(np.arange(len(hv)), hv, '-o')
plt.title("Convergence")
plt.xlabel("Generation")
plt.ylabel("Hypervolume")
plt.savefig('out/convergence.png')
# plt.show()
