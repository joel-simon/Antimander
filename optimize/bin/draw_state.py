import os, sys, random, time
import pygame
import numpy as np
sys.path.append(os.path.abspath('.'))
from src.draw import draw_districts
from src.state import State

state = State.fromFile(sys.argv[1])
print(state.n_tiles)

n_districts = 20
districts = np.random.randint(0, n_districts, (state.n_tiles))
colors = np.random.randint(0, 255, (n_districts, 3))

pygame.init()
w, h = (1200, 600)
screen = pygame.display.set_mode((w, h))
screen.fill((255, 255, 255))

draw_districts(screen, districts, state, colors)
pygame.display.update()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()