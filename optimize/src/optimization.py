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
# from src.novelty import DistrictHistogramNoveltyArchive as NoveltyArchive
from src.feasibleinfeasible import *
from src.optimize_utils import *

def optimize(config):
    """ This is the core function."""
    ############################################################################
    # Config validation.
    ############################################################################
    if config.feasinfeas_2N:
        assert config.novelty is not None, 'Must set a novelty method for feasinfeas_2N'
    assert config.novelty is False or config.novelty in novelty.archives, 'Novelty method does not exist:'+config.novelty
    feasinfeas = bool(config.feasinfeas) or bool(config.feasinfeas_2N)
    if config.out is not None:
        os.makedirs(config.out, exist_ok=False)
    for k, v in vars(config).items():
        if k[0] != '_': print(f'{k}: {v}')
    original_state = State.fromFile(config.state)
    original_state = original_state.mergeIslands()[0]
    if config.seed is not None:
        random.seed(config.seed)
        np.random.seed(config.seed)
    print('-'*80)
    ############################################################################
    # The core of the code. First, contract the state graph.
    ############################################################################
    print('Subdividing State:')
    states = [ original_state ]
    mappings = [ None ]
    while states[-1].n_tiles > config.max_start_tiles:
        state, mapping = states[-1].contract()
        states.append(state)
        mappings.append(mapping)
    states = states[::-1]
    mappings = mappings[::-1]
    ############################################################################
    # Second, Create an initial population that has populaiton equality.
    ############################################################################
    state = states[0]
    print(f"{'-'*80}\nCreating Initial Population:")
    seeds = np.array(feasible_seeds(state, config))
    ############################################################################
    # Create metrics and hypervolume-masks. Masks determine which metrics are
    # used for hypervolume.
    ############################################################################
    used_metrics = []
    used_constraints = []
    if feasinfeas:
        feas_mask = [] # Binary array if metric_i is used in feas.
        infeas_mask = [] # Binary array if metric_i is used in infeas.
    for name in config.metrics:
        if name == 'competitiveness':
            def test(state, districts, n_districts):
                score = np.array(metrics.competitiveness(state, districts, n_districts))
                score = score if score > .02 else 0
                return score
            print('using competitiveness thresh')
            used_metrics.append(test)
        else:
            used_metrics.append(getattr(metrics, name))
        if feasinfeas:
            feas_mask.append(True)
            infeas_mask.append(False)
    
    if config.pp_constraint and config.pp_constraint > 0:
        def pp_constraint(state, districts, n_districts):
            pp_scores = metrics.polsby_popper(state, districts, n_districts)
            return (pp_scores > config.pp_constraint)
        used_constraints.append(pp_constraint)
        infeas_mask[0] = True
    
    if config.equality_constraint > 0:
        used_constraints.append(partial(metrics.equality, threshold=config.equality_constraint))
        if feasinfeas: # FI uses contraints as objectives in infeas population.
            used_metrics.append(partial(metrics.equality, threshold=0)) # Equality objective does not have a threshold.
            feas_mask.append(False) # Only infeas population considers this.
            infeas_mask.append(True)
    
    if feasinfeas and config.novelty:  # add the flag for novelty last.
        infeas_mask.append(True) # Infeas always uses novelty.
        feas_mask.append(config.feasinfeas_2N) # Feas pop only uses novelty if this flag set.
    
    ALG = NSGA2
    if config.NSGA3:
        from pymoo.factory import get_reference_directions
        ref_dirs = get_reference_directions("das-dennis", len(hv_mask), n_partitions=50)
        ALG = partial(NSGA3, ref_dirs=ref_dirs)
    
    if feasinfeas:
        run_fi = partial(run_fi_optimization, feas_mask=feas_mask, infeas_mask=infeas_mask)
        assert len(feas_mask) == len(infeas_mask) == (len(used_metrics) + bool(config.novelty))
    
    ############################################################################
    # Run a optimization process for each resolution using the previous
    # outputs as the seeds for the next.
    ############################################################################
    print('-'*80 + '\n' + 'Starting Optimization:')
    hv_histories = []
    # pf_histories = []
    n_gens = config.n_gens // len(states)

    # pp_constraints = np.linspace(1.0, config.pp_constraint, len(states))
    print(feas_mask, infeas_mask)
    for opt_i, (state, mapping) in enumerate(zip(states, mappings)):
        print('-'*80)
        print(f'Optimizing {opt_i} / {len(states)}')
        print(f'\tNum tiles: {state.n_tiles}')
        last_phase = opt_i == len(states)-1
        use_ppcnstr = config.pp_constraint# and opt_i > 0
        
        # def pp_constraint(state, districts, n_districts):
        #     pp_scores = metrics.polsby_popper(state, districts, n_districts)
        #     return (pp_scores > config.pp_constraint)

        OPT = run_fi if feasinfeas else run_optimization
        result, hv_history = OPT(
            ALG, state, used_metrics,
            used_constraints,
            # + [pp_constraint] if use_ppcnstr else used_constraints,
            seeds, config, n_gens, opt_i
        )
        hv_histories.append(hv_history)
        # pf_histories.append(pf_history)
        if config.out is not None:
            save_results(config, state, result, opt_i, hv_history)#, pf_history)
            plot_results(config, state, result, opt_i, hv_history)#, pf_history)
        if not last_phase:
            # seeds = upscale(result.X, mapping)
            seeds = upscale(result.pop.get('X'), mapping)
        print('Final HV %f'%hv_history[-1])
    
    return result.X.tolist(), result.F.tolist(), hv_histories
