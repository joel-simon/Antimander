import sys, random, time
import pygame
from pygame import gfxdraw
import numpy as np

from state import State
import districts
import mutation
from constraints import fix_pop_equality
from metrics import compactness, efficiency_gap, competitiveness

n_districts = 5
state = State.makeRandom(200)
districts = districts.make_random(state, n_districts)

n_pop = state.tile_populations.sum()
ideal_pop = n_pop / n_districts
pop_max = ideal_pop * (1+ .1)
pop_min = ideal_pop * (1- .1)

fix_pop_equality(state, districts, n_districts, tolerance=.10, max_iters=1000)

pygame.init()
screen = pygame.display.set_mode((600, 600))
screen.fill((255, 255, 255))
font = pygame.font.SysFont("comicsansms", 14)

def draw_districts(districts, state, colors):
    for i in range(state.n_tiles):
        vertices = [ (x*600, y*600) for x,y in state.tile_vertices[i] ]
        district = districts[i]

        gfxdraw.filled_polygon(screen, vertices, colors[district] )
        gfxdraw.aapolygon(screen, vertices, (50, 50, 50))

        x,y = state.tile_centers[i]
        v = (int(x*600), int(y*600))

        if not mutation.can_lose(districts, state, n_districts, i):
            pygame.draw.circle(screen, (0,0,200), v, 5)

colors = np.random.randint(0, 255, (n_districts, 3))
mutate = True
draw_districts(districts, state, colors)


def C(state, districts, n_districts):
    tile_populations = state.tile_populations
    dist_pop = np.zeros((n_districts, 2) , dtype='float32')
    max_margin = 0.0

    for ti in range(state.n_tiles):
        dist_pop[districts[ti], 0] += tile_populations[ti, 0]
        dist_pop[districts[ti], 1] += tile_populations[ti, 1]
    print(dist_pop)
    for di in range(n_districts):
        margin = abs(dist_pop[di, 0] - dist_pop[di, 1]) / (dist_pop[di, 0] + dist_pop[di, 1])
        max_margin = margin if (margin > max_margin) else max_margin

    return max_margin

while True:
    if mutate:
        d2 = districts.copy()
        mutation.mutate(d2, n_districts, state, 0.01, pop_min, pop_max)
        if competitiveness(state, d2, n_districts) < competitiveness(state, districts, n_districts):
            districts = d2
            print(competitiveness(state, d2, n_districts), C(state, d2, n_districts))

        draw_districts(districts, state, colors)
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()
            elif event.key == pygame.K_LEFT:
                p.mutate()
                draw_districts(districts, colors)
                # pass
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
    pygame.display.update()