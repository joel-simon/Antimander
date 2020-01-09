import os, sys, random, time
sys.path.append(os.path.abspath('.'))
import pygame
from pygame import gfxdraw
import numpy as np
from src.state import State
from src import districts, mutation, metrics
from src.connectivity import can_lose
# from src.constraints import fix_pop_equality
import src.metrics

n_districts = 5
state = State.fromFile(sys.argv[1])
print('Loaded state data', state.n_tiles)
state, mapping = state.contract(seed=0)
state, mapping = state.contract(seed=0)
state, mapping = state.contract(seed=0)
print('Contracted', state.n_tiles)

districts = districts.make_random(state, n_districts)
print('Made random partition')

pygame.init()
w, h = (1200, 600)
screen = pygame.display.set_mode((w, h))
screen.fill((255, 255, 255))

def draw_districts(districts, state, colors, dx=0):
    xmin, ymin, xmax, ymax = state.bbox

    def pmap(p):
        return (
            int((p[0]-xmin) * w/(xmax-xmin)),
            int((p[1]-ymin) * h/(ymax-ymin))
        )

    for i in range(state.n_tiles):
        district = districts[i]
        vertices = [ pmap(p) for p in state.tile_vertices[i] ]
        gfxdraw.filled_polygon(screen, vertices, colors[district] )
        gfxdraw.aapolygon(screen, vertices, (50, 50, 50))

    for i in range(state.n_tiles):
        center = pmap(state.tile_centers[i])

        for j in state.tile_neighbors[i]:
            if i < j:
                center0 = pmap(state.tile_centers[j])
                pygame.gfxdraw.line(screen, *center, *center0, (0, 0, 0, 255))

        # if not can_lose(districts, state, n_districts, i):
        #     pygame.draw.circle(screen, (0,0,200), center, 5)

colors = np.random.randint(0, 255, (n_districts, 3))

draw_districts(districts, state, colors)

# districts_final = np.array([ districts[mapping[i]] for i in range(len(mapping)) ])
# draw_districts(districts_final, state_final, colors, dx=600)

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