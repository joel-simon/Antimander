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
# from pymoo.util.misc import stack

class MyCross(Crossover):
    def __init__(self, prob_uniform, **kwargs):
        super().__init__(n_parents=2, n_offsprings=2, **kwargs)
        self.prob_uniform = prob_uniform

    def _do(self, problem, X, **kwargs):
        _, n_matings, n_var = X.shape
        # random matrix to do the crossover
        M = np.random.random((n_matings, n_var)) < self.prob_uniform
        _X = crossover_mask(X, M)
        return _X


class MyMut(Mutation):
    def __init__(self, prob=None):
        super().__init__()
        self.prob = prob
    def _do(self, problem, X, **kwargs):
        return X + np.random.randn(*X.shape) * 0.5


class MyProblem(Problem):
    def __init__(self, n_var=1, **kwargs):
        super().__init__(n_var=n_var, n_obj=1, n_constr=0, xl=-10, xu=10, type_var=np.double, **kwargs)

    def _calc_pareto_front(self, n_pareto_points=100):
        x = np.linspace(0, 1, n_pareto_points)
        return np.array([x, 1 - x]).T

    def _evaluate(self, x, out, *args, **kwargs):
        f1 = x[:, 0]**2
        f2 = (x[:, 0]-2)**2
        # print(np.column_stack([ f1, f2 ]).shape)
        out["F"] = np.column_stack([ f1, f2 ])

problem = MyProblem()
algorithm = NSGA2(
    pop_size=50,
    sampling= np.random.rand(100, 1),
    crossover = MyCross(0.5),
    mutation = MyMut()
)
res = minimize(
    problem,
    algorithm,
    ('n_gen', 20),
    seed=1,
    verbose=True,
    save_history=True
)


# print(pf)
# plt.scatter(res.F[:, 0], res.F[:, 1])
# plt.show()

from pymoo.performance_indicator.hv import Hypervolume
metric = Hypervolume(ref_point=np.array([4.0, 4.0]))
pop_each_gen = [a.pop for a in res.history]

obj_and_feasible_each_gen = [pop[pop.get("feasible")[:,0]].get("F") for pop in pop_each_gen]
hv = [metric.calc(f) for f in obj_and_feasible_each_gen]

plt.plot(np.arange(len(hv)), hv, '-o')
plt.title("Convergence")
plt.xlabel("Generation")
plt.ylabel("Hypervolume")
plt.show()
