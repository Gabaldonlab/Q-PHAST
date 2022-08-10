#!/usr/bin/env python

# example script to be run in colonyzer_env

# import 
import pygame, time, sys

try:

    background_colour = (255,255,255)
    (width, height) = (300, 200)
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Tutorial 1')
    screen.fill(background_colour)
    pygame.display.flip()
    running = True
    start_time = time.time()

    while running:

        elapsed_time = time.time()-start_time
        if elapsed_time>0.01: running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    print("pygame's GUI works well")

except Exception as err:

    print("\n\n---\nERROR: pygame's GUI does not work well.\n---\n\n")
    print("---\nThis is the error thrown when trying to run pygame:")
    print(err)
    print("---\n")
    sys.exit(1)
