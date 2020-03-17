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
from src import districts, metrics, mutation
from src.state import State
from src.constraints import fix_pop_equality
from src.novelty import DistrictHistogramNoveltyArchive as NoveltyArchive
from src.feasibleinfeasible import *

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
        t = time.time()
        X = X.copy()
        mutation_rate = 1.0 / self.state.n_tiles
        for i in range(X.shape[0]):
            mutation.mutate(X[i], self.n_districts, self.state, mutation_rate, self.pop_min, self.pop_max)
        return X

class DistrictProblem(Problem):
    """ This class just calls the objective functions.
    """
    def __init__( self, state, n_districts, n_iters, use_novelty, used_metrics,
                  used_constraints=[], *args, **kwargs ):
        super().__init__(
            n_var=state.n_tiles,
            n_obj=len(used_metrics)+use_novelty,
            n_constr=len(used_constraints),
            type_var=np.integer, *args, **kwargs
        )
        self.state = state
        self.n_districts = n_districts
        self.used_metrics = used_metrics
        self.used_constraints = used_constraints
        self.use_novelty = use_novelty
        if self.use_novelty:
            print('Making novelty archive...')
            self.archive = NoveltyArchive(state, n_districts)

    def _evaluate(self, districts, out, *args, **kwargs):
        out['F'] = np.array([
            [ f(self.state, d, self.n_districts) for f in self.used_metrics ]
            for d in districts
        ])
        if self.used_constraints:
            out['G'] = np.array([
                [ f(self.state, d, self.n_districts) !=0 for f in self.used_constraints ]
                for d in districts
            ])
        if self.use_novelty:
            novelty = np.zeros(len(districts))
            novelty = self.archive.updateAndGetSparseness(districts)
            novelty = 1.0 - novelty
            # print(novelty.min(), novelty.mean(), novelty.max())
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
def save_results(outdir, config, state, result, opt_i, hv_history):
    """ Save all the results and config to disk. """
    with open(os.path.join(outdir, 'config.json'), 'w') as f:
        json.dump(vars(config), f, indent=4)
    with open(os.path.join(outdir, 'state_%i.json'%opt_i), 'w') as f:
        json.dump(state.toJSON(), f)
    with open(os.path.join(outdir, 'hv_%i.txt'%opt_i), 'w') as f:
        for hv in hv_history:
            f.write("%f\n" % hv)
    with open(os.path.join(outdir, 'rundata_%i.json'%opt_i), 'w') as f:
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

def upscale(districts, mapping):
    """ Convert districts to the next phase. """
    upscaled = np.zeros((districts.shape[0], mapping.shape[0]), dtype='i')
    for i in range(districts.shape[0]):
        for j in range(mapping.shape[0]):
            upscaled[i, j] = districts[i, mapping[j]]
    return upscaled

def log_algorithm(algorithm, text, pbar, HV, hypervolume_mask):
    """ A logging function passed as the 'callback' to the algorithm """
    if algorithm.history is None:
        algorithm.history = []

    F = algorithm.pop.get("F")

    # Fix novelty stagnation by recalculating all novelty scores. TODO: Put in seperate function.
    if algorithm.problem.use_novelty:
        X = algorithm.pop.get('X')
        novelty = algorithm.problem.archive.getNovelty(X)
        novelty = 1.0 - novelty
        F[:, -1] = novelty
        algorithm.pop.set('F', F)
    
    if F.shape[1] != len(hypervolume_mask): # TODO find out why this happens only first gen.
        return

    _F = F[:, hypervolume_mask]
    hv = round(HV.calc(_F), 5)
    algorithm.history.append( hv )
    # if hasattr(algorithm, 'pop_size_history'):
    #     algorithm.pop_size_history.append(int(F.shape[0]))
    pbar.update(1)
    pbar.set_description("%s: %s" % (text, hv))

def run_fi_optimization(ALG, state, metrics, constraints, seeds, config, n_gens, opt_i, feas_mask, infeas_mask):
    """ Run one optimziation phase with feasible-infeasible method. """
    pop_size = config.pop_size//2 # Half for each population.
    feas_algo = NSGA2_FI(
        pop_size=pop_size,
        sampling=seeds[:pop_size] if opt_i == 0 else seeds,
        mutation=DistrictMutation(state, config.n_districts, config.equality_constraint),
        crossover=DistrictCross(),
        callback=partial(
            log_algorithm,
            text='  Feas HV',
            HV=Hypervolume(ref_point=np.ones(sum(feas_mask))),
            pbar=tqdm(total=n_gens, position=0),
            hypervolume_mask=np.ones(sum(feas_mask), dtype='bool') # This gets only 1's because mask is already applied in FI alg.
        )
    )
    infeas_algo = NSGA2_FI(
        pop_size=pop_size,
        sampling=seeds[pop_size:] if opt_i == 0 else seeds,
        crossover=DistrictCross(),
        mutation=DistrictMutation(state, config.n_districts, 1.0),
        selection=TournamentSelection(func_comp=cv_agnostic_binary_tournament),
        callback=partial(
            log_algorithm,
            text='InFeas HV',
            HV=Hypervolume(ref_point=np.ones(sum(infeas_mask))),
            pbar=tqdm(total=n_gens, position=1),
            hypervolume_mask=np.ones(sum(infeas_mask), dtype='bool') # This gets only 1's because mask is already applied in FI alg.
        )
    )
    problem = DistrictProblemFI(
        state, config.n_districts, n_gens,
        use_novelty=config.novelty,
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
    return result, feas_algo.history

def run_optimization(ALG, state, metrics, constraints, seeds, config, n_gens, opt_i):
    mask = [ True ] * len(metrics) + ([ False ] if config.novelty else [])
    algorithm = ALG(
        pop_size=config.pop_size,
        sampling=seeds,
        crossover=DistrictCross(),
        mutation=DistrictMutation(state, config.n_districts, config.equality_constraint),
        callback=partial(
            log_algorithm,
            text='HV', 
            HV=Hypervolume(ref_point=np.ones(sum(mask))),
            pbar=tqdm(total=n_gens),
            hypervolume_mask=mask
        ),
    )
    problem = DistrictProblem(
        state, config.n_districts, n_gens,
        use_novelty=config.novelty,
        used_metrics=metrics,
        used_constraints=constraints
    )
    result = minimize(
        problem, algorithm, ('n_gen', n_gens),
        seed=0, verbose=False, save_history=False
    )
    result.F = result.F[:, mask]
    return result, algorithm.history
