import matplotlib.pyplot as plt
import numpy as np
import math, random, json
from nsga2 import run

from map import Map
from partition import Partition

plt.ion()

m = Map.makeRandom(100, seed=0)

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
    config={
        'maximize': True,
        'pop_size':  300,
        'n_objectives': 2,
        'max_gen':  200
    },
    seed=seed,
    crossover=crossover,
    evaluate=evaluate,
    notification=notification,
    copy=copy
)

np.save('out/values.npy', np.array(values))
np.save('out/solutions.npy', np.array([s.tile_districts for s in solutions]))
with open('out/map.json', 'w') as f:
    json.dump(m.toJSON(), f)
