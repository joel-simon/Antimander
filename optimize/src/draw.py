import pygame
# import colorsys
import numpy as np
from pygame import gfxdraw
from src.test import merge_polygons
from collections import defaultdict
from src.metrics import bounding_circles, bounding_hulls
BLACK = (0, 0, 0)

def flatten(a):
    return [ item for sublist in a for item in sublist ]

def normalize(a):
    """ Normalize an array to [0, 1] while ignoring nan values """
    nn = a[~np.isnan(a)]
    return (a - np.min(nn)) / np.ptp(nn)

def draw_districts(
    state,
    districts,
    n_districts,
    screen,
    colors,
    dx=0,
    dy=0,
    scale=1.0,
    draw_vertices=False,
    draw_can_lose=False,
    draw_neigbors_lines=False,
    draw_bounding_circles=False,
    draw_bounding_hulls=False,
    draw_district_edges=False,
    # draw_populations=False
):
    w, h = screen.get_width(), screen.get_height()
    xmin, ymin, xmax, ymax = state.bbox
    scale = min(w/(xmax-xmin), h/(ymax-ymin))
    pmap = lambda p:(int((p[0]-xmin)*scale)+dx, h-int((p[1]-ymin)*scale)+dy)

    # print( state.tile_voters.sum(axis=1).min() )

    total_voters = state.tile_voters.sum(axis=1)
    vote_percentages = normalize(state.tile_voters[:, 0] / total_voters)
    populations = normalize(state.tile_populations)

    # if draw_populations:
    #     import matplotlib.pyplot as plt
    #     cmap = plt.get_cmap('RdBu')
    #     def get_color(p):
    #         return [ round(255*x) for x in cmap(p) ]

    for ti in range(state.n_tiles):
        district = districts[ti]
        color = colors[district]

        # value = vote_percentages[ti]
        # if np.isnan(value):
        #     color = (0,0,0)
        # else:
        #     percent = state.tile_voters[ti, 0] / total_voters[ti]
        #     color = get_color(value)

        for poly in state.tile_vertices[ti]:
            vertices = [ pmap(p) for p in poly ]
            gfxdraw.filled_polygon(screen, vertices, color )
            pygame.draw.polygon(screen, (50, 50, 50), vertices, 1)

    if draw_vertices:
        vert_to_di = defaultdict(set)
        for ti in range(state.n_tiles):
            for p in set(flatten(state.tile_vertices[ti])):
                vert_to_di[ p ].add( ti )

        for ti in range(state.n_tiles):
            for p in set(flatten(state.tile_vertices[ti])):
                # for poly in state.tile_vertices[ti]:
                # for p in poly:
                if len(vert_to_di[p]) == 1:
                    pygame.draw.circle(screen, (0,0,200), pmap(p), 1)
                if len(vert_to_di[p]) > 1:
                    pygame.draw.circle(screen, (200,0,0), pmap(p), 1)

    if draw_neigbors_lines:
        for i in range(state.n_tiles):
            center = pmap(state.tile_centers[i])
            for j in state.tile_neighbors[i]:
                if i < j:
                    center0 = pmap(state.tile_centers[j])
                    pygame.gfxdraw.line(screen, *center, *center0, (0, 0, 0, 255))

    if draw_bounding_circles:
        for x, y, r in bounding_circles(state, districts, n_districts):
            pygame.draw.circle(screen, (200,0,0), pmap((x, y)), int(r*scale), 2)

    if draw_bounding_hulls:
        for vertices in bounding_hulls(state, districts, n_districts):
            vertices = [ pmap(p) for p in vertices ]
            pygame.draw.polygon(screen, (200, 0, 0), vertices, 2)

    if draw_district_edges:
        for ti0, tile_edge_data in enumerate(state.tile_edges):
            for ti1, edge_data in tile_edge_data.items():
                if ti1 == 'boundry' or districts[ti0] != districts[ti1]:
                    for edge in edge_data['edges']:
                        p1, p2 = edge
                        pygame.draw.line(screen, BLACK, pmap(p1), pmap(p2), 3)

    if draw_can_lose:
        if not can_lose(districts, state, n_districts, i):
            pygame.draw.circle(screen, (0,0,200), center, 5)

def wait_loop():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()