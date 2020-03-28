import os, random, time, json
import numpy as np
from functools import partial
try:
    get_ipython()
    from tqdm.notebook import tqdm
except:
    from tqdm import tqdm
from copy import copy
from pymoo.model.problem import Problem
from pymoo.model.mutation import Mutation
from pymoo.model.crossover import Crossover
from pymoo.performance_indicator.hv import Hypervolume
from pymoo.algorithms.nsga2 import NSGA2
from pymoo.algorithms.nsga3 import NSGA3
from src import districts, metrics, mutation, novelty
from src.state import State
from src.constraints import fix_pop_equality
from src.feasibleinfeasible import *
# from src.novelty import EdgesHistogramNoveltyArchive, CentersHistogramNoveltyArchive, MutualTilesNoveltyArchive

############################################################################
# Evolutionary Operators.
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
        X = X.copy()
        mutation_rate = 1.0 / self.state.n_tiles
        for i in range(X.shape[0]):
            mutation.mutate(X[i], self.n_districts, self.state, mutation_rate, self.pop_min, self.pop_max)
        return X

class DistrictProblem(Problem):
    """ This class just calls the objective functions.
    """
    def __init__( self, state, n_iters, config, used_metrics,
                  used_constraints=[], *args, **kwargs ):
        super().__init__(
            n_var=state.n_tiles,
            n_obj=len(used_metrics)+bool(config.novelty),
            n_constr=len(used_constraints),
            type_var=np.integer, *args, **kwargs
        )
        self.state = state
        self.n_districts = config.n_districts
        self.used_metrics = used_metrics
        self.used_constraints = used_constraints
        self.novelty = config.novelty
        if self.novelty:
            print('Making novelty archive...')
            arch = novelty.archives[self.novelty]
            self.archive = arch(state, self.n_districts, **config.nov_params)

    def _evaluate(self, districts, out, *args, **kwargs):
        state, n_districts, = self.state, self.n_districts
        out['F'] = np.array([
            [ f(state, d, n_districts) for f in self.used_metrics ]
            for d in districts
        ])
        if self.used_constraints:
            out['G'] = np.zeros((districts.shape[0], self.n_constr))
            for di, d in enumerate(districts):
                for ci, c in enumerate(self.used_constraints):
                    out['G'][di, ci] = c(state, d, n_districts, out['F'][di])
            print(out['G'].sum(axis=0))
        if self.novelty:
            novelty = self.archive.updateAndGetNovelty(districts)
            novelty = 1.0 - novelty
            out['F'] = np.append( out['F'], novelty[:, np.newaxis], axis=1 )
        assert not np.isnan(out['F']).any()
        assert out['F'].min() >= 0
        assert out['F'].max() <= 1.0

class DistrictProblemFI(FI_problem_mixin, DistrictProblem):
    pass

def minimize(problem, algorithm,termination=None,**kwargs):
    if termination is None:
        termination = None
    elif not isinstance(termination, Termination):
        if isinstance(termination, str):
            termination = get_termination(termination)
        else:
            termination = get_termination(*termination)
    algorithm.initialize(problem,termination=termination,**kwargs)
    res = algorithm.solve()
    res.algorithm = algorithm
    return res

################################################################################
# MISC Utilitites
################################################################################
def save_results(config, state, result, opt_i, hv_history):
    """ Save all the results and config to disk. """
    with open(os.path.join(config.out, 'config.json'), 'w') as f:
        json.dump(vars(config), f, indent=4)
    with open(os.path.join(config.out, 'state_%i.json'%opt_i), 'w') as f:
        json.dump(state.toJSON(), f)
    with open(os.path.join(config.out, 'hv_%i.txt'%opt_i), 'w') as f:
        for hv in hv_history:
            f.write("%f\n" % hv)
    with open(os.path.join(config.out, 'rundata_%i.json'%opt_i), 'w') as f:
        json.dump({
            "config": vars(config),
            'values': result.F.tolist(),
            'solutions': result.X.tolist(),
            'metrics_data': {
                'lost_votes': [
                    np.asarray(metrics.lost_votes(state, x, config.n_districts)).tolist()
                    for x in result.X
                ],
                'bounding_hulls': [
                    metrics.bounding_hulls(state, x, config.n_districts)
                    for x in result.X
                ]
            }
        }, f)

def plot_results(config, state, result, opt_i, hv_history):
    import matplotlib.pyplot as plt
    plt.plot(hv_history, label='Phase: %i'%opt_i)
    plt.xlabel('Generations')
    plt.ylabel('Hypervolume')
    plt.legend()
    plt.savefig(os.path.join(config.out, 'hv_history_%i.png'%opt_i))

def upscale(districts, mapping):
    """ Convert districts to the next phase. """
    upscaled = np.zeros((districts.shape[0], mapping.shape[0]), dtype='i')
    for i in range(districts.shape[0]):
        for j in range(mapping.shape[0]):
            upscaled[i, j] = districts[i, mapping[j]]
    return upscaled

def equality_constraint(state, district, n_districts, values, threshold):
    """ Return if it violates constraint """ 
    return metrics.equality(state, district, n_districts) > threshold

def value_constraint(state, district, n_districts, values, index, threshold):
    """ Return if it violates constraint """ 
    return values[index] > threshold

def opt_callback(algorithm, text, pbar, HV, hypervolume_mask):
    """ A logging function passed as the 'callback' to the algorithm """
    F = algorithm.pop.get("F")
    
    # Calculate novelty here so it can be doen for entire population.
    # if algorithm.problem.novelty:
    #     X = algorithm.pop.get('X')
    #     novelty = algorithm.problem.archive.updateAndGetNovelty(X)
    #     F[:, -1] = 1.0 - novelty
    #     # F[:, -1] *= F[:, 0] # Multiply novelty by compactness.
    #     algorithm.pop.set('F', F)
    #     # print(novelty.shape, novelty.min(), novelty.mean(), novelty.max())
    # print('opt_callback', F.shape, F.sum(axis=0))

    F_hv = F[:, hypervolume_mask]
    hv = round(HV.calc(F_hv), 5)
    algorithm.hv_history.append(hv)
    
    # TODO
    # pf_size = int(F.shape[0]) 
    # algorithm.pf_size_history.append(pf_size)
    
    pbar.update(1)
    pbar.set_description(f"{text}: {hv} {F.shape[0]}")

def feasible_seeds(state, config, max_iters=400):
    seeds = []
    n_failures = 0
    allowed_failures = 2*config.pop_size
    with tqdm(total=config.pop_size) as pbar:
        while len(seeds) < config.pop_size:
            try:
                rand_dist = districts.make_random(state, config.n_districts)
                if not config.dont_fix_seeds and config.equality_constraint > 0:
                    fix_pop_equality(
                        state, rand_dist, config.n_districts,
                        tolerance=config.equality_constraint,
                        max_iters=max_iters
                    )
                seeds.append(rand_dist)
                pbar.update(1)
            except Exception as e:
                n_failures += 1
                if n_failures == allowed_failures:
                    raise ValueError('Too many failures in fix_seeds')
    return seeds

def run_fi_optimization(ALG, state, metrics, constraints, seeds, config, n_gens, opt_i, feas_mask, infeas_mask):
    """ Run one optimziation phase with feasible-infeasible method. """
    # print(feas_mask, infeas_mask)
    pop_size = config.pop_size//2 # Half for each population.
    feas_algo = NSGA2_FI(
        pop_size=pop_size,
        sampling=seeds[:pop_size] if opt_i == 0 else seeds,
        mutation=DistrictMutation(state, config.n_districts, config.equality_constraint),
        crossover=DistrictCross(),
        callback=partial(
            opt_callback,
            text='  Feas HV',
            HV=Hypervolume(ref_point=np.ones(sum(feas_mask))),
            pbar=tqdm(total=n_gens, position=0),
            hypervolume_mask=np.ones(sum(feas_mask), dtype='bool') # This gets only 1's because mask is already applied in FI alg.
        )
    )
    feas_algo.hv_history = []
    feas_algo.pf_size_history = []
    infeas_algo = NSGA2_FI(
        pop_size=pop_size,
        sampling=seeds[pop_size:] if opt_i == 0 else seeds,
        crossover=DistrictCross(),
        mutation=DistrictMutation(state, config.n_districts, 1.0),
        selection=TournamentSelection(func_comp=cv_agnostic_binary_tournament),
        callback=partial(
            opt_callback,
            text='InFeas HV',
            HV=Hypervolume(ref_point=np.ones(sum(infeas_mask))),
            pbar=tqdm(total=n_gens, position=1),
            hypervolume_mask=np.ones(sum(infeas_mask), dtype='bool') # This gets only 1's because mask is already applied in FI alg.
        )
    )
    problem = DistrictProblemFI(
        state, n_gens, config,
        used_metrics=metrics,
        used_constraints=constraints
    )
    result = FI_minimize(
        problem, feas_algo, infeas_algo, ('n_gen', n_gens),
        feas_mask=feas_mask,
        infeas_mask=infeas_mask,
        verbose=False,
        seed=0
    )
    # print('final', result.F.sum(axis=0))
    return result, feas_algo.hv_history#, feas_algo.pf_size_history

def run_optimization(ALG, state, metrics, constraints, seeds, config, n_gens, opt_i):
    mask = [ True ] * len(metrics) + ([ False ] if config.novelty else [])
    print('Run optimization', len(seeds))
    algorithm = ALG(
        pop_size=config.pop_size,
        sampling=seeds,
        crossover=DistrictCross(),
        mutation=DistrictMutation(state, config.n_districts, config.equality_constraint),
        callback=partial(
            opt_callback,
            text='HV', 
            HV=Hypervolume(ref_point=np.ones(sum(mask))),
            pbar=tqdm(total=n_gens),
            hypervolume_mask=mask
        ),
    )
    algorithm.hv_history = []
    algorithm.pf_size_history = []
    problem = DistrictProblem(
        state, n_gens, config,
        used_metrics=metrics,
        used_constraints=constraints
    )
    result = minimize(
        problem, algorithm, ('n_gen', n_gens),
        seed=0, verbose=False, save_history=False
    )
    # print(algorithm.pop.get('X').shape)
    #result.F = result.F[:, mask]
    # result.X = algorithm.pop.get('X')
    # result.F = algorithm.pop.get('F')
    # print('Finished optimization', result.F.shape)
    return result, algorithm.hv_history#, algorithm.pf_size_history
