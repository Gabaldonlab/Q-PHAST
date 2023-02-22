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

Check the github repository (https://github.comGabaldonlab/Q-PHAST) to know how to use this script.
"""

# mandatory arguments (if run in command line)               
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--os", dest="os", required=False, default=None, type=str, help="The Operating System. It should be 'windows', 'linux' or 'mac'")
parser.add_argument("--output", dest="output", required=False, default=None, type=str, help="The output directory.")
parser.add_argument("--docker_image", dest="docker_image", required=False, default=None, type=str, help="The name of the docker image in the format <name>:<tag>. All the versions of the images are in https://hub.docker.com/repository/docker/mikischikora/q-phast. For example, you can set '--docker_image mikischikora/q-phast:v1' to run version 1.")
parser.add_argument("--input", dest="input", required=False, default=None, type=str, help="A folder with the plate layout and the raw images to analyze. It should contain one subfolder (named after the plate batch) with the images of each 'plate_batch'.")
parser.add_argument("--keep_tmp_files", dest="keep_tmp_files", required=False, default=False, action="store_true", help="Keep the intermediate files (forqca debugging).")
parser.add_argument("--replace", dest="replace", required=False, default=False, action="store_true", help="Remove the --output folder to repeat any previously run processes.")
parser.add_argument("--pseudocount_log2_concentration", dest="pseudocount_log2_concentration", required=False, type=float, default=0.1, help="A float that is used to pseudocount the concentrations for susceptibility measures.")
parser.add_argument("--min_nAUC_to_beConsideredGrowing", dest="min_nAUC_to_beConsideredGrowing", required=False, type=float, default=0.5, help="A float that indicates the minimum nAUC to be considered growing in susceptibility measures. This may depend on the experiment. This is added in the 'is_growing' field.")
parser.add_argument("--min_points_to_calculate_resistance_auc", dest="min_points_to_calculate_resistance_auc", required=False, type=int, default=4, help="An integer number indicating the minimum number of points required to calculate the rAUC for susceptibility measures.")

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

    # generate the window of each type of args
    fun.generate_analyze_images_window_mandatory()

    # define the replace window
    fun.generate_replace_window()

    # define the output and input
    opt.output = "%s%soutput_%s"%(opt.output, fun.get_os_sep(), fun.pipeline_name)
    print("Writing results into the output folder '%s', using input files from '%s'"%(opt.output, opt.input))

    # generate the 
    fun.generate_analyze_images_window_optional()


    # log
    print("Running pipeline...")

###########################################


# keep start time
start_time = time.time()

######  DEBUG INPUTS #########

# check that the mandatory args are not none
if opt.docker_image is None: raise ValueError("You should provide a string in --docker_image")
if opt.input is None: raise ValueError("You should provide a string in --input")
if opt.output is None: raise ValueError("You should provide a string in --output")

opt.input = fun.get_fullpath(opt.input)
opt.output = fun.get_fullpath(opt.output)
if not os.path.isdir(opt.input): raise ValueError("The folder provided in --input does not exist")

# replace
if opt.replace is True: fun.delete_folder(opt.output)

# check the OS
if not opt.os in {"linux", "mac", "windows"}: raise ValueError("--os should have 'linux', 'mac' or 'windows'")

# print the cmd
arguments = " ".join(["--%s %s"%(arg_name, arg_val) for arg_name, arg_val in [("os", opt.os), ("input", opt.input), ("output", opt.output), ("docker_image", opt.docker_image), ("pseudocount_log2_concentration", opt.pseudocount_log2_concentration), ("min_nAUC_to_beConsideredGrowing", opt.min_nAUC_to_beConsideredGrowing), ("min_points_to_calculate_resistance_auc", opt.min_points_to_calculate_resistance_auc)]])

if opt.keep_tmp_files is True: arguments += " --keep_tmp_files"
if opt.replace is True: arguments += " --replace"

full_command = "%s %s%smain.py %s"%(sys.executable, pipeline_dir, os_sep, arguments)
print("Executing the following command:\n---\n%s\n---\nNote that you can run this command to perform the exact same analysis."%full_command)

# check that the docker image can be run
print("Trying to run docker image. If this fails it may be because either the image is not in your system or docker is not properly initialized.")
fun.run_cmd('docker run -it --rm %s bash -c "sleep 1"'%(opt.docker_image))

#############################

######### GENERATE THE DOCKER CMD AND RUN #################

# define the plate layout file
plate_layout_file = "%s%s%s"%(opt.input, fun.get_os_sep(), fun.get_plate_layout_file_from_input_dir(opt.input))

# make the output
opt.output = fun.get_fullpath(opt.output)
fun.make_folder(opt.output)

# make the inputs_dir, where the small inputs will be stored
tmp_input_dir = "%s%stmp_small_inputs"%(opt.output, fun.get_os_sep())
fun.delete_folder(tmp_input_dir); fun.make_folder(tmp_input_dir)

# init command with general features
docker_cmd = 'docker run --rm -it -e KEEP_TMP_FILES=%s -e pseudocount_log2_concentration=%s -e min_nAUC_to_beConsideredGrowing=%s -e min_points_to_calculate_resistance_auc=%s -v "%s":/small_inputs -v "%s":/output -v "%s":/images'%(opt.keep_tmp_files, opt.pseudocount_log2_concentration, opt.min_nAUC_to_beConsideredGrowing, opt.min_points_to_calculate_resistance_auc, tmp_input_dir, opt.output, opt.input)

# add the scripts from outside
docker_cmd += ' -v "%s%sscripts":/workdir_app/scripts'%(pipeline_dir, fun.get_os_sep())

# pass the plate layout to docker
fun.copy_file(plate_layout_file, "%s%splate_layout.xlsx"%(tmp_input_dir, fun.get_os_sep()))

# get the corrected images
print("\n\nSTEP 1/3: Getting cropped, flipped images with improved contrast...")
fun.run_docker_cmd("%s -e MODULE=analyze_images_process_images"%(docker_cmd), ["%s/analyze_images_process_images_correct_finish.txt"%opt.output])

# select the coordinates based on user input
print("\n\nSTEP 2/3: Selecting the coordinates of the spots...")
fun.get_colonyzer_coordinates_GUI(opt.output, docker_cmd)

# get fitness and susceptibility measurements
print("\n\nSTEP 3/3: Getting fitness and susceptibility measurements...")
fun.run_docker_cmd("%s -e MODULE=analyze_images_get_measurements"%(docker_cmd), ["%s/analyze_images_get_measurements_correct_finish.txt"%opt.output])

# clean
for f in ['analyze_images_run_colonyzer_subset_images_correct_finish.txt', 'analyze_images_process_images_correct_finish.txt', 'analyze_images_get_measurements_correct_finish.txt']: fun.remove_file("%s%s%s"%(opt.output, fun.get_os_sep(), f))
fun.delete_folder(tmp_input_dir)


# log
print("main.py worked successfully in %.2f seconds!"%(time.time()-start_time))

###########################################################

