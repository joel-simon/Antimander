import os, sys, copy, time, copy
import numpy as np
from tqdm.notebook import tqdm
from IPython.utils import io
from concurrent.futures import ProcessPoolExecutor
sys.path.append(os.path.abspath('../optimize'))
from src.optimization import optimize
from easydict import EasyDict as edict
import matplotlib.pyplot as plt

def optimize_silent(config):
    try:
        with io.capture_output() as captured:
            X, F, H = optimize(edict(config))
    except Exception as e:
        print('Error in optimize', e)
        X, F, H = None, None, None
    print('.', end='', flush=True)
    return X, F, H

def optimize_parallel(configs, n_cores=None):
    if n_cores is None:
        n_cores = os.cpu_count()
    start = time.time()
    with ProcessPoolExecutor(max_workers=n_cores) as executor:
        data = list(executor.map(optimize_silent, configs))
    print(f'\nFinished {len(configs)} in {round(time.time()-start, 5)} seconds.')
    return data
        
def optimize_repeat(configs, n_repeats, n_cores=None):
    with_repeats = []
    for conf in configs:
        for seed in range(n_repeats):
            out = f"{conf.out}_s{seed}" if conf.out else None
            print(out)
            with_repeats.append(dictadd(conf, seed=seed, out=out))
    results = optimize_parallel(with_repeats, n_cores)
    return [ results[i*n_repeats:(i+1)*n_repeats ] for i in range(len(configs)) ]                                                 

def dictadd(d, **kwarks):
    d = edict(copy.deepcopy(d))
    for k, v in kwarks.items():
        assert k in d, (k, d)
        d[k] = v
    return d

def plot_final_hv(data, xlabel, x):
    hv_histories = [ d[1] for d in data ]
    y = np.zeros(len(hv_histories))
    err = np.zeros(len(hv_histories))
    for i in range(len(hv_histories)):
        final_hvs = [ hv_histories[i][j][-1][-1] for j in range(len(results[i])) ]
        y[i] = np.mean(final_hvs)
        err[i] = np.std(final_hvs)
    plt.fill_between(x, y-err, y+err, alpha=.5)
    plt.plot(x, y)
    plt.xlabel(xlabel)
    plt.ylabel('Hypervolume')
    
def plot_repeats(data, title=None, log=True):
    hv_histories = [ d[2] for d in data ]
    hv_histories = np.array(hv_histories)
    
    if log:
        print(title)
        print('\tavg final hv', round(hv_histories[:, -1, -1].mean(), 5))
        print('\tavg final pf', np.mean( [ len(d[0]) for d in data ]))
      
    n_steps = hv_histories.shape[2]
    for phase_i in range(hv_histories.shape[1]):
        x = np.arange(n_steps)
        y = hv_histories[:, phase_i].mean(axis=0)
        err = hv_histories[:, phase_i].std(axis=0)
        plt.fill_between(x, y-err, y+err, alpha=.5)
        plt.plot(x, y, label=f'Phase {phase_i}')
    if title:
        plt.title(title)
    plt.xlabel('Generations')
    plt.ylabel('Hypervolume')
    plt.legend(loc='lower right')

default_config = edict({
    "state": None,
    "out": None,
    "seed": 1,
    "feasinfeas":False,
    "feasinfeas_2N":False,
    "max_start_tiles":400,
    "n_districts": 8,
    "n_gens": 12000,
    "pop_size": 300,
    "metrics":[
      "polsby_popper",
      "competitiveness",
      "efficiency_gap"
    ],
    "equality_constraint":0.05,
    "novelty":False,
    "NSGA3":False,
    "dont_fix_seeds":False,
    "pp_constraint": None,
    "nov_params": {}
})