import os, sys, random, time
import pygame
import numpy as np
sys.path.append(os.path.abspath('.'))
from src.draw import draw_districts, wait_loop
from src.state import State

state = State.fromFile(sys.argv[1])

pygame.init()
screen = pygame.display.set_mode(( 1200, 600 ))
screen.fill(( 255, 255, 255 ))

n_districts = 20
districts = np.random.randint(0, n_districts, (state.n_tiles))
colors = np.random.randint(0, 255, (n_districts, 3))

draw_districts(state, districts, n_districts, screen, colors, draw_vertices=True)
pygame.display.update()
wait_loop()