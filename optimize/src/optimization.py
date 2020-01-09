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
    def __init__(self, state, n_districts, tolerance=.15):
        super().__init__()
        self.state = state
        self.n_districts = n_districts
        ideal_pop = state.population / n_districts
        self.pop_max = ideal_pop * (1 + tolerance)
        self.pop_min = ideal_pop * (1 - tolerance)

    def _do(self, problem, X, **kwargs):
        t = time.time()
        X = X.copy()
        for i in range(X.shape[0]):
            mutation_rate = random.gauss(0.01, 0.01)
            mutation.mutate(X[i], self.n_districts, self.state, mutation_rate, self.pop_min, self.pop_max)
        return X

class DistrictProblem(Problem):
    """ This class just calls the obtective functions.
    """
    def __init__(self, state, n_districts, n_iters, metrics, **kwargs):
        super().__init__(n_var=state.n_tiles, n_obj=len(metrics), type_var=np.integer, **kwargs)
        self.state = state
        self.n_districts = n_districts
        self.metrics = metrics
        self.hv = Hypervolume(ref_point=np.array([1]*len(metrics)))
        self.history = []
        self.pbar = tqdm(total=n_iters)

    def _evaluate(self, X, out, *args, **kwargs):
        t = time.time()
        out['F'] = np.array([
            [ f(self.state, p, self.n_districts) for f in self.metrics ]
            for p in X
        ])
        assert not np.isnan(out['F']).any()
        assert out['F'].min() >= 0
        assert out['F'].max() <= 1.0
        self.history.append(round(self.hv.calc(out['F']), 6))
        self.pbar.update(1)
        self.pbar.set_description("Hypervolume %s" % self.history[-1])
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


# def make_random(state, n_districts):

    # boundry_tiles = np.where(state.tile_boundaries)[0].tolist()
    # seeds = random.sample(boundry_tiles, n_districts)
    # districts = np.full(state.n_tiles, -1, dtype='i')
    # n_assigned = 0
    # open_neighbors = [ set() for _ in range(n_districts) ]
    # d_populations  = [ state.tile_populations[idx] for idx in seeds ]
    # for d_idx, t_idx in enumerate(seeds):
    #     districts[ t_idx ] = d_idx
    #     n_assigned += 1
    #     for t_idx0 in state.tile_neighbors[t_idx]:
    #         if districts[t_idx0] == -1:
    #             open_neighbors[d_idx].add(t_idx0)
    # while n_assigned < state.n_tiles:
    #     # Select the smallest district that has open neighbors.
    #     d_idx = next(d for d in np.argsort(d_populations) if len(open_neighbors[d]) > 0)
    #     # Give it a random neighbor.
    #     t_idx = random.choice(list(open_neighbors[d_idx]))
    #     # print('giving %i to %i'%(t_idx, d_idx))
    #     districts[ t_idx ] = d_idx
    #     d_populations[ d_idx ] += state.tile_populations[ t_idx ]
    #     n_assigned += 1
    #     for on in open_neighbors:
    #         if t_idx in on:
    #             on.remove(t_idx)
    #     for t_idx0 in state.tile_neighbors[t_idx]:
    #         if districts[t_idx0] == -1:
    #             open_neighbors[d_idx].add(t_idx0)
    # assert districts.min() == 0
    # assert all(len(on) == 0 for n in open_neighbors)
    # return districts

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
        print(state.n_tiles)

    states = states[::-1]
    mappings = mappings[::-1]
    thresholds = np.linspace(0.5, 0.1, num=len(states))
    print('Resolutions:', [ s.n_tiles for s in states ])
    print('Equality thresholds:', thresholds)

    ############################################################################
    """ Second, Create an initial population that has populaiton equality. """
    ############################################################################
    seeds = []
    state = states[0]
    print('Creating initial population.', config['pop_size'], config['n_districts'])
    with tqdm(total=config['pop_size']) as pbar:
        while len(seeds) < config['pop_size']:
            try:
                dists = districts.make_random(state, config['n_districts'])
                fix_pop_equality(
                    state, dists, config['n_districts'],
                    tolerance=thresholds[0],
                    max_iters=300
                )
                seeds.append(dists)
                pbar.update(1)
            except Exception as e:
                # print('FPE failed.', e)
                pass
    seeds = np.array(seeds)
    print('Created seeds')

    ############################################################################
    """ Run a optimization process for each resolution using the previups
        outputs as the seeds for the next.
    """
    ############################################################################
    for opt_i, (state, mapping, threshold) in enumerate(zip(states, mappings, thresholds)):
        print('Making novelty archive...')
        archive
        print('Optimizing', opt_i, state.n_tiles, threshold)
        used_metrics = { name: getattr(metrics, name) for name in config['metrics'] }

        for seed in seeds:
            fix_pop_equality(
                state, seed, config['n_districts'],
                tolerance=threshold,
                max_iters=500
            )

        algorithm = NSGA2(
            pop_size=config['pop_size'],
            sampling=seeds,
            crossover=DistrictCross(),
            mutation=DistrictMutation(state, config['n_districts'], .15),
        )
        problem = DistrictProblem(
            state,
            config['n_districts'],
            config['n_gens'],
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
