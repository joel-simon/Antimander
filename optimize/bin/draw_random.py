import sys, random, time
import pygame
from pygame import gfxdraw
import numpy as np

from state import State
import districts
import mutation
from connectivity import can_lose
from constraints import fix_pop_equality
import metrics

n_districts = 5
state = State.makeRandom(300, seed=0).contract(seed=0)
# print(state.tile_neighbours)
# state = State.fromFile('state.json')
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
        district = districts[i]
        vertices = [ (x*600, y*600) for x,y in state.tile_vertices[i] ]
        # vertices = [ ((x+93)*100, 600 - ((y-42)*100)) for x,y in state.tile_vertices[i] ]
        gfxdraw.filled_polygon(screen, vertices, colors[district] )
        gfxdraw.aapolygon(screen, vertices, (50, 50, 50))

    # g = state.neighbour_graph[0]
    # print(g)
    # for i, J in g.items():
    #     x,y = state.tile_centers[i]
    #     center = (int(x*600), int(y*600))
    #     for j in J:
    #         x0, y0 = state.tile_centers[j]
    #         center0 = (int(x0*600), int(y0*600))
    #         pygame.gfxdraw.line(screen, *center, *center0, (0, 0, 0, 255))
    # return

    for i in range(state.n_tiles):
        x,y = state.tile_centers[i]
        center = (int(x*600), int(y*600))

        for j in state.tile_neighbours[i]:
            if i < j:
                x0, y0 = state.tile_centers[j]
                center0 = (int(x0*600), int(y0*600))
                pygame.gfxdraw.line(screen, *center, *center0, (0, 0, 0, 255))

        if not can_lose(districts, state, n_districts, i):
            pygame.draw.circle(screen, (0,0,200), center, 5)

colors = np.random.randint(0, 255, (n_districts, 3))
mutate = True
draw_districts(districts, state, colors)

met = metrics.efficiency_gap
# met = efficiency_gap

while True:
    if mutate:
        d2 = districts.copy()
        mutation.mutate(d2, n_districts, state, 0.01, pop_min, pop_max)
        # print(met(state, d2, n_districts))
        if met(state, d2, n_districts) < met(state, districts, n_districts):
            districts = d2
        draw_districts(districts, state, colors)

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()
            elif event.key == pygame.K_LEFT:
                p.mutate()
                draw_districts(districts, colors)
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
    pygame.display.update()