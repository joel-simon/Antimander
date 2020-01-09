import pygame
from pygame import gfxdraw

def draw_districts(screen, districts, state, colors, dx=0):
    w, h = screen.get_width(), screen.get_height()
    xmin, ymin, xmax, ymax = state.bbox
    def pmap(p):
        return (
            int((p[0]-xmin) * w/(xmax-xmin)),
            h - int((p[1]-ymin) * h/(ymax-ymin))
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