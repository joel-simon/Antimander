import os, sys, random, time
sys.path.append(os.path.abspath('.'))
import pygame
from pygame import gfxdraw
import numpy as np
from src.state import State
from src import districts, mutation, metrics
from src.connectivity import can_lose
from src.constraints import fix_pop_equality
import src.metrics

n_districts = 5
# state_final = State.makeRandom(300, seed=0)
state_final = State.fromFile('data/t_500.json')
state, mapping = state_final.contract(seed=0)
districts = districts.make_random(state, n_districts)
fix_pop_equality(state, districts, n_districts, tolerance=.10, max_iters=1000)

pygame.init()
screen = pygame.display.set_mode((600*2, 600))
screen.fill((255, 255, 255))

def draw_districts(districts, state, colors, dx=0):
    for i in range(state.n_tiles):
        district = districts[i]
        vertices = [ ((x*600)+dx, y*600) for x,y in state.tile_vertices[i] ]
        gfxdraw.filled_polygon(screen, vertices, colors[district] )
        gfxdraw.aapolygon(screen, vertices, (50, 50, 50))

    for i in range(state.n_tiles):
        x,y = state.tile_centers[i]
        center = (int(x*600)+dx, int(y*600))

        for j in state.tile_neighbours[i]:
            if i < j:
                x0, y0 = state.tile_centers[j]
                center0 = (int(x0*600)+dx, int(y0*600))
                pygame.gfxdraw.line(screen, *center, *center0, (0, 0, 0, 255))

        if not can_lose(districts, state, n_districts, i):
            pygame.draw.circle(screen, (0,0,200), center, 5)

colors = np.random.randint(0, 255, (n_districts, 3))

draw_districts(districts, state, colors)

districts_final = np.array([ districts[mapping[i]] for i in range(len(mapping)) ])
draw_districts(districts_final, state_final, colors, dx=600)

while True:
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