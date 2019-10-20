import matplotlib.pyplot as plt
import numpy as np
import math, random, json
from nsga2 import run

from map import Map
from partition import Partition

plt.ion()

m = Map.makeRandom(100, seed=0)

n_districts = 5
nsga_config = {
    'maximize': True,
    'pop_size':  200,
    'n_objectives': 2,
    'max_gen':  100
}

def seed():
    return Partition.makeRandom(5, m, seed=None)

def crossover(a, b):
    a = a.copy()
    b = b.copy()
    a.mutate()
    b.mutate()
    return (a, b)

def evaluate(solutions):
    return np.array([ p.evaluate() for p in solutions ])

def notification(gen_no, pf_solutions, pf_values):
    print(gen_no, len(pf_values))
    pf_values = np.array(pf_values)
    plt.xlabel('Function 1', fontsize=15)
    plt.ylabel('Function 2', fontsize=15)
    plt.scatter(pf_values[:,0], pf_values[:,1])
    plt.pause(0.0001)
    plt.clf()

def copy(p):
    return p.copy()

solutions, values = run(
    config=nsga_config,
    seed=seed,
    crossover=crossover,
    evaluate=evaluate,
    notification=notification,
    copy=copy
)

# np.save('out/values.npy', np.array(values))
# np.save('out/solutions.npy', np.array([s.tile_districts for s in solutions]))
# with open('out/values.json', 'w') as f:

with open('out/rundata.json', 'w') as f:
    json.dump({
        'n_districts': n_districts,
        'nsga_config': nsga_config,
        'map': m.toJSON(),
        'values': np.array(values).tolist(),
        'solutions': [ s.tile_districts.tolist() for s in solutions ]
    }, f)
