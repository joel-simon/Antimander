import os, sys, random, time
import pygame
from pygame import gfxdraw
import numpy as np
sys.path.append(os.path.abspath('.'))
from src.state import State
from src import districts, mutation, metrics, metrics_test
from src.connectivity import can_lose
from src.constraints import fix_pop_equality
from src.draw import draw_districts

n_districts = 5
# state = State.fromFile('data/NC.json')
state = State.makeRandom(100, seed=None)
state, mapping = state.contract()

met = metrics.compactness_ch

districts = districts.make_random(state, n_districts)

n_pop = state.tile_populations.sum()
ideal_pop = n_pop / n_districts
pop_max = ideal_pop * (1+ 1)
pop_min = ideal_pop * (1- 1)

# print(fix_pop_equality(state, districts, n_districts, tolerance=.10, max_iters=1000))

pygame.init()
w, h = (1200, 1200 )
screen = pygame.display.set_mode((w, h))
screen.fill((255, 255, 255))

colors = np.random.randint(0, 255, (n_districts, 3))
mutate = False


w, h = screen.get_width(), screen.get_height()
xmin, ymin, xmax, ymax = state.bbox
def pmap(p):
    return (
        int((p[0]-xmin) * w/(xmax-xmin)),
        h - int((p[1]-ymin) * h/(ymax-ymin))
    )

def draw_shapes(screen, state, polygons):
    for points in polygons:
        points = [ pmap(p) for p in points ]
        # gfxdraw.aapolygon(screen, points, (50, 50, 50))
        pygame.draw.polygon(screen, (50, 50, 50), vertices, 3)


# for va, vb in state.derp:
#     va = pmap(va)
#     vb = pmap(vb)
#     pygame.gfxdraw.line(screen, *va, *vb, (255, 0, 0))

# from src.test import merge_polygons
# polygon = merge_polygons(state.tile_vertices)
# print(polygon)
draw_districts(state, districts, n_districts, screen, colors)
pygame.display.update()

while True:
    if mutate:
        d2 = districts.copy()
        mutation.mutate(d2, n_districts, state, 0.01, pop_min, pop_max)

        new_fitness = met(state, d2, n_districts)
        # print(new_fitness, met(state, districts, n_districts))

        if new_fitness < met(state, districts, n_districts):
            print(new_fitness)
            districts = d2
            draw_districts(state, districts, n_districts, screen, colors)

            draw_shapes(screen, state, [polygon])

            pygame.display.update()
        else:
            pass
            # print('.')

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
