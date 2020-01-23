import os, sys, random, time
import pygame
import numpy as np
sys.path.append(os.path.abspath('.'))
from src import districts
from src.draw import draw_districts, wait_loop
from src.state import State
from src.optimization import upscale

def upscale(districts, mapping):
    upscaled = np.zeros((districts.shape[0], mapping.shape[0]), dtype='i')
    for i in range(districts.shape[0]):
        for j in range(mapping.shape[0]):
            upscaled[i, j] = districts[i, mapping[j]]
    return upscaled

pygame.init()
seed = 1337
# seed = 1

if len(sys.argv) == 1:
    states = [ State.makeRandom(1000, seed=seed) ]
else:
    states = [ State.fromFile(sys.argv[1]) ]

# if len(sys.argv) == 1:
### Subdivide voronoi grid map. ###
screen = pygame.display.set_mode(( 2000, 500 ))
screen.fill(( 255, 255, 255 ))
n_districts = 20

n_divisions = 3
# states = [ State.makeRandom(1000, seed=seed) ]
# states = [ state ]
mappings = [ None ]

for _ in range(n_divisions):
    state, mapping = states[-1].contract()
    states.append(state)
    mappings.append(mapping)

dists = districts.make_random(states[-1], n_districts)
colors = np.random.randint(0, 255, (n_districts, 3))

for div_i, (state, mapping) in enumerate(zip(states[::-1], mappings[::-1])):
    dx = div_i * 500
    draw_districts(state, dists, n_districts, screen, colors,
                   draw_vertices=False, draw_neigbors_lines=True, dx=dx)
    if mapping is not None:
        dists = upscale(dists[np.newaxis], mapping)[0]
# else:
#     ### Subdivide real state data. ###
#     state = State.fromFile(sys.argv[1])
#     screen = pygame.display.set_mode(( 1200, 600 ))
#     screen.fill(( 255, 255, 255 ))
#     n_districts = 20
#     # print(state.n_tiles)
#     for _ in range(2):
#         state, mapping = state.contract(seed=seed)
#         # print(state.n_tiles)
#         dists = np.random.randint(0, n_districts, (state.n_tiles))
#         colors = np.random.randint(0, 255, (n_districts, 3))
#         draw_districts(state, dists, n_districts, screen, colors, draw_vertices=False, dy=0)
#         pygame.display.update()

pygame.display.update()
wait_loop()