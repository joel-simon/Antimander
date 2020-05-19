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
from src.optimize_utils import  value_constraint

def optimize(config):
    """ This is the core function."""
    #---------------------------------------------------------------------------
    # Config validation.
    #---------------------------------------------------------------------------
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
    # for metric_name, limit, in config.metrics:
    #     assert (type(limit) is float and 0 <= limit <= 1), F'{limit} is not a number.' 
    #     assert hasattr(metrics, metric_name), F'{metric_name} is not a metric.' 
    print('-'*80)
    #---------------------------------------------------------------------------
    # The core of the code. First, contract the state graph.
    #---------------------------------------------------------------------------
    print('Subdividing State:')
    states = [ original_state ]
    mappings = [ None ]
    while states[-1].n_tiles > config.max_start_tiles:
        state, mapping = states[-1].contract()
        states.append(state)
        mappings.append(mapping)
    states = states[::-1]
    mappings = mappings[::-1]
    #---------------------------------------------------------------------------
    # Second, Create an initial population that has populaiton equality.
    #---------------------------------------------------------------------------
    state = states[0]
    print(f"{'-'*80}\nCreating Initial Population:")
    seeds = np.array(feasible_seeds(state, config))
    #---------------------------------------------------------------------------
    # Create metrics and hypervolume-masks. Masks determine which metrics are
    # used for hypervolume.
    #---------------------------------------------------------------------------
    used_metrics = [] # list of funtions that return floats.
    used_constraints = [] # list of funtions that return binary.
    if feasinfeas:
        feas_mask = [] # Binary array if metric_i is used in feas.
        infeas_mask = [] # Binary array if metric_i is used in infeas.
    
    metrics_limits = np.array([ metrics.limits[m] for m in config.metrics ])
    for mi, name in enumerate(config.metrics):
        limit = metrics.limits[name]
        used_metrics.append(getattr(metrics, name))
        
        if limit < 1.0:
            used_constraints.append(partial(value_constraint, index=mi, threshold=limit))
        if feasinfeas:
            feas_mask.append(True)
            infeas_mask.append(limit < 1.0) # If it has a limit it is a constraint.

    if config.equality_constraint > 0:
        used_constraints.append(partial(equality_constraint, threshold=config.equality_constraint))
        if feasinfeas: # FI uses contraints as objectives in infeas population.
            used_metrics.append(partial(metrics.equality)) # Equality objective does not have a threshold.
            feas_mask.append(False) # Only infeas population considers this.
            infeas_mask.append(True)
    
    if feasinfeas and config.novelty:  # add the flag for novelty last.
        infeas_mask.append(True) # Infeas always uses novelty.
        feas_mask.append(config.feasinfeas_2N) # Feas pop only uses novelty if this flag set.
    
    ALG = NSGA2
    if config.NSGA3:
        from pymoo.factory import get_reference_directions
        #TODO: grid search nsga3 params.
        ref_dirs = get_reference_directions("das-dennis", len(hv_mask), n_partitions=50)
        ALG = partial(NSGA3, ref_dirs=ref_dirs)
    
    if feasinfeas:
        run_fi = partial(run_fi_optimization, feas_mask=feas_mask, infeas_mask=infeas_mask)
        assert len(feas_mask) == len(infeas_mask) == (len(used_metrics) + bool(config.novelty))
    
    #---------------------------------------------------------------------------
    # Run a optimization process for each resolution using the previous
    # outputs as the seeds for the next.
    #---------------------------------------------------------------------------
    print('-'*80 + '\n' + 'Starting Optimization:')
    hv_histories = []
    # pf_histories = []
    n_gens = config.n_gens // len(states)

    for opt_i, (state, mapping) in enumerate(zip(states, mappings)):
        print('-'*80)
        print(f'Optimizing {opt_i} / {len(states)}')
        print(f'\tNum tiles: {state.n_tiles}')
        last_phase = opt_i == len(states)-1
        OPT = run_fi if feasinfeas else run_optimization
        result, hv_history = OPT(ALG, state, used_metrics, used_constraints,
                                 seeds, config, n_gens, opt_i)
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
