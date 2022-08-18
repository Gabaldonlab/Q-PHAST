#!/usr/bin/env python

# This script runs the module as defined by $MODULE

########## DEFIINE ENV #########

# this is run from /workdir_app inside the docker image

# module imports
import os, sys, time

# define dirs
ScriptsDir = "/workdir_app/scripts"
CondaDir =  "/opt/conda"
OutDir = "/output"
SmallInputs = "/small_inputs"
ImagesDir = "/images"

# import the functions
sys.path.insert(0, ScriptsDir)
import app_functions as fun

# log
fun.print_with_runtime("running %s %s"%(fun.PipelineName, os.environ["MODULE"]))

# get the start time
start_time = time.time()

################################

######### TEST ENV ########

# check that the pygame can be executed
#fun.run_cmd("%s/pygame_example_script.py"%ScriptsDir, env="colonyzer_env")

# the output directory should exist
if not os.path.isdir(OutDir): raise ValueError("You should specify the output directory by setting a volume. If you are running on linux terminal you can set '-v <output directory>:/output'")

###########################

#### MAIN #####

# depending on the input run one or the other pipeline
if os.environ["MODULE"]=="get_plate_layout": fun.run_get_plate_layout("%s/strains.xlsx"%SmallInputs, "%s/drugs.xlsx"%SmallInputs, OutDir)

elif os.environ["MODULE"]=="analyze_images": fun.run_analyze_images("%s/plate_layout_long.xlsx"%SmallInputs, ImagesDir, OutDir, {'True':True, 'False':False}[str(os.environ["KEEP_TMP_FILES"])])

else: raise ValueError("The module is  incorrect")

###############


# log
fun.print_with_runtime("%s: pipeline '%s' finished successfully in %.4f seconds"%(fun.PipelineName, os.environ["MODULE"], time.time()-start_time))
