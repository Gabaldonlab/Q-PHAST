# A python3 script to run the pipeline from any OS

############# ENV ############

# imports
import os, sys, argparse, shutil, subprocess
from pathlib import Path
import tkinter as tk
from tkinter.filedialog import askopenfilename, askdirectory
import subprocess
import webbrowser


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

##############################

##### DEFINE FUNCTIONS #######

# define general variables
window_width = 400 # width of all windows
pipeline_name = "qCAST"

def get_fullpath(x):

    """Takes a path and substitutes it bu the full path"""

    if opt.os in {"linux", "mac"}:
        if x.startswith("/"): return x

        # a ./    
        elif x.startswith("./"): return "%s/%s"%(os.getcwd(), "/".join(x.split("/")[1:]))

        # others (including ../)
        else: return "%s/%s"%(os.getcwd(), x)

    elif opt.os=="windows":
        if Path(x).is_absolute() is True: return x

        # a .\
        elif x.startswith(".\\"): return "%s\\%s"%(os.getcwd(), "\\".join(x.split("\\")[1:]))

        # others (including ..\)
        else: return "%s\\%s"%(os.getcwd(), x)

    else: raise ValueError("--os should have 'linux', 'mac' or 'windows'")

def run_cmd(cmd):

    """Runs os.system in cmd"""

    out_stat = os.system(cmd) 
    if out_stat!=0: raise ValueError("\n%s\n did not finish correctly. Out status: %i"%(cmd, out_stat))

def make_folder(f):

    if not os.path.isdir(f): os.mkdir(f)


def remove_file(f):

    if os.path.isfile(f): os.unlink(f)

def delete_folder(f):

    if os.path.isdir(f): shutil.rmtree(f)

def file_is_empty(path): 
    
    """ask if a file is empty or does not exist """

    if not os.path.isfile(path): return True
    elif os.stat(path).st_size==0: return True
    else: return False

def get_os_sep(): return {"windows":"\\", "linux":"/", "mac":"/"}[opt.os]

def copy_file(origin_file, dest_file):

    """Copies file"""

    dest_file_tmp = "%s.tmp"%dest_file
    shutil.copy(origin_file, dest_file_tmp)
    os.rename(dest_file_tmp, dest_file)

def generate_os_window():

    """Generates the OS selection window"""

    window = tk.Tk(); window.geometry("%ix150"%(window_width))
    window.title(pipeline_name)

    tk.Label(window, text="\nSelect the Operating System:", font=('Arial bold',15)).pack(side=tk.TOP)
    for os_name in ["linux", "mac", "windows"]: 

        def set_os(x = os_name):
            opt.os = x
            window.destroy()

        tk.Button(window, text=os_name, padx=20, pady=15, font=('Arial bold',13), command=set_os).pack(side=tk.LEFT, expand=True) 

    window.mainloop()
    if opt.os is None: raise ValueError("You should select the OS")


def generate_docker_image_window():

    """Generates the image selection window"""

    try: docker_images = ["%s:%s"%(l.split()[0], l.split()[1]) for l in str(subprocess.check_output("docker images", shell=True)).split("\\n") if not l.startswith("b'REPOSITORY") and len(l.split())>2 and 'mikischikora/qcast' in l]
    except: raise ValueError("The docker command 'docker images' did not work properly. Are you sure that docker is running?")

    image_w = 60
    window = tk.Tk(); window.geometry("%ix%i"%(window_width, image_w + len(docker_images)*image_w))
    window.title(pipeline_name)

    tk.Label(window, text="\nSelect the docker image:", font=('Arial bold',15)).pack(side=tk.TOP)
    for docker_img in docker_images: 

        def set_docker_image(x = docker_img):
            opt.docker_image = x
            window.destroy()

        tk.Button(window, text=docker_img, padx=30, pady=10, font=('Arial bold',13), command=set_docker_image).pack(side=tk.TOP, expand=True) 

    window.mainloop()
    if opt.docker_image is None: raise ValueError("You should select the docker_img")


def generate_module_window():

    """ generate a window that defines the module"""

    window = tk.Tk()
    window.geometry("%ix150"%(window_width))
    window.title(pipeline_name)

    tk.Label(window, text="\nSelect the module:", font=('Arial bold',15)).pack(side=tk.TOP)

    for module, module_name in [("get_plate_layout", "plate_layout"), ("analyze_images", "analyze_images")]: 

        def set_module(x = module):
            opt.module = x
            window.destroy()

        tk.Button(window, text="%s"%(module_name), padx=15, pady=15, font=('Arial bold',13), command=set_module).pack(side=tk.LEFT, expand=True)

    window.mainloop()
    if opt.module is None: raise ValueError("You should select the module")


def generate_output_window():

    """Generates the output folder"""


    window = tk.Tk()
    window.geometry("%ix150"%(window_width))
    window.title(pipeline_name)

    tk.Label(window, text='\nSelect the output folder:', font=('Arial bold',15)).pack(side=tk.TOP)

    def set_outfolder():
        opt.output = askdirectory()
        window.destroy()

    tk.Button(window, text="Browse folders", padx=15, pady=15, font=('Arial bold',13), command=set_outfolder).pack(side=tk.LEFT, expand=True)

    window.mainloop()
    if opt.output is None: raise ValueError("You should select the outfolder")
    if not os.path.isdir(opt.output): raise ValueError("You should select a valid outfolder")


def generate_replace_window():

    """Generates the replace window"""

    window = tk.Tk()
    window.geometry("%ix210"%(window_width))
    window.title(pipeline_name)

    tk.Label(window, text='\nRemove the output folder\nand re-do all analyses?\n', font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text="(set 'No' to re-start from a previous run)\n", font=('Arial bold',12)).pack(side=tk.TOP)

    for rep_value, replace_text in [(True, "Yes"), (False, "No")]: 

        def set_replace(x = rep_value):
            opt.replace = x
            window.destroy()

        tk.Button(window, text="%s"%(replace_text), padx=15, pady=15, font=('Arial bold',13), command=set_replace).pack(side=tk.LEFT, expand=True)

    window.mainloop()

def get_last_part_of_string(x, max_size=15):

    """Gets a string and return the last part of it"""

    if len(x)>max_size: return "...%s"%(x[-max_size:])
    else: return x

def generate_get_plate_layout_window():

    """Generates the window of get plate layout"""

    # init window
    window = tk.Tk()
    window.geometry("%ix500"%(window_width))
    window.title(pipeline_name)

    # text
    tk.Label(window, text='\nModule get_plate_layout', font=('Arial bold',15)).pack(side=tk.TOP)

    # info disclaymer
    help_label = tk.Label(window, text='[Click here] to see example files\n', font=('Arial bold', 13))
    help_label.pack(side=tk.TOP)
    help_label.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://github.com/Gabaldonlab/qCAST/tree/main/testing/testing_subset"))

    # add the strains
    tk.Label(window, text='1) select the strains excel:', font=('Arial bold',15)).pack(side=tk.TOP)
    def define_strains(): 
        opt.strains = askopenfilename(filetypes=[("All files", "*.*")])
        strains_button["text"] = get_last_part_of_string(opt.strains)

    strains_button = tk.Button(window, text="Browse files", padx=15, pady=15, font=('Arial bold',13), command=define_strains)
    strains_button.pack(side=tk.TOP, expand=True)

    # add the drugs
    tk.Label(window, text='2) select the drugs excel:', font=('Arial bold',15)).pack(side=tk.TOP)
    def define_drugs(): 
        opt.drugs = askopenfilename(filetypes=[("All files", "*.*")])
        drugs_button["text"] = get_last_part_of_string(opt.drugs)

    drugs_button = tk.Button(window, text="Browse files", padx=15, pady=15, font=('Arial bold',13), command=define_drugs)
    drugs_button.pack(side=tk.TOP, expand=True)

    # run
    tk.Label(window, text='3) click to Run:', font=('Arial bold',15)).pack(side=tk.TOP)
    def run_module(): window.destroy()
    tk.Button(window, text="Run module", padx=15, pady=15, font=('Arial bold',13), command=run_module).pack(side=tk.TOP, expand=True)

    window.mainloop()
    if opt.strains is None or opt.drugs is None: raise ValueError("You should provide an excel for both strains and drugs")
    if opt.drugs==opt.strains: raise ValueError("The drugs and strains excels can't be the same")

def generate_analyze_images_window_mandatory():

    """Generates one window for the image analysis"""

    # init window
    window = tk.Tk()
    window.geometry("%ix600"%(window_width))
    window.title(pipeline_name)

    # text
    tk.Label(window, text='\nModule analyze_images\n', font=('Arial bold',15)).pack(side=tk.TOP)

    # add the plate layout
    tk.Label(window, text="1) select plate layout excel:", font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text="(file 'plate_layout_long.xlsx'\nfrom 'get_plate_layout' module)", font=('Arial bold',13)).pack(side=tk.TOP)

    def define_plate_layout(): 
        opt.plate_layout = askopenfilename(filetypes=[("All files", "*.*")])
        plate_layout_button["text"] = get_last_part_of_string(opt.plate_layout)

    plate_layout_button = tk.Button(window, text="Browse files", padx=15, pady=15, font=('Arial bold',13), command=define_plate_layout)
    plate_layout_button.pack(side=tk.TOP, expand=True)

    # add the images
    tk.Label(window, text="\n2) select images folder:", font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text="(folder with raw images, with a\nsubfolder for each plate_batch)", font=('Arial bold',13)).pack(side=tk.TOP)

    def define_images(): 
        opt.images = askdirectory()
        images_button["text"] = get_last_part_of_string(opt.images)

    images_button = tk.Button(window, text="Browse folders", padx=15, pady=15, font=('Arial bold',13), command=define_images)
    images_button.pack(side=tk.TOP, expand=True)

    # run and capture the entries
    tk.Label(window, text='\n3) click to Run:', font=('Arial bold',15)).pack(side=tk.TOP, expand=True)
    def run_module(): 

        # run
        window.destroy()
    
    tk.Button(window, text="Run module", padx=15, pady=15, font=('Arial bold',13), command=run_module).pack(side=tk.TOP, expand=True)

    # run and debug
    window.mainloop()

    if opt.plate_layout is None or opt.images is None: raise ValueError("You should provide an excel with the plate layout and a folder with the images")
    if not os.path.isdir(opt.images): raise ValueError("You should select a valid images")



def generate_analyze_images_window_optional():

    """Generates one window for the image analysis"""


    # init window
    window = tk.Tk()
    window.geometry("%ix850"%(window_width))
    window.title(pipeline_name)

    # text
    tk.Label(window, text='\nModule analyze_images', font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text="(optional parameters)\n", font=('Arial bold',13)).pack(side=tk.TOP)

    # add the keep_tmp_files
    tk.Label(window, text='\n1) Keep temporary files?', font=('Arial bold',15)).pack(side=tk.TOP)

    def set_keep_tmp_files_True():
        opt.keep_tmp_files = True
        keep_tmp_files_True_button["font"] = ('Arial bold',18)
        keep_tmp_files_False_button["font"] = ('Arial bold',11)

    def set_keep_tmp_files_False():
        opt.keep_tmp_files = False
        keep_tmp_files_True_button["font"] = ('Arial bold',11)
        keep_tmp_files_False_button["font"] = ('Arial bold',18)

    keep_tmp_files_True_button = tk.Button(window, text="Yes", padx=15, pady=10, font=('Arial bold',11), command=set_keep_tmp_files_True)
    keep_tmp_files_False_button = tk.Button(window, text="No", padx=15, pady=10, font=('Arial bold',18), command=set_keep_tmp_files_False)

    keep_tmp_files_True_button.pack(side=tk.TOP, expand=True)
    keep_tmp_files_False_button.pack(side=tk.TOP, expand=True)

    # add the entry of the pseudocount_log2_concentration
    tk.Label(window, text='\n2) pseudocount concentration:', font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text='(float added to concentrations\nfor susceptibility measures)', font=('Arial bold',13)).pack(side=tk.TOP)
    pseudocount_log2_concentration_entry = tk.Entry(window, font=('Arial bold',13))
    pseudocount_log2_concentration_entry.insert(0, str(opt.pseudocount_log2_concentration))
    pseudocount_log2_concentration_entry.pack(side=tk.TOP, expand=True)

    # add the entry of the min_nAUC_to_beConsideredGrowing
    tk.Label(window, text='\n3) min nAUC growing:', font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text='(minimum nAUC (float)\nto be considered growing)', font=('Arial bold',13)).pack(side=tk.TOP)
    min_nAUC_to_beConsideredGrowing_entry = tk.Entry(window, font=('Arial bold',13))
    min_nAUC_to_beConsideredGrowing_entry.insert(0, str(opt.min_nAUC_to_beConsideredGrowing))
    min_nAUC_to_beConsideredGrowing_entry.pack(side=tk.TOP, expand=True)

    # add the entry of the min_points_to_calculate_resistance_auc
    tk.Label(window, text='\n4) min concentrations rAUC:', font=('Arial bold',15)).pack(side=tk.TOP)
    tk.Label(window, text='(minimum # concentrations \nnecessary to calculate rAUC)', font=('Arial bold',13)).pack(side=tk.TOP)
    min_points_to_calculate_resistance_auc_entry = tk.Entry(window, font=('Arial bold',13))
    min_points_to_calculate_resistance_auc_entry.insert(0, str(opt.min_points_to_calculate_resistance_auc))
    min_points_to_calculate_resistance_auc_entry.pack(side=tk.TOP, expand=True)

    # run and capture the entries
    tk.Label(window, text='\n5) click to Run:', font=('Arial bold',15)).pack(side=tk.TOP, expand=True)
    def run_module(): 

        # get the extra measurements
        opt.pseudocount_log2_concentration = float(pseudocount_log2_concentration_entry.get())
        opt.min_nAUC_to_beConsideredGrowing = float(min_nAUC_to_beConsideredGrowing_entry.get())
        opt.min_points_to_calculate_resistance_auc = int(min_points_to_calculate_resistance_auc_entry.get())

        # run
        window.destroy()
    
    tk.Button(window, text="Run module", padx=15, pady=15, font=('Arial bold',13), command=run_module).pack(side=tk.TOP, expand=True)

    # run and debug
    window.mainloop()
    
##############################

##### RUN GUI TO DEFINE ARGUMENTS #########

# only get arguments through GUI if there are no arguments passed
if len(sys.argv)==1:

    # generate a series of buttons that select common arguments
    generate_os_window()
    generate_docker_image_window()
    generate_module_window()

    # define the output
    generate_output_window()
    opt.output = "%s%soutput_%s"%(opt.output, get_os_sep(), opt.module)
    print("Writing results into the output folder '%s'"%opt.output)

    # define the replace window
    generate_replace_window()

    # generate the window of each module
    if opt.module=="get_plate_layout": generate_get_plate_layout_window()
    elif opt.module=="analyze_images": 
        generate_analyze_images_window_mandatory()
        generate_analyze_images_window_optional()

    else: raise ValueError("module should have 'get_plate_layout' or 'analyze_images'")

    # log
    print("Running pipeline...")

###########################################

######  DEBUG INPUTS #########


# check that the mandatory args are not none
if opt.docker_image is None: raise ValueError("You should provide a string in --docker_image")
if opt.output is None: raise ValueError("You should provide a string in --output")

# replace
if opt.replace is True: delete_folder(opt.output)

# arguments of each module
if opt.module=="get_plate_layout":
    if opt.strains is None or opt.drugs is None: raise ValueError("For module get_plate_layout, you should provide the --strains and --drugs arguments.")
    opt.strains = get_fullpath(opt.strains)
    opt.drugs = get_fullpath(opt.drugs)
    if file_is_empty(opt.strains): raise ValueError("The file provided in --strains does not exist or it is empty")
    if file_is_empty(opt.drugs): raise ValueError("The file provided in --drugs does not exist or it is empty")

elif opt.module=="analyze_images":
    if opt.plate_layout is None or opt.images is None: raise ValueError("For module analyze_images, you should provide the --plate_layout and --images arguments.")
    opt.plate_layout = get_fullpath(opt.plate_layout)
    opt.images = get_fullpath(opt.images)
    if file_is_empty(opt.plate_layout): raise ValueError("The file provided in --plate_layout does not exist or it is empty")
    if not os.path.isdir(opt.images): raise ValueError("The folder provided in --images does not exist")

else: raise ValueError("--module should have 'get_plate_layout' or 'analyze_images'")

# check the OS
if not opt.os in {"linux", "mac", "windows"}: raise ValueError("--os should have 'linux', 'mac' or 'windows'")

# check that the docker image can be run
print("Trying to run docker image. If this fails it may be because either the image is not in your system or docker is not properly initialized.")
run_cmd('docker run -it --rm %s bash -c "sleep 1"'%(opt.docker_image))

#############################

######### GENERATE THE DOCKER CMD AND RUN #################

# make the output
opt.output = get_fullpath(opt.output)
make_folder(opt.output)

# make the inputs_dir, where the small inputs will be stored
tmp_input_dir = "%s%stmp_small_inputs"%(opt.output, get_os_sep())
delete_folder(tmp_input_dir); make_folder(tmp_input_dir)

# init command with general features
docker_cmd = 'docker run --rm -it -e MODULE=%s -e KEEP_TMP_FILES=%s -e pseudocount_log2_concentration=%s -e min_nAUC_to_beConsideredGrowing=%s -e min_points_to_calculate_resistance_auc=%s -v "%s":/small_inputs -v "%s":/output'%(opt.module, opt.keep_tmp_files, opt.pseudocount_log2_concentration, opt.min_nAUC_to_beConsideredGrowing, opt.min_points_to_calculate_resistance_auc, tmp_input_dir, opt.output)

# add the scripts from outside (debug)
if opt.os in {"linux", "mac"}: CurDir = get_fullpath("/".join(__file__.split("/")[0:-1]))
elif opt.os=="windows": CurDir = get_fullpath("\\".join(__file__.split("\\")[0:-1]))
docker_cmd += ' -v "%s%sscripts":/workdir_app/scripts'%(CurDir, get_os_sep())

# configure for each os
if opt.os=="linux":

    docker_cmd = 'xhost +local:docker && %s'%docker_cmd
    docker_cmd += ' -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix'

elif opt.os=="mac":

    local_IP = str(subprocess.check_output("ifconfig en0 | grep 'inet '", shell=True)).split("inet")[1].split()[0]
    docker_cmd = 'xhost +%s && %s'%(local_IP, docker_cmd)
    docker_cmd += ' -e DISPLAY=%s:0'%local_IP

elif opt.os=="windows":

    docker_cmd += " -e DISPLAY=host.docker.internal:0.0"

# copy files and update the docker_cmd for each module
if opt.module=="get_plate_layout":
    copy_file(opt.strains, "%s%sstrains.xlsx"%(tmp_input_dir, get_os_sep()))
    copy_file(opt.drugs, "%s%sdrugs.xlsx"%(tmp_input_dir, get_os_sep()))

elif opt.module=="analyze_images":
    copy_file(opt.plate_layout, "%s%splate_layout_long.xlsx"%(tmp_input_dir, get_os_sep()))
    docker_cmd += ' -v "%s":/images'%opt.images

# at the end add the name of the image
docker_stderr = "%s%sdocker_stderr.txt"%(opt.output, get_os_sep())
docker_cmd += ' %s bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate main_env > /dev/null 2>&1 && /workdir_app/scripts/run_app.py 2>/output/docker_stderr.txt"'%(opt.docker_image)

# run
print("Running docker image with the following cmd:\n---\n%s\n---\n"%docker_cmd)

try: run_cmd(docker_cmd)
except: 
    print("\n\nERROR: The run of the pipeline failed. This is the error log (check it to fix the error):\n---\n%s\n---\nExiting with code 1!"%("".join(open(docker_stderr, "r").readlines())))
    sys.exit(1)

# clean
remove_file(docker_stderr)
delete_folder(tmp_input_dir) # clean

# log
print("main.py %s worked successfully!"%opt.module)

###########################################################

