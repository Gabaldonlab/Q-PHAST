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
sys.exit(0)

# the output directory should exist
if not os.path.isdir(OutDir): raise ValueError("You should specify the output directory by setting a volume. If you are running on linux terminal you can set '-v <output directory>:/output'")

###########################


#### MAIN #####

# depending on the input run one or the other pipeline
if os.path.isdir(StrainsAndDrugsDir) and not os.path.isdir(ImagesDir):

	# define the name of the pipeline
	pipeline_step_name = "plate positions"

	# run pipeline

elif os.path.isdir(ImagesDir) and not os.path.isdir(StrainsAndDrugsDir):

	# define the name of the pipeline
	pipeline_step_name = "image analysis"

	# run pipeline

else: raise ValueError("You should pass either a directory with strains and drugs (in a linux terminal '-v <directory with strains and drugs>:/strains_and_drugs') or a directory with images (in a linux terminal '-v <directory with images>:/images'), but not both. ")

###############


# log
fun.print_with_runtime("%s: pipeline '%s' finished successfully"%(fun.PipelineName, pipeline_step_name))
