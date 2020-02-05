import os, random, time, json
import numpy as np
from functools import partial
from tqdm import tqdm
from copy import copy
from pymoo.model.problem import Problem
from pymoo.model.mutation import Mutation
from pymoo.model.crossover import Crossover
from pymoo.performance_indicator.hv import Hypervolume
from pymoo.algorithms.nsga2 import NSGA2
from pymoo.algorithms.nsga3 import NSGA3
# from pymoo.optimize import minimize

from src import districts, metrics, mutation
from src.state import State
from src.constraints import fix_pop_equality
# from src.novelty import DistrictHistogramNoveltyArchive as NoveltyArchive
from src.novelty import MutualTilesNoveltyArchive as NoveltyArchive
from src.feasibleinfeasible import *

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
        t = time.time()
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
            novelty = self.archive.updateAndGetSparseness(districts)
            novelty = 1.0 - ( novelty * 0.5 )
            np.clip(novelty, 0, 1, out=novelty)
            out['F'] = np.append( out['F'], novelty[:, np.newaxis], axis=1 )
        assert not np.isnan(out['F']).any()
        assert out['F'].min() >= 0
        assert out['F'].max() <= 1.0

class DistrictProblemFI(FI_problem_mixin, DistrictProblem):
    pass

############################################################################
def save_results(outdir, config, state, result, opt_i, hv_history, hv_history2=None):
    with open(os.path.join(outdir, 'config.json'), 'w') as f:
        json.dump(config, f, indent=4)

    with open(os.path.join(outdir, 'state_%i.json'%opt_i), 'w') as f:
        json.dump(state.toJSON(), f)

    with open(os.path.join(outdir, 'hv_%i.txt'%opt_i), 'w') as f:
        for hv in hv_history:
            f.write("%f\n" % hv)

    with open(os.path.join(outdir, 'rundata_%i.json'%opt_i), 'w') as f:
        json.dump({
            "config": config,
            'values': result.F.tolist(),
            'solutions': result.X.tolist(),
            'metrics_data': {
                'lost_votes': [
                    np.asarray(metrics.lost_votes(state, x, config['n_districts'])).tolist()
                    for x in result.X
                ],
                'bounding_hulls': [
                    metrics.bounding_hulls(state, x, config['n_districts'])
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

def log_algorithm(algorithm, text, pbar, HV, hypervolume_mask, use_novelty):
    """ A function passed as the 'callback' genetic algorithm, handles logging. """
    if algorithm.history is None:
        algorithm.history = []

    F = algorithm.pop.get("F")

    # Fix novelty stagnation (the novelty of old solutions).
    if algorithm.problem.use_novelty:
        X = algorithm.pop.get('X')
        novelty = algorithm.problem.archive.getNovelty(X)
        F[:, -1] = novelty
        algorithm.pop.set('F', F)

    if F.shape[1] == len(hypervolume_mask):
        hv = round(HV.calc(F[:, hypervolume_mask ]), 5)
        algorithm.history.append( hv )
        if hasattr(algorithm, 'pop_size_history'):
            algorithm.pop_size_history.append(int(F.shape[0]))
        pbar.update(1)
        pbar.set_description("%s: %s" % (text, hv))
    else:
        print(F.shape, hypervolume_mask)

def optimize(config, _state, outdir, save_plots=True):
    ############################################################################
    """ The core of the code. First, contract the state graph. """
    ############################################################################
    os.makedirs(outdir, exist_ok=False)
    print('-'*80)
    print('Starting Optimization:')
    for k, v in config.items():
        if k[0] != '_':
            print(f'\t{k}: {v}')
    print('-'*80)
    print('Subdividing State:')
    states = [ _state ]
    mappings = [ None ]
    while states[-1].n_tiles > config['max_start_tiles']:
        state, mapping = states[-1].contract()
        states.append(state)
        mappings.append(mapping)
    states = states[::-1]
    mappings = mappings[::-1]
    thresholds = np.linspace(*config['equality_range'], num=len(states))
    print('Equality thresholds:', thresholds)
    ############################################################################
    """ Second, Create an initial population that has populaiton equality. """
    ############################################################################
    seeds = []
    state = states[0]
    print('-'*80)
    print('Creating Initial Population:')
    feasibleinfeasible = bool(config['feasibleinfeasible'])
    with tqdm(total=config['pop_size']) as pbar:
        while len(seeds) < config['pop_size']:
            try:
                dists = districts.make_random(state, config['n_districts'])
                if not config['dont_fix_seeds']:
                    fix_pop_equality(
                        state, dists, config['n_districts'],
                        tolerance=thresholds[0],
                        max_iters=300
                    )
                seeds.append(dists)
                pbar.update(1)
            except Exception as e:
                #print('FPE failed.', e)
                pass
    seeds = np.array(seeds)
    ############################################################################
    """ Run a optimization process for each resolution using the previous
        outputs as the seeds for the next. """
    ############################################################################
    for opt_i, (state, mapping, threshold) in enumerate(zip(states, mappings, thresholds)):
        print('-'*80)
        print(f'Optimizing {opt_i} / {len(states)}')
        print(f'\tNum tiles: {state.n_tiles}\n\tThreshold: {threshold}')
        is_last_phase = opt_i == len(states)-1

        def is_compact(state, districts, n_districts):
            return metrics.polsby_popper(state, districts, n_districts) > 0.8

        used_metrics = []
        used_constraints = [ partial(metrics.equality, threshold=threshold) ]
        hypervolume_mask = []

        for name in config['metrics']:
            if name == 'novelty':
                pass
            elif name == 'equality':
                used_metrics.append(partial(metrics.equality, threshold=0))
                hypervolume_mask.append(False)
            else:
                used_metrics.append(getattr(metrics, name))
                hypervolume_mask.append(True)

        use_novelty = ('novelty' in config['metrics']) and opt_i <= config['novelty_phases']-1
        if use_novelty:
            print('Using novelty')

        if config['NSGA3']:
            from pymoo.factory import get_reference_directions
            ref_dirs = get_reference_directions("das-dennis", len(hypervolume_mask), n_partitions=50)
            ALG = partial(NSGA3, ref_dirs=ref_dirs)
        else:
            ALG = NSGA2

        if opt_i == 0:
            n_gens = config['n_gens_first']
        elif is_last_phase:
            n_gens = config['n_gens_last']
        else:
            n_gens = config['n_gens']

        if feasibleinfeasible:
            #Add a metric that is the contraints for feasible and objective for infeasible.
            # used_metrics.append(equality_thr)
            # used_metrics.append(partial(metrics.equality, threshold=0))

            # Feasible population seeks to maximize performance objectives.
            feas_mask = ([ True ] * (len(used_metrics)-1)) + [ False ]
            feas_hv_mask = copy(feas_mask)

            # Infeasible population seeks to maximize constraint violation.
            infeas_mask = ([ False ] * (len(used_metrics)-1)) + [ True ]
            infeas_hv_mask = copy(infeas_mask)

            if use_novelty:
                feas_mask.append(False)
                infeas_mask.append(True)
                feas_hv_mask.append(False)
                infeas_hv_mask.append(False)

            pop_size = config['pop_size']//2
            feas_algo = NSGA2_FI(
                pop_size=pop_size,
                sampling=seeds[:pop_size] if opt_i == 0 else seeds,
                mutation=DistrictMutation(state, config['n_districts'], threshold),
                crossover=DistrictCross(),
                callback=partial(
                    log_algorithm,
                    text='  Feas HV',
                    HV=Hypervolume(ref_point=np.ones(sum(feas_hv_mask))),
                    pbar=tqdm(total=n_gens, position=0),
                    hypervolume_mask=feas_hv_mask,
                    use_novelty=use_novelty
                )
            )
            infeas_algo = NSGA2_FI(
                pop_size=pop_size,
                sampling=seeds[pop_size:] if opt_i == 0 else seeds,
                crossover=DistrictCross(),
                mutation=DistrictMutation(state, config['n_districts'], 1.0),
                selection=TournamentSelection(func_comp=cv_agnostic_binary_tournament),
                callback=partial(
                    log_algorithm,
                    text='InFeas HV',
                    HV=Hypervolume(ref_point=np.ones(sum(infeas_hv_mask))),
                    pbar=tqdm(total=n_gens, position=1),
                    hypervolume_mask=infeas_hv_mask,
                    use_novelty=use_novelty
                )
            )
            problem = DistrictProblemFI(state, config['n_districts'], n_gens,
                                        use_novelty=use_novelty,
                                        used_metrics=used_metrics,
                                        used_constraints=used_constraints )
            result = FI_minimize(problem,feas_algo,infeas_algo,('n_gen', n_gens),
                                 feas_mask=feas_mask, infeas_mask=infeas_mask,
                                 seed=0, verbose=False )
            save_results(outdir, config, state, result, opt_i, feas_algo.history, infeas_algo.history)
            if save_plots:
                import matplotlib.pyplot as plt
                plt.figure()
                plt.plot(feas_algo.history, label='Feas Phase: %i'%opt_i)
                # plt.plot(infeas_algo.history, label='Infeas Phase: %i'%opt_i)
                plt.xlabel('Generations')
                plt.ylabel('Hypervolume')
                plt.legend()
                plt.savefig(os.path.join(outdir, 'hv_history_%i.png'%opt_i))
                # plt.figure()
                # plt.plot(feas_algo.pop_size_history, label='Feas Population: %i'%opt_i)
                # plt.plot(infeas_algo.pop_size_history, label='Infeas Population: %i'%opt_i)
                # plt.xlabel('Generations')
                # plt.ylabel('Population')
                # plt.legend()
                # plt.savefig(os.path.join(outdir, 'pop_history_%i.png'%opt_i))
            print('')
            print('Final HV %f'%feas_algo.history[-1])

        else:
            if use_novelty: # has to be last
                hypervolume_mask.append(False)
            HV = Hypervolume(ref_point=np.array([ 1 ]*sum(hypervolume_mask)))
            algorithm = ALG(
                pop_size=config['pop_size'],
                sampling=seeds,
                crossover=DistrictCross(),
                mutation=DistrictMutation(state, config['n_districts'], threshold),
                callback=partial(log_algorithm, text='HV', HV=HV,pbar=tqdm(total=n_gens),
                                 hypervolume_mask=hypervolume_mask,
                                 use_novelty=use_novelty),
            )
            problem = DistrictProblem(state, config['n_districts'], n_gens,
                                      use_novelty=use_novelty,
                                      used_metrics=used_metrics,
                                      used_constraints=used_constraints)
            result = minimize(problem, algorithm,('n_gen', n_gens), seed=0,
                              verbose=False, save_history=False )
            save_results(outdir, config, state, result, opt_i, algorithm.history)
            if save_plots:
                import matplotlib.pyplot as plt
                plt.plot(algorithm.history, label='Phase: %i'%opt_i)
                plt.xlabel('Generations')
                plt.ylabel('Hypervolume')
                plt.legend()
                plt.savefig(os.path.join(outdir, 'hv_history_%i.png'%opt_i))
            print('')
            print('Final HV %f'%algorithm.history[-1])

        if mapping is not None:
            seeds = upscale(result.X, mapping)
