import os, sys, random, time
import pygame
from pygame import gfxdraw
import numpy as np
sys.path.append(os.path.abspath('.'))
from src.state import State
from src import districts, mutation, metrics
from src.connectivity import can_lose
from src.constraints import fix_pop_equality
from src.draw import draw_districts


state = State.fromFile('data/WI.json')
# state = State.makeRandom(300, seed=1)
# for _ in range(1):
#     state, _ = state.contract(seed=0)
#     print(state.n_tiles)

# met = metrics.compactness_convex_hull
met = metrics.polsby_popper
mutate = False
n_districts = 50
# districts = districts.make_random(state, n_districts)
districts = np.random.randint(0, n_districts, (state.n_tiles,), dtype='i')
tolerance = 0.5
draw_kwargs = {
    "draw_bounding_hulls": False,
    "draw_bounding_circles": False,
    "draw_district_edges": False,
    "draw_vertices": False,
    "draw_neigbors_lines": True
}

# print(fix_pop_equality(state, districts, n_districts, tolerance=tolerance, max_iters=1000))
pygame.init()
w, h = (1200, 1200)
screen = pygame.display.set_mode((w, h))
screen.fill((255, 255, 255))
colors = np.random.randint(0, 255, (n_districts, 3))


draw_districts(state, districts, n_districts, screen, colors, **draw_kwargs)
pygame.display.update()
step = 0
while True:
    if mutate:
        d2 = districts.copy()

        n_pop = np.sum(state.tile_populations)
        ideal_pop = n_pop / n_districts
        pop_max = ideal_pop * (1+tolerance)
        pop_min = ideal_pop * (1-tolerance)

        mutation.mutate(d2, n_districts, state, 0.00, pop_min, pop_max)

        new_fitness = met(state, d2, n_districts)

        if new_fitness < met(state, districts, n_districts):
            print('\nnew_fitness', step, new_fitness)
            districts = d2
            draw_districts(state, districts, n_districts, screen, colors, **draw_kwargs)
            pygame.display.update()
        else:
            # pass
            print('.', end = '')

        step += 1

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()
            # elif event.key == pygame.K_LEFT:
                # p.mutate()
                # draw_districts(state, districts, n_districts, screen, display)
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
