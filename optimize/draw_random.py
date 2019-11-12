import sys, random, time
import pygame
from pygame import gfxdraw
import numpy as np
from map import Map
import partition as Partition

from constraints import pop_equality, fix_pop_equality
from metrics import compactness, efficiency_gap
# from utils.articulation_points import articulationPoints
# from mutation import can_lose, mutate
import mutation
n_districts = 5
m = Map.makeRandom(200, seed=0)
p = Partition.make_random(m, n_districts, seed=None)

# start = time.time()
# for i in range(m.n_tiles):
#     mutation.can_lose(p, m, n_districts, i)
# print((time.time() - start))
# exit()
fix_pop_equality(m, p, n_districts, tolerance=.10, max_iters=1000)

# P = [ Partition.make_random(m, n_districts, seed=None) for _ in range(100) ]
# start = time.time()
# total_steps = 0
# failed = 0
# for p in P:
#     try:
#         total_steps += fix_pop_equality(m, p, n_districts, tolerance=.10, max_iters=100)
#     except ValueError as e:
#         failed += 1
# print(failed)
# print((time.time() - start) / total_steps)
# # print(sum(pop_equality(m, p, n_districts) for p in P))
# exit()


pygame.init()
screen = pygame.display.set_mode((600, 600))
screen.fill((255, 255, 255))
font = pygame.font.SysFont("comicsansms", 14)

def draw_partition(partition, map, colors):
    # aps = articulationPoints(partition, map)

    for i in range(map.n_tiles):
        vertices = [ (x*600, y*600) for x,y in map.tile_vertices[i] ]
        district = partition[i]

        gfxdraw.filled_polygon(screen, vertices, colors[district] )
        gfxdraw.aapolygon(screen, vertices, (50, 50, 50))

        x,y = map.tile_centers[i]
        v = (int(x*600), int(y*600))

        if not mutation.can_lose(partition, map, n_districts, i):
            pygame.draw.circle(screen, (0,0,200), v, 5)

colors = np.random.randint(0, 255, (n_districts, 3))
mutate = True
draw_partition(p, m, colors)

while True:
    if mutate:
        mutation.mutate(p, n_districts, m, 0.01, None, None)
        draw_partition(p, m, colors)
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()
            elif event.key == pygame.K_LEFT:
                p.mutate()
                draw_partition(p, colors)
                # pass
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
    pygame.display.update()