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
#fun.print_with_runtime("running %s %s"%(fun.PipelineName, os.environ["MODULE"]))

# get the start time
start_time = time.time()

################################

######### TEST ENV ########

# the output directory should exist
if not os.path.isdir(OutDir): raise ValueError("You should specify the output directory by setting a volume. If you are running on linux terminal you can set '-v <output directory>:/output'")

###########################

#### MAIN #####

# define a bool dict
bool_dict = {'True':True, 'False':False}

# process images
if os.environ["MODULE"]=="analyze_images_process_images": fun.run_analyze_images_process_images("%s/plate_layout.xlsx"%SmallInputs, ImagesDir, OutDir, bool_dict[str(os.environ["skip_contrast_correction"])])

# perform growth measurements for one image
elif os.environ["MODULE"]=="analyze_images_run_colonyzer_subset_images": fun.run_analyze_images_run_colonyzer_subset_images(OutDir)

# perform fitness measurements
elif os.environ["MODULE"]=="get_fitness_measurements": fun.run_analyze_images_get_fitness_measurements("%s/plate_layout.xlsx"%SmallInputs, ImagesDir, OutDir, float(os.environ["pseudocount_log2_concentration"]), float(os.environ["min_nAUC_to_beConsideredGrowing"]))

elif os.environ["MODULE"]=="get_rel_fitness_and_susceptibility_measurements": 

    fun.run_analyze_images_get_rel_fitness_and_susceptibility_measurements("%s/plate_layout.xlsx"%SmallInputs, ImagesDir, OutDir, bool_dict[str(os.environ["KEEP_TMP_FILES"])], float(os.environ["pseudocount_log2_concentration"]), float(os.environ["min_nAUC_to_beConsideredGrowing"]), int(os.environ["min_points_to_calculate_resistance_auc"]))

    # set permissions to be accessible in all cases
    fun.run_cmd("chmod -R 777 %s"%OutDir)

else: raise ValueError("The module is incorrect")

###############

# log
log_text = "%s: pipeline '%s' finished successfully in %.4f seconds"%(fun.PipelineName, os.environ["MODULE"], time.time()-start_time)
#fun.print_with_runtime(log_text)

# write final file
final_file = "%s/%s_correct_finish.txt"%(OutDir, os.environ["MODULE"])
open(final_file, "w").write(log_text+"\n")

