import os, sys, random, time
import pygame
from pygame import gfxdraw
import numpy as np
sys.path.append(os.path.abspath('.'))
from src.state import State
from src import districts, mutation, metrics, metrics_test
from src.connectivity import can_lose
from src.constraints import fix_pop_equality
# import src.metrics
# import src.metrics_test
from src.draw import draw_districts

n_districts = 5
state = State.fromFile('data/NC_c2.json')
# print('a',state.n_tiles)
# state = State.makeRandom(400, seed=0)
# state, mapping = state.contract()
# print(state)
# print(state.tile_neighbors)


# met = metrics.compactness
# met = efficiency_gap
# met = metrics_test.compactness_ec
met = metrics.compactness

# def make_random(state, n_districts):
    # boundry_tiles = np.where(state.tile_boundaries)[0].tolist()
    # seeds = random.sample(boundry_tiles, n_districts)
    # districts = np.full(state.n_tiles, -1, dtype='i')
    # n_assigned = 0

    # open_neighbors = [ set() for _ in range(n_districts) ]
    # d_populations  = [ state.tile_populations[idx] for idx in seeds ]

    # for d_idx, t_idx in enumerate(seeds):
    #     districts[ t_idx ] = d_idx
    #     n_assigned += 1
    #     for t_idx0 in state.tile_neighbors[t_idx]:
    #         if districts[t_idx0] == -1:
    #             open_neighbors[d_idx].add(t_idx0)

    # frontiers = set()

    # while n_assigned < state.n_tiles:
    #     # Select the smallest district that has open neighbors.
    #     d_idx = next(d for d in np.argsort(d_populations) if len(open_neighbors[d]) > 0)
    #     # Give it a random neighbor.
    #     t_idx = random.choice(list(open_neighbors[d_idx]))
    #     # print('giving %i to %i'%(t_idx, d_idx))
    #     districts[ t_idx ] = d_idx
    #     d_populations[ d_idx ] += state.tile_populations[ t_idx ]
    #     n_assigned += 1

    #     for on in open_neighbors:
    #         if t_idx in on:
    #             on.remove(t_idx)

    #     for t_idx0 in state.tile_neighbors[t_idx]:
    #         if districts[t_idx0] == -1:
    #             open_neighbors[d_idx].add(t_idx0)

    # print(d_populations)
    # # assert districts.min() == 0
    # # assert all(len(on) == 0 for n in open_neighbors)
    # return districts

districts = districts.make_random(state, n_districts)

n_pop = state.tile_populations.sum()
ideal_pop = n_pop / n_districts
pop_max = ideal_pop * (1+ 1)
pop_min = ideal_pop * (1- 1)

# print(fix_pop_equality(state, districts, n_districts, tolerance=.10, max_iters=1000))

pygame.init()
w, h = (600, 600)
screen = pygame.display.set_mode((w, h))
screen.fill((255, 255, 255))

colors = np.random.randint(0, 255, (n_districts, 3))
mutate = True

draw_districts(screen, districts, state, colors)
pygame.display.update()



def draw_shapes(screen, state, polygons):
    w, h = screen.get_width(), screen.get_height()
    xmin, ymin, xmax, ymax = state.bbox
    def pmap(p):
        return (
            int((p[0]-xmin) * w/(xmax-xmin)),
            h - int((p[1]-ymin) * h/(ymax-ymin))
        )
    # print(polygons[0])
    for points in polygons:
        points = [ pmap(p) for p in points ]
        gfxdraw.aapolygon(screen, points, (50, 50, 50))

while True:
    if mutate:
        d2 = districts.copy()
        mutation.mutate(d2, n_districts, state, 0.01, pop_min, pop_max)

        new_fitness = met(state, d2, n_districts)

        if new_fitness < met(state, districts, n_districts):
            print(new_fitness)
            districts = d2
            draw_districts(screen, districts, state, colors)
            # draw_shapes(screen, state, shapes)
            pygame.display.update()
        else:
            print('.')

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()
            elif event.key == pygame.K_LEFT:
                p.mutate()
                draw_districts(districts, colors)
                pygame.display.update()
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
