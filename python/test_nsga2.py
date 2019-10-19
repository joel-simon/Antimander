import matplotlib.pyplot as plt
import numpy as np
import math, random
from nsga2 import run

plt.ion()

def seed():
    return random.uniform(-10, 10)

def crossover(a, b):
    child1 = (a + b) / 2
    child2 = (a + b) / 2
    child1 += random.uniform(-0.5, 0.5)
    child2 += random.uniform(-0.5, 0.5)

    return [ child1, child2 ]

def evaluate(solutions):
    return np.array([[ -x**2, -(x-2)**2 ] for x in solutions ])

def notification(gen_no, pf_solutions, pf_values):
    pf_values = np.array(pf_values)
    plt.xlabel('Function 1', fontsize=15)
    plt.ylabel('Function 2', fontsize=15)
    plt.scatter(pf_values[:,0], pf_values[:,1])
    plt.pause(0.0001)
    plt.clf()

def copy(v):
    return v

run(
    config={
        'maximize': True,
        'pop_size':  20,
        'n_objectives': 2,
        'max_gen':  100
    },
    seed=seed,
    crossover=crossover,
    evaluate=evaluate,
    notification=notification,
    copy=copy
)