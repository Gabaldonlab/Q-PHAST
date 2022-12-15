# A python3 script to run the pipeline from any OS

############# ENV ############

# imports
import os, sys, argparse, subprocess, re, time

# general functions

# add the functions
if "/" in os.getcwd(): os_sep = "/"
elif "\\" in os.getcwd(): os_sep = "\\"
else: raise ValueError("unknown OS. This script is %s"%__file__)

pipeline_dir = os_sep.join(os.path.realpath(__file__).split(os_sep)[0:-1])
sys.path.insert(0, '%s%sscripts'%(pipeline_dir, os_sep))
import main_functions as fun

description = """
This is a pipeline to measure antifungal susceptibility from image data in any OS. Run with: 

    In linux and mac: 'python3 main.py <arguments>'

    In windows: 'py main.py <arguments>'

Check the github repository (https://github.comGabaldonlab/qCAST) to know how to use this script.
"""

# mandatory arguments (if run in command line)               
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--os", dest="os", required=False, default=None, type=str, help="The Operating System. It should be 'windows', 'linux' or 'mac'")
parser.add_argument("--module", dest="module", required=False, default=None, type=str, help="The module to run. It may be 'get_plate_layout' or 'analyze_images'")
parser.add_argument("--output", dest="output", required=False, default=None, type=str, help="The output directory.")
parser.add_argument("--docker_image", dest="docker_image", required=False, default=None, type=str, help="The name of the docker image in the format <name>:<tag>. All the versions of the images are in https://hub.docker.com/repository/docker/mikischikora/qcast. For example, you can set '--docker_image mikischikora/qcast:v1' to run version 1.")

# optional args for each module
parser.add_argument("--strains", dest="strains", required=False, default=None, type=str, help="An excel table with the list of strains. This only has an effect if --module is 'get_plate_layout'")
parser.add_argument("--drugs", dest="drugs", required=False, default=None, type=str, help="An excel table with the list of drugs and concentrations. This only has an effect if --module is 'get_plate_layout'")
parser.add_argument("--plate_layout", dest="plate_layout", required=False, default=None, type=str, help="An excel table with the plate layout in long format. This should be the file 'plate_layout_long'.xlsx genertaed by the 'get_plate_layout' module. This only has an effect if --module is 'analyze_images'")
parser.add_argument("--images", dest="images", required=False, default=None, type=str, help="A folder with the raw images to analyze. It should contain one subfolder (named after the plate batch) with the images of each 'plate_batch'. This only has an effect if --module is 'analyze_images'")
parser.add_argument("--keep_tmp_files", dest="keep_tmp_files", required=False, default=False, action="store_true", help="Keep the intermediate files in the 'analyze_images' module(for debugging).")
parser.add_argument("--replace", dest="replace", required=False, default=False, action="store_true", help="Remove the --output folder to repeat any previously run processes.")

parser.add_argument("--pseudocount_log2_concentration", dest="pseudocount_log2_concentration", required=False, type=float, default=0.1, help="A float that is used to pseudocount the concentrations for susceptibility measures. This only has an effect if --module is 'analyze_images'")
parser.add_argument("--min_nAUC_to_beConsideredGrowing", dest="min_nAUC_to_beConsideredGrowing", required=False, type=float, default=0.5, help="A float that indicates the minimum nAUC to be considered growing in susceptibility measures. This may depend on the experiment. This is added in the 'is_growing' field. This only has an effect if --module is 'analyze_images'")
parser.add_argument("--min_points_to_calculate_resistance_auc", dest="min_points_to_calculate_resistance_auc", required=False, type=int, default=4, help="An integer number indicating the minimum number of points required to calculate the rAUC for susceptibility measures. This only has an effect if --module is 'analyze_images'")

# parse
opt = parser.parse_args()

# pass the opt to functions
fun.opt = opt

##############################

##### RUN GUI TO DEFINE ARGUMENTS #########

# only get arguments through GUI if there are no arguments passed
if len(sys.argv)==1:

    # generate a series of buttons that select common arguments
    fun.generate_os_window()
    fun.generate_docker_image_window()
    fun.generate_module_window()

    # define the output
    fun.generate_output_window()
    opt.output = "%s%soutput_%s"%(opt.output, fun.get_os_sep(), opt.module)
    print("Writing results into the output folder '%s'"%opt.output)

    # define the replace window
    fun.generate_replace_window()

    # generate the window of each module
    if opt.module=="get_plate_layout": fun.generate_get_plate_layout_window()
    elif opt.module=="analyze_images": 
        fun.generate_analyze_images_window_mandatory()
        fun.generate_analyze_images_window_optional()

    else: raise ValueError("module should have 'get_plate_layout' or 'analyze_images'")

    # log
    print("Running pipeline...")

###########################################

# keep start time
start_time = time.time()

######  DEBUG INPUTS #########

# check that the mandatory args are not none
if opt.docker_image is None: raise ValueError("You should provide a string in --docker_image")
if opt.output is None: raise ValueError("You should provide a string in --output")

# replace
if opt.replace is True: fun.delete_folder(opt.output)

# arguments of each module
if opt.module=="get_plate_layout":
    if opt.strains is None or opt.drugs is None: raise ValueError("For module get_plate_layout, you should provide the --strains and --drugs arguments.")
    opt.strains = fun.get_fullpath(opt.strains)
    opt.drugs = fun.get_fullpath(opt.drugs)
    if fun.file_is_empty(opt.strains): raise ValueError("The file provided in --strains does not exist or it is empty")
    if fun.file_is_empty(opt.drugs): raise ValueError("The file provided in --drugs does not exist or it is empty")

elif opt.module=="analyze_images":
    if opt.plate_layout is None or opt.images is None: raise ValueError("For module analyze_images, you should provide the --plate_layout and --images arguments.")
    opt.plate_layout = fun.get_fullpath(opt.plate_layout)
    opt.images = fun.get_fullpath(opt.images)
    if fun.file_is_empty(opt.plate_layout): raise ValueError("The file provided in --plate_layout does not exist or it is empty")
    if not os.path.isdir(opt.images): raise ValueError("The folder provided in --images does not exist")

else: raise ValueError("--module should have 'get_plate_layout' or 'analyze_images'")

# check the OS
if not opt.os in {"linux", "mac", "windows"}: raise ValueError("--os should have 'linux', 'mac' or 'windows'")

# check that the docker image can be run
print("Trying to run docker image. If this fails it may be because either the image is not in your system or docker is not properly initialized.")
fun.run_cmd('docker run -it --rm %s bash -c "sleep 1"'%(opt.docker_image))

#############################

######### GENERATE THE DOCKER CMD AND RUN #################

# make the output
opt.output = fun.get_fullpath(opt.output)
fun.make_folder(opt.output)

# make the inputs_dir, where the small inputs will be stored
tmp_input_dir = "%s%stmp_small_inputs"%(opt.output, fun.get_os_sep())
fun.delete_folder(tmp_input_dir); fun.make_folder(tmp_input_dir)

# init command with general features
docker_cmd = 'docker run --rm -it -e KEEP_TMP_FILES=%s -e pseudocount_log2_concentration=%s -e min_nAUC_to_beConsideredGrowing=%s -e min_points_to_calculate_resistance_auc=%s -v "%s":/small_inputs -v "%s":/output'%(opt.keep_tmp_files, opt.pseudocount_log2_concentration, opt.min_nAUC_to_beConsideredGrowing, opt.min_points_to_calculate_resistance_auc, tmp_input_dir, opt.output)

# add the scripts from outside
docker_cmd += ' -v "%s%sscripts":/workdir_app/scripts'%(pipeline_dir, fun.get_os_sep())

# copy files and update the docker_cmd for each module
if opt.module=="get_plate_layout":
    fun.copy_file(opt.strains, "%s%sstrains.xlsx"%(tmp_input_dir, fun.get_os_sep()))
    fun.copy_file(opt.drugs, "%s%sdrugs.xlsx"%(tmp_input_dir, fun.get_os_sep()))

elif opt.module=="analyze_images":
    fun.copy_file(opt.plate_layout, "%s%splate_layout_long.xlsx"%(tmp_input_dir, fun.get_os_sep()))
    docker_cmd += ' -v "%s":/images'%opt.images


# get plate layout
if opt.module=="get_plate_layout": 
    print("Running module get_plate_layout")
    fun.run_docker_cmd("%s -e MODULE=get_plate_layout"%(docker_cmd), ["%s%splate_layout_long.xlsx"%(opt.output, fun.get_os_sep())])

# analyze images
elif opt.module=="analyze_images": 

    # get the corrected images
    print("\n\nSTEP 1: Getting cropped, flipped images with improved contrast...")
    fun.run_docker_cmd("%s -e MODULE=analyze_images_process_images"%(docker_cmd), ["%s/analyze_images_process_images_correct_finish.txt"%opt.output])

    # select the coordinates based on user input
    print("\n\nSTEP 2: Selecting the coordinates of the spots...")
    fun.get_colonyzer_coordinates_GUI(opt.output)


    # get fitness and susceptibility measurements
    print("\n\nSTEP 3: Getting fitness and susceptibility measurements...")
    fun.run_docker_cmd("%s -e MODULE=analyze_images_get_measurements"%(docker_cmd), ["%s/analyze_images_get_measurements_correct_finish.txt"%opt.output])

else: raise ValueError("invalid module")

# clean
fun.delete_folder(tmp_input_dir) # clean

# log
print("main.py %s worked successfully in %.2f seconds!"%(opt.module, time.time()-start_time))

###########################################################

