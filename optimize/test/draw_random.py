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

n_districts = 5
# state = State.fromFile('data/NC.json')
state = State.makeRandom(1024, seed=1)
# state, mapping = state.contract()

met = metrics.compactness_convex_hull
# met = metrics.compactness_reock
mutate = True

districts = districts.make_random(state, n_districts)
tolerance = 0.3
print(fix_pop_equality(state, districts, n_districts, tolerance=tolerance, max_iters=1000))

pygame.init()
w, h = (800, 800 )
screen = pygame.display.set_mode((w, h))
screen.fill((255, 255, 255))

colors = np.random.randint(0, 255, (n_districts, 3))


draw_districts(state, districts, n_districts, screen, colors, draw_bounding_circles=False, draw_bounding_hulls=True)
pygame.display.update()

while True:
    if mutate:
        d2 = districts.copy()

        n_pop = state.tile_populations.sum()
        ideal_pop = n_pop / n_districts
        pop_max = ideal_pop * (1+tolerance)
        pop_min = ideal_pop * (1-tolerance)

        mutation.mutate(d2, n_districts, state, 0.00, pop_min, pop_max)

        new_fitness = met(state, d2, n_districts)
        # print('new_fitness', new_fitness)

        if new_fitness < met(state, districts, n_districts):
            print('\nnew_fitness', new_fitness)
            districts = d2
            draw_districts(state, districts, n_districts, screen, colors, draw_bounding_hulls=True, draw_bounding_circles=False)
            pygame.display.update()
        else:
            # pass
            print('.', end = '')

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()
            elif event.key == pygame.K_LEFT:
                p.mutate()
                draw_districts(state, districts, n_districts, screen, display)
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
