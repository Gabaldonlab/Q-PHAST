#!/usr/bin/env python

# Display an image for some seconds. It should be run in colonyzer_env. Inspired by https://pythonprogramming.net/displaying-images-pygame/

# define the env
import pygame, sys, time

# parse args
image_file = sys.argv[1]
w = int(sys.argv[2])
h = int(sys.argv[3])
caption = sys.argv[4]

import pygame
from pygame.locals import*
img = pygame.image.load(image_file)

white = (255, 64, 64)

screen = pygame.display.set_mode((w, h))
pygame.display.set_caption(caption)

screen.fill((white))
running = True

start_time = time.time()
while running:
    screen.fill((white))
    screen.blit(img,(0,0))
    pygame.display.flip()
    if (time.time()-start_time)>5: running = False

pygame.quit()
quit()
