import pygame
from pygame import gfxdraw
from src.test import merge_polygons
from collections import defaultdict

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
    draw_neigbors_lines=False
):
    w, h = screen.get_width(), screen.get_height()
    xmin, ymin, xmax, ymax = state.bbox
    scale = min(w/(xmax-xmin), h/(ymax-ymin))
    def pmap(p):
        return (
            int((p[0]-xmin) * scale) + dx,
            h - int((p[1]-ymin) * scale) + dy
        )

    for ti in range(state.n_tiles):
        district = districts[ti]
        vertices = [ pmap(p) for p in state.tile_vertices[ti] ]
        gfxdraw.filled_polygon(screen, vertices, colors[district] )
        # gfxdraw.aapolygon(screen, vertices, (200, 200, 200))
        pygame.draw.polygon(screen, (50, 50, 50), vertices, 2)


    # for di in range(n_districts)[2:6]:
    #     vertices = merge_polygons([ state.tile_vertices[ti] for ti in range(state.n_tiles) if districts[ti] == di ])
    #     vertices = [ pmap(p) for p in vertices ]
    #     if len(vertices) > 2:
    #         pygame.draw.polygon(screen, (200, 0, 0), vertices, 3)
        # pygame.draw.polygon(screen, (50, 50, 50), vertices, 2)
        # di = districts[ti]
        # for tj in state.tile_neighbors[ti]:
        #     dj = districts[tj]
        #     if dj != di:
        #         for v1, v2 in state.tile_edges[ti][tj]['edges']:
        #             pygame.draw.line(screen, (255, 0, 0), pmap(v1), pmap(v2), 3)

    if draw_vertices:
        vert_to_di = defaultdict(set)
        for ti in range(state.n_tiles):
            for v in state.tile_vertices[ti]:
                vert_to_di[ v ].add( ti )
        for ti in range(state.n_tiles):
            for v in state.tile_vertices[ti]:
                if len(vert_to_di[v]) == 1:
                    pygame.draw.circle(screen, (0,0,200), pmap(v), 2)
                if len(vert_to_di[v]) > 1:
                    pygame.draw.circle(screen, (200,0,0), pmap(v), 2)


    if draw_neigbors_lines:
        for i in range(state.n_tiles):
            center = pmap(state.tile_centers[i])
            if len(state.tile_neighbors[i]) == 0:
                pygame.draw.circle(screen, (200,0,0), center, 3)
            # for j in state.tile_neighbors[i]:
            #     if i < j:
            #         center0 = pmap(state.tile_centers[j])
            #         pygame.gfxdraw.line(screen, *center, *center0, (0, 0, 0, 255))

    if draw_can_lose:
        if not can_lose(districts, state, n_districts, i):
            pygame.draw.circle(screen, (0,0,200), center, 5)

def wait_loop():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()