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
from src.novelty import NoveltyArchive

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
        for i in range(X.shape[0]):
            mutation_rate = random.gauss(0.01, 0.01)
            mutation.mutate(X[i], self.n_districts, self.state, mutation_rate, self.pop_min, self.pop_max)
        return X

class DistrictProblem(Problem):
    """ This class just calls the obtective functions.
    """
    def __init__(self, state, n_districts, n_iters, use_novelty, metrics, **kwargs):
        super().__init__(n_var=state.n_tiles, n_obj=len(metrics)+use_novelty, type_var=np.integer, **kwargs)
        self.state = state
        self.n_districts = n_districts
        self.metrics = metrics
        self.use_novelty = use_novelty
        self.hv = Hypervolume(ref_point=np.array([1]*len(metrics)))
        self.hv_history = []
        self.pbar = tqdm(total=n_iters)
        if self.use_novelty:
            print('Making novelty archive...')
            self.archive = NoveltyArchive(state, n_districts)

    def _evaluate(self, districts, out, *args, **kwargs):
        t = time.time()
        out['F'] = np.array([
            [ f(self.state, d, self.n_districts) for f in self.metrics ]
            for d in districts
        ])
        # Dont count novelty in the hypervolume.
        self.hv_history.append(round(self.hv.calc(out['F']), 6))
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
    print('Subdividing state')
    states = [ _state ]
    mappings = [ None ]
    while states[-1].n_tiles > config['max_start_tiles']:
        state, mapping = states[-1].contract()
        states.append(state)
        mappings.append(mapping)
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
                print('FPE failed.', e)
                pass
    seeds = np.array(seeds)
    print('Created seeds')
    ############################################################################
    """ Run a optimization process for each resolution using the previous
        outputs as the seeds for the next. """
    ############################################################################
    os.makedirs(outdir, exist_ok=False)
    for opt_i, (state, mapping, threshold) in enumerate(zip(states, mappings, thresholds)):
        print('Optimizing', opt_i, state.n_tiles, threshold)
        last_res = opt_i == len(states)-1
        used_metrics = { name: getattr(metrics, name) for name in config['metrics'] if name != 'novelty' }
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
            use_novelty=('novelty' in config['metrics']) and not last_res,
            metrics=used_metrics.values()
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
