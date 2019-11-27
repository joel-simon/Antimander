import os, random, time, json
import numpy as np
from tqdm import tqdm
from pymoo.model.problem import Problem
from pymoo.model.mutation import Mutation
from pymoo.model.crossover import Crossover
from pymoo.performance_indicator.hv import Hypervolume
from pymoo.algorithms.nsga2 import NSGA2
from pymoo.optimize import minimize

from src import districts, metrics, mutation
from src.state import State
from src.constraints import fix_pop_equality

all_metrics = {
    "compactness": metrics.compactness,
    "competitiveness": metrics.competitiveness,
    "efficiency_gap": metrics.efficiency_gap
}

############################################################################
#
############################################################################

class DistrictCross(Crossover):
    """ The crossover operator does nothing.
    """
    def __init__(self, **kwargs):
        super().__init__(n_parents=2, n_offsprings=2, **kwargs)
    def _do(self, problem, X, **kwargs):
        return X.copy()

class DistrictMutation(Mutation):
    """ Mutate the districts while preserving the population equality.
    """
    def __init__(self, state, n_districts):
        super().__init__()
        self.state = state
        self.n_districts = n_districts
        total_pop = state.tile_populations.sum()
        ideal_pop = total_pop / n_districts
        self.pop_max = ideal_pop * (1+.1)
        self.pop_min = ideal_pop * (1-.1)

    def _do(self, problem, X, **kwargs):
        t = time.time()
        X = X.copy()
        for i in range(X.shape[0]):
            mutation_rate = random.gauss(0.01, .01)
            mutation.mutate(X[i], self.n_districts, self.state, mutation_rate, self.pop_min, self.pop_max)
        return X

class DistrictProblem(Problem):
    """ This class just calls the obtective functions.
    """
    def __init__(self, state, n_districts, metrics, **kwargs):
        super().__init__(n_var=state.n_tiles, n_obj=len(metrics), type_var=np.integer, **kwargs)
        self.state = state
        self.n_districts = n_districts
        self.metrics = metrics
        self.hv = Hypervolume(ref_point=np.array([1]*len(metrics)))
        self.history = []

    def _evaluate(self, X, out, *args, **kwargs):
        t = time.time()
        out['F'] = np.array([
            [ f(self.state, p, self.n_districts) for f in self.metrics ]
            for p in X
        ])
        self.history.append(round(self.hv.calc(out['F']), 6))
        print('Hypervolume', self.history[-1])

############################################################################

def save_results(outdir, config, state, result, opt_i):
    path_out = os.path.join(outdir, 'rundata_%i.json'%opt_i)
    with open(path_out, 'w') as f:
        json.dump({
            "config": config,
            'state': state.toJSON(),
            'values': result.F.tolist(),
            'solutions': result.X.tolist(),
            'metrics_data': {
                'lost_votes': [
                    np.asarray(metrics.lost_votes(state, x, config['n_districts'])).tolist()
                    for x in result.X
                ]
            }
        }, f)

def upscale(districts, mapping):
    upscaled = np.zeros((districts.shape[0], mapping.shape[0]), dtype='i')
    for i in range(districts.shape[0]):
        for j in range(mapping.shape[0]):
            upscaled[i, j] = districts[i, mapping[j]]
    return upscaled

def optimize(config, _state, outdir):
    ############################################################################
    """ The core of the code. First, contract the state graph. """
    ############################################################################
    print('Subdividing state')
    states = [ _state ]
    mappings = [ None ]

    while states[-1].n_tiles > config['max_start_tiles']:
        state, mapping = states[-1].contract()
        states.append(state)
        mappings.append(mapping)

    states = states[::-1]
    mappings = mappings[::-1]
    print('Resolutions:', [s.n_tiles for s in states])

    ############################################################################
    """ Second, Create an initial population that has populaiton equality. """
    ############################################################################
    seeds = []
    state = states[0]
    print('Creating initial population.', config['pop_size'], config['n_districts'])
    with tqdm(total=config['pop_size']) as pbar:
        while len(seeds) < config['pop_size']:
            try:
                p = districts.make_random(state, config['n_districts'])
                fix_pop_equality(
                    state, p, config['n_districts'],
                    tolerance=.20,
                    max_iters=100
                )
                seeds.append(p)
                pbar.update(1)
            except Exception as e:
                pass
    seeds = np.array(seeds)
    print('Created seeds')

    ############################################################################
    """ Run a optimization process for each resolution using the previups
        outputs as the seeds for the next.
    """

    ############################################################################
    for opt_i, (state, mapping) in enumerate(zip(states, mappings)):
        used_metrics = { name: all_metrics[name] for name in config['metrics'] }
        algorithm = NSGA2(
            pop_size=config['pop_size'],
            sampling=seeds,
            crossover=DistrictCross(),
            mutation=DistrictMutation(state, config['n_districts']),
        )
        problem = DistrictProblem(
            state,
            config['n_districts'],
            used_metrics.values()
        )
        result = minimize(
            problem,
            algorithm,
            ('n_gen', config['n_gens']),
            seed=0,
            verbose=False,
            save_history=False
        )
        save_results(outdir, config, state, result, opt_i)
        if mapping is not None:
            seeds = upscale(result.X, mapping)
