#!/usr/bin/env python

# This script takes either a /strains_and_drugs or an /images mounted volume, which triggers two types of behaviors

########## DEFIINE ENV #########

# this is run from /workdir_app inside the docker image

# module imports
import os, sys

# define dirs
ScriptsDir = "/workdir_app/scripts"
CondaDir =  "/opt/conda"
OutDir = "/output"
StrainsAndDrugsDir = "/strains_and_drugs"
ImagesDir = "/images"

# import the functions
sys.path.insert(0, ScriptsDir)
import app_functions as fun

# log
fun.print_with_runtime("running %s"%fun.PipelineName)

################################

######### TEST ENV ########

# check that the pygame can be executed
fun.run_cmd("%s/pygame_example_script.py"%ScriptsDir, env="colonyzer_env")


###########################



# log
fun.print_with_runtime("%s finished successfully"%fun.PipelineName)
