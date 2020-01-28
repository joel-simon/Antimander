import os, random, time, json
import numpy as np
from functools import partial
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
from src.novelty import NoveltyArchive
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
                  used_contraints=[], hypervolume_mask=None, *args, **kwargs ):
        super().__init__(
            n_var=state.n_tiles,
            n_obj=len(used_metrics)+use_novelty,
            n_constr=len(used_contraints),
            type_var=np.integer, *args, **kwargs
        )
        self.state = state
        self.n_districts = n_districts
        self.used_metrics = used_metrics
        self.used_contraints = used_contraints
        self.use_novelty = use_novelty
        if hypervolume_mask is None:
            hypervolume_mask = [ 1 ] * len(used_metrics)
        self.hypervolume_mask = hypervolume_mask
        self.hv = Hypervolume(ref_point=np.array([ 1 ]*sum(hypervolume_mask)))
        self.hv_history = []
        self.pbar = tqdm(total=n_iters)
        if self.use_novelty:
            print('Making novelty archive...')
            self.archive = NoveltyArchive(state, n_districts)

    def _evaluate(self, districts, out, *args, **kwargs):
        t = time.time()
        out['F'] = np.array([
            [ f(self.state, d, self.n_districts) for f in self.used_metrics ]
            for d in districts
        ])
        if self.used_contraints:
            out['G'] = np.array([
                [ f(self.state, d, self.n_districts) !=0 for f in self.used_contraints ]
                for d in districts
            ])
        # Dont count novelty in the hypervolume.
        hv = self.hv.calc(out['F'][:, self.hypervolume_mask])
        self.hv_history.append(round(hv, 6))
        if self.use_novelty:
            novelty = self.archive.updateAndGetSparseness(districts)
            novelty = 1.0 - ( novelty * 0.5 )
            np.clip(novelty, 0, 1, out=novelty)
            out['F'] = np.append( out['F'], novelty[:, np.newaxis], axis=1 )
        assert not np.isnan(out['F']).any()
        assert out['F'].min() >= 0
        assert out['F'].max() <= 1.0
        self.pbar.update(1)
        self.pbar.set_description("Hypervolume %s" % self.hv_history[-1])

# class DistrictProblemContrained(DistrictProblem):
#     """ Like dsitrict problem except poulation equality is a hard constraint """
#     def __init__(self, state, n_districts, n_iters, use_novelty, used_metrics, equality_threshold, *args, **kwargs):
#         # Add equality to list of objectives.
#         used_metrics = used_metrics.slice()
#         self.equality = partial(metrics.equality, threshold=equality_threshold)
#         used_metrics.append(self.equality)
#         super().__init__(state, n_districts, n_iters, use_novelty, used_metrics, n_constr=1, *args, **kwargs)

#     def _evaluate(self, districts, out, *args, **kwargs):
#         # Add equality to list of constraints.
#         super()._evaluate(districts, out, *args, **kwargs)
#         out['G'] = np.array([
#             self.equality(self.state, d, self.n_districts) != 0.0
#             for d in districts
#         ])

class DistrictProblemFI(FI_problem_mixin, DistrictProblem):
    pass

############################################################################
def save_results(outdir, config, state, result, opt_i, hv_history):
    with open(os.path.join(outdir, 'config.json'), 'w') as f:
        json.dump(config, f, indent=4)
    with open(os.path.join(outdir, 'rundata_%i.json'%opt_i), 'w') as f:
        json.dump({
            "config": config,
            'state': state.toJSON(),
            'values': result.F.tolist(),
            'solutions': result.X.tolist(),
            'hv_history': hv_history,
            'metrics_data': {
                'lost_votes': [
                    np.asarray(metrics.lost_votes(state, x, config['n_districts'])).tolist()
                    for x in result.X
                ],
                'bounding_hulls': [
                    [ h.tolist() for h in metrics.bounding_hulls(state, x, config['n_districts']) ]
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

def optimize(config, _state, outdir, save_plots=True):
    ############################################################################
    """ The core of the code. First, contract the state graph. """
    ############################################################################
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
    thresholds = np.linspace(0.5, 0.1, num=len(states))
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
                if not feasibleinfeasible:
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
    os.makedirs(outdir, exist_ok=False)
    for opt_i, (state, mapping, threshold) in enumerate(zip(states, mappings, thresholds)):
        print('-'*80)
        print(f'Optimizing {opt_i} / {len(states)}')
        print(f'\tNum tiles: {state.n_tiles}\n\tThreshold: {threshold}')
        last_phase = opt_i == len(states)-1
        used_metrics = [ getattr(metrics, name) for name in config['metrics'] if name != 'novelty' ]
        used_contraints = []
        use_novelty = ('novelty' in config['metrics']) and not last_phase
        hypervolume_mask = [ True ] * len(used_metrics)
        if feasibleinfeasible:
            equality = partial(metrics.equality, threshold=threshold)
            used_contraints.append(equality)
            used_metrics.append(equality)
            hypervolume_mask.append(False)

            feas_algo = NSGA2_FI(
                pop_size=config['pop_size'],
                sampling=seeds,
                crossover=DistrictCross(),
                mutation=DistrictMutation(state, config['n_districts'], threshold),
            )
            infeas_algo = NSGA2_FI(
                pop_size =config['pop_size'],
                sampling =seeds,
                crossover=DistrictCross(),
                mutation =DistrictMutation(state, config['n_districts'], 1.0),
                selection=TournamentSelection(func_comp=cv_agnostic_binary_tournament)
            )
            problem = DistrictProblemFI(
                state,
                config['n_districts'],
                config['n_gens'],
                use_novelty=use_novelty,
                used_metrics=used_metrics,
                used_contraints=used_contraints,
                hypervolume_mask=hypervolume_mask,
            )
            # Feasible population seeks to maximize performance objectives.
            feas_mask = ([ True ] * (len(used_metrics)-1)) + [ False ]
            # Infeasible population seeks to maximize constraint violation.
            infeas_mask = ([ False ] * (len(used_metrics)-1)) + [ True ]
            # Both populations use novelty.
            if use_novelty:
                feas_mask.append(True)
                infeas_mask.append(True)
            result = FI_minimize(
                problem,
                feas_algo,
                infeas_algo,
                ('n_gen', config['n_gens']),
                feas_mask=feas_mask,
                infeas_mask=infeas_mask,
                seed=0,
                verbose=False
            )
        else:
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
                mutation=DistrictMutation(state, config['n_districts'], threshold),
            )
            problem = DistrictProblem(
                state,
                config['n_districts'],
                config['n_gens'],
                use_novelty=use_novelty,
                used_metrics=used_metrics
            )
            result = minimize(
                problem,
                algorithm,
                ('n_gen', config['n_gens']),
                seed=0,
                verbose=False,
                save_history=False
            )
        save_results(outdir, config, state, result, opt_i, problem.hv_history)
        if mapping is not None:
            seeds = upscale(result.X, mapping)
        if save_plots:
            import matplotlib.pyplot as plt
            plt.plot(problem.hv_history, label='Phase: %i'%opt_i)
            plt.xlabel('Generations')
            plt.ylabel('Hypervolume')
            plt.legend()
            plt.savefig(os.path.join(outdir, 'hv_history_%i.png'%opt_i))
        print('')
        print('Final HV %f'%problem.hv_history[-1])
