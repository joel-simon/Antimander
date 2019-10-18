import sys
import pygame
from pygame import gfxdraw
from Map import Map, Partition
import polygon
import random
from articulationPoints import articulationPoints
import copy

m = Map.makeRandom(400, seed=0)
p = Partition.makeRandom(5, m, seed=None)

print(articulationPoints(p.districts[0]))

pygame.init()
screen = pygame.display.set_mode((600, 600))
screen.fill((255, 255, 255))


def draw_partition(partition):
    m = partition.map

    for district in partition.districts:
        for tile in district.tiles:
            vertices = [(x*600, y*600) for x,y in tile.vertices]
            gfxdraw.filled_polygon(screen, vertices, district.color)

    for tile in m.tiles:
        vertices = [(x*600, y*600) for x,y in tile.vertices]
        # gfxdraw.aapolygon(screen, vertices, (50, 50, 50))


    for district in partition.districts:
        for tile in district.tiles:
            vertices = [(int(x*600), int(y*600)) for x,y in tile.vertices]
            for edge in tile.edges:
                if edge.neighbour is not None and edge.neighbour not in district.tiles:
                    v1 = vertices[edge.vertices[0]]
                    v2 = vertices[edge.vertices[1]]
                    # pygame.draw.line(screen, (200, 0, 0), v1, v2, 3)


            # x1, y1 = tile.center
            # v1 = (int(x1*600), int(y1*600))
            # for edge in tile.edges:
            #     if edge.neighbour:
            #         if p.tile2district[tile] == p.tile2district[edge.neighbour]:
            #             x2, y2 = edge.neighbour.center
            #             v2 = (int(x2*600), int(y2*600))
            #             pygame.draw.line(screen, (200, 0, 0), v1, v2, 1)
        for tile in district.canLose():
            x,y = tile.center
            # pygame.draw.circle(screen, (0,0,200), (int(x*600), int(y*600)), 3)


# font = pygame.font.SysFont("comicsansms", 72)

# text = font.render("Hello, World", True, (0, 128, 0))

draw_partition(p)
while True:
    # p2 = copy.deepcopy(p)
    # p2.mutate()
    # if p2.evaluate()[0] > p1.evaluate()[0]:
    #     p = p2
    p.mutate()
    draw_partition(p)
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()
            elif event.key == pygame.K_LEFT:
                p.mutate()
                draw_partition(p)
                # pass
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
    pygame.display.update()