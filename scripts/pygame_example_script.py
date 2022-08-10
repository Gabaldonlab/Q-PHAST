#!/usr/bin/env python

# example script to be run in colonyzer_env

# import 
import pygame, time, sys, os


background_colour = (255,255,255)
(width, height) = (300, 200)
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Tutorial 1')
screen.fill(background_colour)
pygame.display.flip()
running = True
start_time = time.time()

print("launnching display")
while running:

    elapsed_time = time.time()-start_time
    if elapsed_time>0.1: running = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

print("pygame's GUI works well")

