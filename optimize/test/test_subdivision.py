import os, sys, random, time
import pygame
import numpy as np
sys.path.append(os.path.abspath('.'))
from src import districts
from src.draw import draw_districts, wait_loop
from src.state import State

pygame.init()
seed = 1337

if len(sys.argv) == 1:
    ### Subdivide voronoi grid map. ###
    state = State.makeRandom(1000, seed=seed)
    screen = pygame.display.set_mode(( 2000, 500 ))
    screen.fill(( 255, 255, 255 ))
    n_districts = 20
    for dx in [0, 500, 1000, 1500]:
        if dx != 0:
            state, mapping = state.contract(seed=seed)
        # dists = districts.make_random(state, n_districts)
        dists = np.random.randint(0, n_districts, (state.n_tiles))
        colors = np.random.randint(0, 255, (n_districts, 3))
        draw_districts(state, dists, n_districts, screen, colors, draw_vertices=False, draw_neigbors_lines=True, dx=dx)

else:
    ### Subdivide real state data. ###
    state = State.fromFile(sys.argv[1])
    screen = pygame.display.set_mode(( 1200, 600 ))
    screen.fill(( 255, 255, 255 ))
    n_districts = 20
    print(state.n_tiles)
    for _ in range(2):
        state, mapping = state.contract(seed=seed)
        print(state.n_tiles)
    dists = np.random.randint(0, n_districts, (state.n_tiles))
    colors = np.random.randint(0, 255, (n_districts, 3))
    draw_districts(state, dists, n_districts, screen, colors, draw_vertices=False, dy=0)

pygame.display.update()
wait_loop()