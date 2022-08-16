# A python3 script to run the pipeline from any OS

############# ENV ############

# imports
import os, sys, argparse, shutil

description = """
This is a pipeline to measure antifungal susceptibility from image data in any OS. Run with: 

    In linux and mac: 'python3 main.py <arguments>'

    In windows: 'py main.py <arguments>'

Check the github repository (https://github.com/Gabaldonlab/qCAST) to know how to use this script.
"""

# mandatory arguments              
parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--os", dest="os", required=True, type=str, help="The Operating System. It should be 'windows', 'linux' or 'mac'")
parser.add_argument("--module", dest="module", required=True, type=str, help="The module to run. It may be 'get_plate_layout' or 'analyze_images'")
parser.add_argument("--output", dest="output", required=True, type=str, help="The output directory.")
parser.add_argument("--docker_image", dest="docker_image", required=True, type=str, help="The name of the docker image in the format <name>:<tag>. All the versions of the images are in https://hub.docker.com/repository/docker/mikischikora/qcast. For example, you can set '--docker_image mikischikora/qcast:v1' to run version 1.")

# optional args for each module
parser.add_argument("--strains", dest="strains", required=False, default=None, type=str, help="An excel table with the list of strains. This only has an effect if --module is 'get_plate_layout'")
parser.add_argument("--drugs", dest="drugs", required=False, default=None, type=str, help="An excel table with the list of drugs and concentrations. This only has an effect if --module is 'get_plate_layout'")

# parse
opt = parser.parse_args()

##############################

##### DEFINE FUNCTIONS #######

def get_fullpath(x):

    """Takes a path and substitutes it bu the full path"""

    if opt.os in {"linux", "mac"}:
        if x.startswith("/"): return x

        # a ./    
        elif x.startswith("./"): return "%s/%s"%(os.getcwd(), "/".join(x.split("/")[1:]))

        # others (including ../)
        else: return "%s/%s"%(os.getcwd(), x)

    elif opt.os=="windows":

        define_windows_full_path

    else: raise ValueError("--os should have 'linux', 'mac' or 'windows'")

        
def run_cmd(cmd):

    """Runs os.system in cmd"""

    out_stat = os.system(cmd) 
    if out_stat!=0: raise ValueError("\n%s\n did not finish correctly. Out status: %i"%(cmd, out_stat))

def make_folder(f):

    if not os.path.isdir(f): os.mkdir(f)


def delete_folder(f):

    if os.path.isdir(f): shutil.rmtree(f)

def file_is_empty(path): 
    
    """ask if a file is empty or does not exist """

    if not os.path.isfile(path): return True
    elif os.stat(path).st_size==0: return True
    else: return False


##############################

######  DEBUG INPUTS #########

# arguments of each module
if opt.module=="get_plate_layout":
    if opt.strains is None or opt.drugs is None: raise ValueError("For module get_plate_layout, you should provide the --strains and --drugs argument.")
    opt.strains = get_fullpath(opt.strains)
    opt.drugs = get_fullpath(opt.drugs)
    if file_is_empty(opt.strains): raise ValueError("The file provided in --strains does not exist or it is empty")
    if file_is_empty(opt.drugs): raise ValueError("The file provided in --drugs does not exist or it is empty")

elif opt.module=="analyze_images":
    check_other_args
    make_full_paths
    pass

else: raise ValueError("--module should have 'get_plate_layout' or 'analyze_images'")

# check the OS
if not opt.os in {"linux", "mac", "windows"}: raise ValueError("--os should have 'linux', 'mac' or 'windows'")

# check that the docker image can be run
print("Trying to run docker image. If this fails it may be because either the image is not in your system or docker is not properly initialized.")
run_cmd("docker run -it --rm %s bash -c 'sleep 1'"%(opt.docker_image))
print("The docker image can be run.")

#############################

######### GENERATE THE DOCKER CMD AND RUN #################

# make the output
opt.output = get_fullpath(opt.output)
make_folder(opt.output)

# make the inputs_dir, where the small inputs will be stored
tmp_input_dir = "%s/tmp_small_inputs"%opt.output
delete_folder(tmp_input_dir); make_folder(tmp_input_dir)


# init command with general features
docker_cmd = 'docker run --rm -e MODULE=%s -v "%s":/small_inputs'%(tmp_input_dir, opt.module)

# move files and update the docker_cmd for each module
if opt.module=="get_plate_layout":

    pass

elif opt.module=="analyze_images":

    pass



# at the end add the name of the image
docker_cmd += " %s"%opt.docker_image

# run
print("running docker...")
run_cmd(docker_cmd)
delete_folder(tmp_input_dir) # clean
print("main.py %s worked successfully!"%opt.module)

###########################################################


print(opt.output )

